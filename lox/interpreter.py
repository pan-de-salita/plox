from . import expr
from .ast_printer import AstPrinter
from .token import Token
from .token_type import TokenType


class Interpreter(expr.Visitor[object]):
    def main(self, expression: expr.Expr) -> str:
        # For testing purposes:
        print(AstPrinter().print(expression))
        return self.__stringify(self.__evaluate(expression))

    def __evaluate(self, expression: expr.Expr) -> object:
        return expression.accept(self)

    def visit_ternary_expr(self, ternary: expr.Ternary) -> object:
        condition: object = self.__evaluate(ternary.condition)
        res: object = None

        if self.__is_truthy(condition):
            if condition:
                res = self.__evaluate(ternary.consequent)
            else:
                res = self.__evaluate(ternary.alternative)

        return res

    def visit_binary_expr(self, binary: expr.Binary) -> object:
        # TODO: Handle errors.

        operand: str = binary.operator.lexeme
        left: object = self.__evaluate(binary.left)
        right: object = self.__evaluate(binary.right)
        res: object = None

        match operand:
            case "+":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} + {right}")
                elif self.__is_both_string(left, right):
                    res = eval(f"'{left}' + '{right}'")
            case "-":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} - {right}")
            case "*":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} * {right}")
            case "/":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} / {right}")
            case "==":
                res = eval(f"{left} == {right}")
            case "!=":
                res = eval(f"{left} != {right}")
            case ">":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} > {right}")
            case ">=":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} >= {right}")
            case "<":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} < {right}")
            case "<=":
                if self.__is_both_float(left, right):
                    res = eval(f"{left} <= {right}")

        return res

    def visit_grouping_expr(self, grouping: expr.Grouping) -> object:
        return self.__evaluate(grouping.expression)

    def visit_literal_expr(self, literal: expr.Literal) -> object:
        return literal.value

    def visit_unary_expr(self, unary: expr.Unary) -> object:
        # TODO: Handle errors.

        operand: str = unary.operator.lexeme
        right: object = self.__evaluate(unary.right)
        res: object = None

        match operand:
            case "-":
                if isinstance(right, float):
                    res = -right
            case "!":
                if self.__is_truthy(right):
                    res = not right

        return res

    def __is_truthy(self, obj: object) -> bool:
        if obj is None:
            return False
        elif isinstance(obj, bool) and obj:
            return False
        else:
            return True

    def __is_both_float(self, left: object, right: object) -> bool:
        return isinstance(left, float) and isinstance(right, float)

    def __is_both_string(self, left: object, right: object) -> bool:
        return isinstance(left, str) and isinstance(right, str)

    def __stringify(self, obj: object) -> str:
        if isinstance(obj, float):
            return str(obj).split(".")[0]
        else:
            return str(obj)


if __name__ == "__main__":
    interpreter: Interpreter = Interpreter()
    expression: expr.Expr = expr.Ternary(
        condition=expr.Binary(
            left=expr.Binary(
                left=expr.Literal(value=float(5)),
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

    print(interpreter.main(expression))

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
