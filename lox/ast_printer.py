from . import expr
from .token import Token
from .token_type import TokenType


class AstPrinter(expr.Visitor[str]):
    """A (not very) pretty printer."""

    # NOTE: To be deleted.
    @staticmethod
    def main(expression: expr.Expr | None = None) -> None:
        if not expression or not isinstance(expression, expr.Expr):
            # (+ 1 2)
            # expression: expr.Expr = expr.Binary(
            #     left=expr.Literal(value=1),
            #     operator=Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
            #     right=expr.Literal(value=2),
            # )

            # (* (- 123) (group 45.67))
            # expression: expr.Expr = expr.Binary(
            #     left=expr.Unary(
            #         operator=Token(type=TokenType.MINUS, lexeme="-", literal=None, line=1),
            #         right=expr.Literal(value=123),
            #     ),
            #     operator=Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
            #     right=expr.Grouping(expression=expr.Literal(value=45.67)),
            # )

            # (* (- 123) (* (- 0.4 (/ 5 6)) (group 78.91)))
            expression = expr.Binary(
                left=expr.Unary(
                    operator=Token(
                        type=TokenType.MINUS, lexeme="-", literal=None, line=1
                    ),
                    right=expr.Literal(value=123),
                ),
                operator=Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
                right=expr.Binary(
                    left=expr.Binary(
                        operator=Token(
                            type=TokenType.MINUS, lexeme="-", literal=None, line=1
                        ),
                        left=expr.Literal(value=0.4),
                        right=expr.Binary(
                            left=expr.Literal(value=5),
                            operator=Token(
                                type=TokenType.SLASH, lexeme="/", literal=None, line=1
                            ),
                            right=expr.Literal(value=6),
                        ),
                    ),
                    operator=Token(
                        type=TokenType.STAR, lexeme="*", literal=None, line=1
                    ),
                    right=expr.Grouping(expression=expr.Literal(value=78.910)),
                ),
            )

        print(AstPrinter().print(expression))

    def print(self, expr: expr.Expr) -> str:
        """Pretty-print an expression in Lisp format."""
        return expr.accept(self)

    def visit_binary_expr(self, binary: expr.Binary) -> str:
        """Overrides Visitor.visit_binary_expr()."""
        return self.__parenthesize(binary.operator.lexeme, binary.left, binary.right)

    def visit_grouping_expr(self, grouping: expr.Grouping) -> str:
        """Overrides Visitor.visit_grouping_expr()."""
        return self.__parenthesize("group", grouping.expression)

    def visit_literal_expr(self, literal: expr.Literal) -> str:
        """Overrides Visitor.visit_literal_expr()."""
        if not literal.value:
            return "nil"

        return self.__parenthesize(str(literal.value))

    def visit_unary_expr(self, unary: expr.Unary) -> str:
        """Overrides Visitor.visit_unary_expr()."""
        return self.__parenthesize(unary.operator.lexeme, unary.right)

    def __parenthesize(self, name: str, *exprs: expr.Expr) -> str:
        """Parenthasize expression unless exprs in None."""
        # Iter 1 (Funtional):
        # from functools import reduce
        #
        # return (
        #     ("(" if exprs else "")
        #     + name
        #     + reduce(lambda acc, curr: acc + " " + (curr.accept(self)), exprs, "")
        #     + (")" if exprs else "")
        # )

        # Iter 2 (Imperative):
        # parenthasized = name
        # for e in exprs:
        #     parenthasized += f" {e.accept(self)}"
        #
        # return parenthasized if not exprs else f"({parenthasized})"

        # Iter 3:
        # return (
        #     ("(" if exprs else "")
        #     + name
        #     + "".join(" " + e.accept(self) for e in exprs)
        #     + (")" if exprs else "")
        # )

        if not exprs:
            return name

        return f"({name}{''.join(' ' + e.accept(self) for e in exprs)})"


if __name__ == "__main__":
    AstPrinter.main()
