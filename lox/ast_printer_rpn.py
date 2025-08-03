from . import expr
from .token import Token
from .token_type import TokenType


class AstPrinterRpn(expr.Visitor[str]):
    """A (not very) pretty printer."""

    # NOTE: To be deleted.
    @staticmethod
    def main(expression: expr.Expr | None = None) -> None:
        if not expression or not isinstance(expression, expr.Expr):
            # 1 2 +
            # expression = expr.Binary(
            #     operator=Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
            #     left=expr.Literal(value=1),
            #     right=expr.Literal(value=2),
            # )

            # 1 2 + 4 3 - *
            expression = expr.Binary(
                operator=Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
                left=expr.Binary(
                    operator=Token(
                        type=TokenType.PLUS, lexeme="+", literal=None, line=1
                    ),
                    left=expr.Literal(value=1),
                    right=expr.Literal(value=2),
                ),
                right=expr.Binary(
                    operator=Token(
                        type=TokenType.MINUS, lexeme="-", literal=None, line=1
                    ),
                    left=expr.Literal(value=4),
                    right=expr.Literal(value=3),
                ),
            )

        print(AstPrinterRpn().print(expression))

    def print(self, expr: expr.Expr) -> str:
        """Pretty-print an expression in Lisp format."""
        return expr.accept(self)

    def visit_binary_expr(self, binary: expr.Binary) -> str:
        """Overrides Visitor.visit_binary_expr()."""
        return self.__format_as_rpn(binary.operator.lexeme, binary.left, binary.right)

    def visit_grouping_expr(self, grouping: expr.Grouping) -> str:
        """Overrides Visitor.visit_grouping_expr()."""
        return self.__format_as_rpn("group", grouping.expression)

    def visit_literal_expr(self, literal: expr.Literal) -> str:
        """Overrides Visitor.visit_literal_expr()."""
        if not literal.value:
            return "nil"

        return self.__format_as_rpn(str(literal.value))

    def visit_unary_expr(self, unary: expr.Unary) -> str:
        """Overrides Visitor.visit_unary_expr()."""
        return self.__format_as_rpn(unary.operator.lexeme, unary.right)

    def __format_as_rpn(self, name: str, *exprs: expr.Expr) -> str:
        if not exprs:
            return name

        return f"{''.join(e.accept(self) + ' ' for e in exprs)}{name}"


if __name__ == "__main__":
    AstPrinterRpn.main()
