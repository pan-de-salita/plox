from __future__ import annotations

import builtins
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from . import expr, stmt
from .break_ import Break
from .environment import Environment
from .return_ import Return
from .runtime_exception import RuntimeException
from .token import Token
from .token_type import TokenType


class LoxCallable(ABC):
    @abstractmethod
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        pass

    @abstractmethod
    def arity(self) -> int:
        pass


@dataclass
class LoxFunction(LoxCallable):
    def __init__(
        self,
        declaration: stmt.Function,
        closure: Environment,
        is_initializer: bool = False,
        is_static: bool = False,
        is_getter: bool = False,
    ):
        self._declaration = declaration
        self._closure = closure
        self.is_initializer = is_initializer
        self.is_static = is_static
        self.is_getter = is_getter

    # NOTE: Function parameters and local variables should be isolated from
    # the outer scope, not dumped directly into it. This implementation
    # correctly creates a new environment that acts as a barrier between
    # the function's internals and the rest of the program.
    #
    # If we used interpreter.environment instead of creating a new
    # environment (Environment(enclosing=interpreter.environment)),
    # this code would work (which is not what should happen):
    #
    # fun testX(x) {
    #   print x;
    # }
    #
    # fun testY() {
    #   print x;
    # }
    #
    # testX("for x only.");
    # testY();
    #
    # Parameters are core to functions, especially the fact that a function
    # encapsulates its parameters -- no other code outside of the function
    # can see them. This means each function gets its own environment where
    # it stores those variables.
    #
    # Further, this environment must be created dynamically. Each function
    # call gets its own environment. Otherwise, recursion would break. If
    # there are multiple calls to the same function in play at the same time,
    # each needs its own environment, even though they are all calls to the
    # same function.
    #
    # At the beginning of each function call (not at the function declaration),
    # this call() method creates a new environment. Then it walks the
    # parameter and argument lists in lockstep. For each pair, it creates a
    # *new* variable with the paremeter's name and binds it to the argument's value.

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        environment: Environment = Environment(enclosing=self._closure)

        for idx, param in enumerate(self._declaration.params):
            environment.define(
                name=param.lexeme,
                value=arguments[idx],
                is_initialized=True,
            )

        try:
            interpreter.execute_block(self._declaration.body, environment)
        except Return as return_:
            if self.is_initializer:
                # After a method is bound to a class instance, `this`
                # (the only variable) would exist in index 0 of the immediate closure.
                return self._closure.get_at(0, "this")

            return return_.value

        if self.is_initializer:
            return self._closure.get_at(0, "this")

        return None

    def arity(self) -> int:
        return len(self._declaration.params)

    def bind(self, instance: LoxInstance) -> LoxFunction:
        environment: Environment = Environment(enclosing=self._closure)
        environment.define("this", instance, True)
        return LoxFunction(
            self._declaration,
            environment,
            self.is_initializer,
            self.is_static,
            self.is_getter,
        )

    def __str__(self) -> str:
        return f"<fn {self._declaration.name.lexeme}>"


@dataclass
class LoxLambdaExpression(LoxCallable):
    _declaration: expr.Lambda
    _closure: Environment

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        environment: Environment = Environment(enclosing=self._closure)

        for idx, param in enumerate(self._declaration.params):
            environment.define(
                name=param.lexeme,
                value=arguments[idx],
                is_initialized=True,
            )

        try:
            interpreter.execute_block(self._declaration.body, environment)
        except Return as return_:
            return return_.value

        return None

    def arity(self) -> int:
        return len(self._declaration.params)

    def __str__(self) -> str:
        return "<fn lambda>"


@dataclass
class AnonymousLoxCallable(LoxCallable):
    _callable: Callable[[Interpreter, list[object]], object]
    _arity: int

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        return self._callable(interpreter, arguments)

    def arity(self) -> int:
        return self._arity

    def __str__(self) -> str:
        return "<native fn>"


class LoxInstance:
    def __init__(self, klass: LoxClass) -> None:
        self.klass: LoxClass = klass
        self.fields: dict[str, object] = {**self.load_default_fields()}

    def get(self, name: Token) -> object:
        if name.lexeme in self.fields:
            return self.fields.get(name.lexeme)

        method: LoxFunction | None = self.klass.find_method(name.lexeme)
        if method:
            return method.bind(self)

        raise RuntimeException(name, f"Undefined property {name.lexeme}.")

    def set(self, key: Token, value: object) -> None:
        if key.lexeme in self.load_default_fields():
            raise RuntimeException(key, f"{key.lexeme} is a reserved field.")

        self.fields[key.lexeme] = value

    def load_default_fields(self) -> dict[str, object]:
        return {
            "klass": self.klass,
            "methods": self.get_methods(),
        }

    def get_methods(self) -> list[LoxFunction]:
        return list(self.klass.methods)

    def __str__(self) -> str:
        return f"<{self.klass.name} instance>"


class LoxClass(LoxInstance, LoxCallable):
    def __init__(
        self,
        name: str,
        methods: dict[str, LoxFunction],
        metaclass: LoxClass | None = None,
    ) -> None:
        self.methods: dict[str, LoxFunction]
        self.name: str = name

        if metaclass is None:
            instance_methods: dict[str, LoxFunction] = {
                name: decl for name, decl in methods.items() if not decl.is_static
            }
            static_methods: dict[str, LoxFunction] = {
                name: decl for name, decl in methods.items() if decl.is_static
            }

            self.methods = instance_methods
            super().__init__(LoxClass(f"Meta{name}", static_methods, self))
        else:
            self.methods = methods
            super().__init__(self)

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        instance: LoxInstance = LoxInstance(self)

        initializer: LoxFunction = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)

        return instance

    def arity(self) -> int:
        initializer: LoxFunction = self.find_method("init")
        if initializer is not None:
            return self.methods.get("init").arity()

        return 0

    def find_method(self, name: str) -> LoxFunction | None:
        return self.methods.get(name)

    def __str__(self) -> str:
        return f"<class> {self.name}"


class Interpreter(expr.Visitor[object], stmt.Visitor[None]):
    def __init__(self, error_callback: Callable[[RuntimeException], None]) -> None:
        self.globals: Environment = (
            Environment()
        )  # Fixed reference to the outermost global environment
        self._environment: Environment = self.globals

        self._locals: dict[expr.Expr, int] = {}
        self._error_callback: Callable[[RuntimeException], None] = error_callback
        self._is_run_prompt: bool = False

        self.globals.define(
            name="clock",
            value=AnonymousLoxCallable(
                _callable=lambda interpreter, arguments: time.time(), _arity=0
            ),
            is_initialized=True,
        )

    def interpret(self, statements: list[stmt.Stmt]) -> None:
        # print([v.name if "name" in dir(v) else v.keyword for v in self._locals])
        # print(self._locals)
        # print(statements)

        try:
            for statement in statements:
                self.__execute(statement)
        except RuntimeException as error:
            self._error_callback(error)

    def resolve(
        self, variable: expr.Variable | expr.Assign | expr.This, depth: int
    ) -> None:
        self._locals[variable] = depth

    def __execute(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    def visit_var_stmt(self, var_: stmt.Var) -> None:
        value: None | object = None
        if var_.initializer:
            value = self.__evaluate(var_.initializer)

        self._environment.define(
            name=var_.name.lexeme,
            value=value,
            is_initialized=var_.is_initialized,
        )

    def visit_while_stmt(self, while_: stmt.While) -> None:
        try:
            while self.__is_truthy(self.__evaluate(while_.condition)):
                self.__execute(while_.body)
        except Break:
            return

    def visit_break_stmt(self, break_: stmt.Break) -> None:
        raise Break()

    def visit_function_stmt(self, function: stmt.Function) -> None:
        self._environment.define(
            name=function.name.lexeme,
            value=LoxFunction(
                declaration=function,
                # NOTE: This is the environment that is active when the function
                # is declared, not when it's called. It represents the lexical
                # scope surrounding the function declaration. When we call the
                # function, we use this environment as the call's parent instead
                # of going straight to globals.
                #
                # This creates an environment chain that goes from the function's
                # body out through the environments where the function is declared,
                # all the way out to the global scope. The runtime environment
                # chain matches the textual nesting of the source code like we want.
                closure=self._environment,
                is_initializer=False,
            ),
            is_initialized=True,
        )

    def visit_class_stmt(self, class_: stmt.Class) -> None:
        # Declare the class in the current environment.
        self._environment.define(class_.name.lexeme, None, False)

        methods: dict[str, LoxFunction] = {
            method.name.lexeme: LoxFunction(
                declaration=method,
                closure=self._environment,
                is_initializer=method.name.lexeme == "init",
                is_statis=method.is_static,
                is_getter=method.is_getter,
            )
            for method in class_.methods
        }

        # Store the class object in the previously declared variable.
        # This two-stage variable binding process allows references to the
        # class inside its own methods.
        klass: LoxClass = LoxClass(class_.name.lexeme, methods)
        self._environment.assign(class_.name, klass)

    def visit_if_stmt(self, if_: stmt.If) -> None:
        if self.__is_truthy(self.__evaluate(if_.condition)):
            self.__execute(if_.then_branch)
        elif if_.else_branch is not None:
            self.__execute(if_.else_branch)

    def visit_block_stmt(self, block: stmt.Block) -> None:
        self.execute_block(
            block_statements=block.statements,
            environment=Environment(enclosing=self._environment),
        )

    def execute_block(
        self, block_statements: list[stmt.Stmt], environment: Environment
    ) -> None:
        previous_environment: Environment = self._environment
        try:
            # Switch self's environment to be a new one with previous_environment
            # as its enclosure. This allows for executed statements within the
            # block to have access to the state in the enclosing environment(s).
            #
            # E.g.:
            # var a = 1;
            # {
            #     var b = a;
            #     {
            #         var c = a + b;
            #         print c; // => 2
            #     }
            # }
            #
            # - Global environment. No inherited environment.
            # - First block environment. Inherits from, and therefore accesses,
            #   global environment (previous_environment).
            # - Second block environment:
            #   - Directly inherits from: first block environment (previous_environment)
            #   - Indirectly accesses: global environment (via chain through first block)
            self._environment = environment
            for block_statement in block_statements:
                self.__execute(block_statement)
        finally:
            # Restore old environment at the end of the block.
            self._environment = previous_environment

    def visit_print_stmt(self, print_: stmt.Print) -> None:
        builtins.print(self.__stringify(self.__evaluate(print_.expression)))

    def visit_return_stmt(self, return_: stmt.Return) -> None:
        value: object = None
        if return_.value:
            value = self.__evaluate(return_.value)

        raise Return(value)

    def visit_expression_stmt(self, expression: stmt.Expression) -> None:
        value: object = self.__evaluate(expression.expression)

        if self._is_run_prompt:
            print(self.__stringify(value))

    def __evaluate(self, expression: expr.Expr) -> object:
        return expression.accept(self)

    def visit_assign_expr(self, assign: expr.Assign) -> object:
        value: object = self.__evaluate(assign.value)
        distance: int | None = self._locals.get(assign)

        if distance is not None:  # Distance can be 0.
            self._environment.assign_at(distance, assign.name, value)
        else:
            self.globals.assign(assign.name, value)

        return value

    def visit_logical_expr(self, logical: expr.Logical) -> object:
        left: object = self.__evaluate(logical.left)

        if logical.operator.type == TokenType.OR and self.__is_truthy(left):
            return left

        if logical.operator.type == TokenType.AND and not self.__is_truthy(left):
            return left

        return self.__evaluate(logical.right)

    def visit_ternary_expr(self, ternary: expr.Ternary) -> object:
        condition: object = self.__evaluate(ternary.condition)
        result: object = None

        if self.__is_truthy(condition):
            result = self.__evaluate(ternary.consequent)
        else:
            result = self.__evaluate(ternary.alternative)

        return result

    def visit_binary_expr(self, binary: expr.Binary) -> object:
        operator: Token = binary.operator
        left: object = self.__evaluate(binary.left)
        right: object = self.__evaluate(binary.right)
        result: object = None

        match operator.type:
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    result = float(left) + float(right)
                elif isinstance(left, str) and isinstance(right, str):
                    result = str(left) + str(right)
                elif (isinstance(left, float) and isinstance(right, str)) or (
                    isinstance(left, str) and isinstance(right, float)
                ):
                    result = self.__stringify(left) + self.__stringify(right)
                else:
                    raise RuntimeException(
                        operator, "Operands cannot be concatenated or added."
                    )
            case TokenType.MINUS:
                self.__check_number_operands(operator, left, right)
                result = float(left) - float(right)  # type: ignore[arg-type]
            case TokenType.STAR:
                self.__check_number_operands(operator, left, right)
                result = float(left) * float(right)  # type: ignore[arg-type]
            case TokenType.SLASH:
                self.__check_number_operands(operator, left, right)
                result = float(left) / float(right)  # type: ignore[arg-type]
            case TokenType.MODULO:
                self.__check_number_operands(operator, left, right)
                result = float(left) % float(right)  # type: ignore[arg-type]
            case TokenType.EQUAL_EQUAL:
                result = self.__is_equal(left, right)  # type: ignore[arg-type]
            case TokenType.BANG_EQUAL:
                result = not self.__is_equal(left, right)  # type: ignore[arg-type]
            case TokenType.GREATER:
                self.__check_number_operands(operator, left, right)
                result = float(left) > float(right)  # type: ignore[arg-type]
            case TokenType.GREATER_EQUAL:
                self.__check_number_operands(operator, left, right)
                result = float(left) >= float(right)  # type: ignore[arg-type]
            case TokenType.LESS:
                self.__check_number_operands(operator, left, right)
                result = float(left) < float(right)  # type: ignore[arg-type]
            case TokenType.LESS_EQUAL:
                self.__check_number_operands(operator, left, right)
                result = float(left) <= float(right)  # type: ignore[arg-type]
            case TokenType.COMMA:
                result = right  # type: ignore[arg-type]

        return result

    def visit_call_expr(self, call: expr.Call) -> object:
        callee: object = self.__evaluate(call.callee)

        arguments: list[object] = []
        for argument in call.arguments:
            arguments.append(self.__evaluate(argument))

        if not isinstance(callee, LoxCallable):
            raise RuntimeException(call.paren, "Can only call functions and methods.")

        function: LoxCallable = callee
        if len(arguments) != function.arity():
            raise RuntimeException(
                call.paren,
                f"Expected {function.arity()} arguments but got {len(arguments)}.",
            )

        return function.call(self, arguments)

    def visit_get_expr(self, get: expr.Get) -> object:
        instance: object = self.__evaluate(get.object)

        if not isinstance(instance, LoxInstance):
            raise RuntimeException(
                get.name,
                "Only instances have properties.",
            )

        get_expr: object = instance.get(get.name)
        if isinstance(get_expr, LoxFunction) and get_expr.is_getter:
            return get_expr.call(self, [])

        return get_expr

    def visit_set_expr(self, set: expr.Set) -> object:
        instance: object = self.__evaluate(set.object)

        if not isinstance(instance, LoxInstance):
            raise RuntimeException(
                set.name,
                "Only instances have fields.",
            )

        value: object = self.__evaluate(set.value)
        instance.set(set.name, value)
        return value

    def visit_grouping_expr(self, grouping: expr.Grouping) -> object:
        return self.__evaluate(grouping.expression)

    def visit_literal_expr(self, literal: expr.Literal) -> object:
        return literal.value

    def visit_this_expr(self, this_: expr.This) -> object:
        return self.__look_up_variable(this_.keyword, this_)

    def visit_unary_expr(self, unary: expr.Unary) -> object:
        operator: Token = unary.operator
        right: object = self.__evaluate(unary.right)
        result: object = None

        match operator.type:
            case TokenType.MINUS:
                self.__check_number_operand(operator, right)
                result = -float(right)  # type: ignore[arg-type]
            case TokenType.BANG:
                result = not self.__is_truthy(right)

        return result

    def visit_variable_expr(self, variable: expr.Variable) -> object:
        return self.__look_up_variable(variable.name, variable)

    def __look_up_variable(
        self, name: Token, variable: expr.Variable | expr.This
    ) -> object:
        distance: int | None = self._locals.get(variable)
        if distance is None:
            return self.globals.get_(name)
        return self._environment.get_at(distance, name.lexeme)

    def visit_lambda_expr(self, lambda_: expr.Lambda) -> object:
        return LoxLambdaExpression(lambda_, self._environment)

    def __check_number_operand(self, operator: Token, operand: object) -> None:
        if isinstance(operand, float):
            return

        raise RuntimeException(operator, "Operand must be a number.")

    def __check_number_operands(
        self, operator: Token, left: object, right: object
    ) -> None:
        if isinstance(left, float) and isinstance(right, float):
            return

        raise RuntimeException(operator, "Operands must be numbers.")

    def __is_truthy(self, obj: object) -> bool:
        """Checks whether an obj can be evaluated to Lox's definition of
        truthiness, i.e., false and nil are falsey, and everything else
        is truthy."""
        if obj is None:
            return False
        elif isinstance(obj, bool):
            return obj
        else:
            return True

    def __is_equal(self, left: object, right: object) -> bool:
        # For matching the author's implementation. In Java calling equals() on
        # nil results in a NullPointerException. In Python, however, it's safe
        # to compare a value with None; i.e., the following is completely fine:
        #
        # return left == right

        if left is None and right is None:
            return True
        elif left is None:
            return False
        else:
            return left == right

    def __stringify(self, obj: object) -> str:
        if str(obj) == "None":
            return "nil"

        if isinstance(obj, float) and str(obj).endswith(".0"):
            return str(obj).split(".")[0]

        if isinstance(obj, bool):
            return str(obj).lower()

        return str(obj)


if __name__ == "__main__":
    pass
