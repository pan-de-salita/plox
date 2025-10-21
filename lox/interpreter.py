from __future__ import annotations

import builtins
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from . import expr, stmt
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
class AnonymousLoxCallable(LoxCallable):
    _callable: Callable[[Interpreter, list[object]], object]
    _arity: int

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        return self._callable(interpreter, arguments)

    def arity(self) -> int:
        return self._arity

    def __str__(self) -> str:
        return "<native fn>"


@dataclass
class LoxFunction(LoxCallable):
    _declaration: stmt.Function

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        try:
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
            # there are multiple calls to the same functin in play at the same time,
            # each needs its own environment, even though they are all calls to the
            # same function.
            #
            # At the beginning of each function call (not at the function declaration),
            # this call() method creates a new environment. Then it walks the
            # parameter and argument lists in lockstep. For each pair, it creates a
            # *new* variable with the paremeter's name and binds it to the argument's value.
            environment: Environment = Environment(enclosing=interpreter.globals)

            for idx, param in enumerate(self._declaration.params):
                environment.define(
                    name=param.lexeme,
                    value=arguments[idx],
                    is_initialized=True,
                )

            interpreter.execute_block(self._declaration.body, environment)

            return None
        except Return as return_:
            return return_.value

    def arity(self) -> int:
        return len(self._declaration.params)

    def __str__(self) -> str:
        return f"<fn {self._declaration.name.lexeme}>"


class Interpreter(expr.Visitor[object], stmt.Visitor[None]):
    def __init__(self, error_callback: Callable[[RuntimeException], None]) -> None:
        self.globals: Environment = (
            Environment()
        )  # Fixed reference to the outermost global environment

        self._error_callback = error_callback
        self.environment: Environment = self.globals
        self._is_run_prompt: bool = False
        self._is_break: bool = False

        self.globals.define(
            name="clock",
            value=AnonymousLoxCallable(
                _callable=lambda interpreter, arguments: time.time(), _arity=0
            ),
            is_initialized=True,
        )

    def interpret(self, statements: list[stmt.Stmt]) -> None:
        try:
            for statement in statements:
                self.__execute(statement)
        except RuntimeException as error:
            self._error_callback(error)

    def __execute(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    def visit_var_stmt(self, var_: stmt.Var) -> None:
        value: None | object = None
        if var_.expression:
            value = self.__evaluate(var_.expression)

        self.environment.define(
            name=var_.name.lexeme,
            value=value,
            is_initialized=var_.is_initialized,
        )

    def visit_while_stmt(self, while_: stmt.While) -> None:
        while self.__is_truthy(self.__evaluate(while_.condition)):
            if self._is_break:
                break

            self.__execute(while_.body)

        self.__reset_is_break()

    def visit_break_stmt(self, break_: stmt.Break) -> None:
        self._is_break = True

    def visit_function_stmt(self, function: stmt.Function) -> None:
        self.environment.define(
            name=function.name.lexeme,
            value=LoxFunction(function),
            is_initialized=True,
        )

    def visit_if_stmt(self, if_: stmt.If) -> None:
        if self.__is_truthy(self.__evaluate(if_.condition)):
            self.__execute(if_.then_branch)
        elif if_.else_branch is not None:
            self.__execute(if_.else_branch)

    def visit_block_stmt(self, block: stmt.Block) -> None:
        self.execute_block(
            block_statements=block.statements,
            environment=Environment(enclosing=self.environment),
        )

    def execute_block(
        self, block_statements: list[stmt.Stmt], environment: Environment
    ) -> None:
        previous_environment: Environment = self.environment
        try:
            # Switch self's environment to be a new one with previousenvironment
            # as its enclosure. This allows for executed statments within the
            # block to have access to the state in the enclosing environment(s).
            self.environment = environment
            for block_statement in block_statements:
                if self._is_break:
                    break

                self.__execute(block_statement)
        finally:
            # Restore old environment.
            self.environment = previous_environment

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
        self.environment.assign(name=assign.name, value=value)

        return value

    def visit_logical_expr(self, logical: expr.Logical) -> object:
        left: object = self.__evaluate(logical.left)

        if logical.operator.type == TokenType.OR:
            if self.__is_truthy(left):
                return left
        elif logical.operator.type == TokenType.AND:
            if not self.__is_truthy(left):
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

    def visit_grouping_expr(self, grouping: expr.Grouping) -> object:
        return self.__evaluate(grouping.expression)

    def visit_literal_expr(self, literal: expr.Literal) -> object:
        return literal.value

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
        return self.environment.get(variable.name)

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

    def __reset_is_break(self) -> None:
        self._is_break = False


if __name__ == "__main__":
    pass
