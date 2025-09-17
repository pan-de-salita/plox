import builtins
from dataclasses import dataclass, field
from typing import Callable

from . import expr, stmt
from .environment import Environment
from .runtime_exception import RuntimeException
from .token import Token
from .token_type import TokenType


@dataclass()
class Interpreter(expr.Visitor[object], stmt.Visitor[None]):
    _error_callback: Callable[[RuntimeException], None]
    _environment: Environment = field(default_factory=Environment)
    _run_prompt: bool = False

    def interpret(self, statements: list[stmt.Stmt]) -> None:
        # For testing purposes:
        # print(AstPrinter().print(expression))
        try:
            # value: object = self.__evaluate(expression)
            # print(self.__stringify(value))
            for statement in statements:
                self.__execute(statement)
        except RuntimeException as error:
            self._error_callback(error)

    def __execute(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    def visit_block_stmt(self, block: stmt.Block) -> None:
        self.execute_block(
            statements=block.statements,
            environment=Environment(enclosing=self._environment),
        )

    def execute_block(
        self, statements: list[stmt.Stmt], environment: Environment
    ) -> None:
        previous_environment: Environment = self._environment
        try:
            self._environment = environment
            for statement in statements:
                self.__execute(statement=statement)
        finally:
            self._environment = previous_environment

    def visit_expression_stmt(self, expression: stmt.Expression) -> None:
        value: object = self.__evaluate(expression.expression)

        if self._run_prompt:
            print(value)

    def visit_print_stmt(self, print: stmt.Print) -> None:
        builtins.print(self.__stringify(self.__evaluate(print.expression)))

    def visit_var_stmt(self, var: stmt.Var) -> None:
        value: None | object = None
        if var.expression:
            value = self.__evaluate(var.expression)

        self._environment.define(
            name_lexeme=var.name.lexeme, value=value, is_initialized=var.is_initialized
        )

    def __evaluate(self, expression: expr.Expr) -> object:
        return expression.accept(self)

    def visit_assign_expr(self, assign: expr.Assign) -> object:
        value: object = self.__evaluate(assign.value)
        self._environment.assign(name=assign.name, value=value)

        return value

    def visit_ternary_expr(self, ternary: expr.Ternary) -> object:
        condition: object = self.__evaluate(ternary.condition)
        result: object = None

        if self.__is_truthy(condition):
            if condition:
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
        return self._environment.get(variable.name)

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

        if isinstance(obj, float):
            return str(obj).split(".")[0]

        if isinstance(obj, bool):
            return str(obj).lower()

        return str(obj)


if __name__ == "__main__":
    pass
