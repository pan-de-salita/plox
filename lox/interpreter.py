from dataclasses import dataclass

from . import expr


@dataclass()
class Interpreter(expr.Visitor[str]):
    @staticmethod
    def main() -> str:
        return "from Interpreter.main()"

    def visit_ternary_expr(self, ternary: expr.Ternary) -> str:
        return "from visit_ternary_expr()"

    def visit_binary_expr(self, binary: expr.Binary) -> str:
        return "from visit_binary_expr()"

    def visit_grouping_expr(self, grouping: expr.Grouping) -> str:
        return "from visit_grouping_expr()"

    def visit_literal_expr(self, literal: expr.Literal) -> str:
        return "from visit_literal_expr()"

    def visit_unary_expr(self, unary: expr.Unary) -> str:
        return "from visit_unary_expr()"


if __name__ == "__main__":
    interpreter = Interpreter()
    print(interpreter.main())
