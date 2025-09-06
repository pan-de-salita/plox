from . import expr
from .lox import Lox
from .runtime_exception import RuntimeException
from .token import Token
from .token_type import TokenType


class Interpreter(expr.Visitor[object]):
    def interpret(self, expression: expr.Expr) -> None:
        # For testing purposes:
        # print(AstPrinter().print(expression))
        try:
            value: object = self.__evaluate(expression)
            print(self.__stringify(value))
        except RuntimeException as error:
            Lox.runtime_error(error)

    def __evaluate(self, expression: expr.Expr) -> object:
        return expression.accept(self)

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
        # TODO: Handle errors.

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
                else:
                    raise RuntimeException(
                        operator, "Operands must be two numbers or two strings."
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

        return result

    def visit_grouping_expr(self, grouping: expr.Grouping) -> object:
        return self.__evaluate(grouping.expression)

    def visit_literal_expr(self, literal: expr.Literal) -> object:
        return literal.value

    def visit_unary_expr(self, unary: expr.Unary) -> object:
        # TODO: Handle errors.

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
        if object is None:
            return "nil"

        if isinstance(obj, float):
            return str(obj).split(".")[0]

        return str(obj)


if __name__ == "__main__":
    interpreter: Interpreter = Interpreter()
    expression: expr.Expr = expr.Ternary(
        condition=expr.Binary(
            left=expr.Binary(
                left=expr.Literal(value="five"),
                operator=Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
                right=expr.Literal(value=float(0)),
            ),
            operator=Token(
                type=TokenType.EQUAL_EQUAL, lexeme="==", literal=None, line=1
            ),
            right=expr.Literal(value=float(5)),
        ),
        consequent=expr.Binary(
            left=expr.Literal(value=float(5)),
            operator=Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
            right=expr.Literal(value=float(5)),
        ),
        alternative=expr.Binary(
            left=expr.Literal(value=float(0)),
            operator=Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
            right=expr.Literal(value=float(0)),
        ),
    )

    interpreter.interpret(expression)

    # Tests:
    # expr.Binary(
    #     left=expr.Literal(value="Hello "),
    #     operator=Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
    #     right=expr.Literal(value="World"),
    # )
    # expr.Binary(
    #     left=expr.Literal(value=float(5)),
    #     operator=Token(
    #         type=TokenType.EQUAL_EQUAL, lexeme="==", literal=None, line=1
    #     ),
    #     right=expr.Literal(value=float(5)),
    # )
    # expr.Literal(value=float(10))
    # expr.Unary(
    #     operator=Token(type=TokenType.MINUS, lexeme="-", literal=None, line=1),
    #     right=expr.Literal(value=float(10)),
    # )
    # expr.Unary(
    #     operator=Token(type=TokenType.BANG, lexeme="!", literal=None, line=1),
    #     right=expr.Literal(value=False),
    # )
