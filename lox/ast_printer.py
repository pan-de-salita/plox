from . import expr
from .token import Token
from .token_type import TokenType


class AstPrinter(expr.Visitor):
    """A (not very) pretty printer."""

    @staticmethod
    def main() -> None:
        # (* (- 123) (group 45.67))
        expression: expr.Expr = expr.Binary(
            left=expr.Unary(
                operator=Token(type=TokenType.MINUS, lexeme="-", literal=None, line=1),
                right=expr.Literal(value=123),
            ),
            operator=Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
            right=expr.Grouping(expr.Literal(value=45.67)),
        )

        printer = AstPrinter()
        print(printer.print(expression))

    def print(self, expr: expr.Expr) -> str:
        return expr.accept(self)

    def visit_binary_expr(self, binary: expr.Binary) -> str:
        return ""

    def visit_grouping_expr(self, grouping: expr.Grouping) -> str:
        return ""

    def visit_literal_expr(self, literal: expr.Literal) -> str:
        return ""

    def visit_unary_expr(self, unary: expr.Unary) -> str:
        return ""
