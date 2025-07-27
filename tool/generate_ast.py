import sys


class GenerateAst:
    @staticmethod
    def main(args: list[str]) -> None:
        if len(args) != 1:
            print("Usage: generate_ast <output directory>", file=sys.stderr)
            sys.exit(64)

        output_dir: str = args[0]
        GenerateAst.__define_ast(
            output_dir,
            "Expr",
            [
                "Binary   : Expr left, Token operator, Expr right",
                "Grouping : Expr expression",
                "Literal  : object value",
                "Unary    : Token operator, Expr right",
            ],
        )

    @staticmethod
    def __define_ast(output_dir: str, base_name: str, types: list[str]) -> None:
        TAB = "    "

        path: str = f"{output_dir}/{base_name.lower()}.py"
        with open(path, "w", encoding="utf-8") as writer:
            # Import builtin libraries.
            writer.write("from abc import ABC")
            writer.write("\n")
            writer.write("from dataclasses import dataclass")
            writer.write("\n")
            writer.write("\n")
            writer.write("\n")

            # Import custom libraries.
            writer.write("from lox.token import Token")
            writer.write("\n")
            writer.write("\n")
            writer.write("\n")

            # Write parent Expr class.
            writer.write("@dataclass(frozen=True)")
            writer.write("\n")
            writer.write(f"class {base_name}(ABC):")
            writer.write("\n")
            writer.write(f"{TAB}pass")
            writer.write("\n")
            writer.write("\n")
            writer.write("\n")

            # Write child classes.
            for idx, expr in enumerate(types):
                expr_parts: list[str] = [elem.strip() for elem in expr.split(":")]
                expr_name: str = expr_parts[0]
                writer.write("@dataclass(frozen=True)")
                writer.write("\n")
                writer.write(f"class {expr_name}({base_name}):")
                writer.write("\n")

                expr_attrs: list[str] = [
                    attr.strip() for attr in expr_parts[1].split(",")
                ]
                for attr in expr_attrs:
                    attr_parts: list[str] = [elem.strip() for elem in attr.split(" ")]
                    attr_name: str = attr_parts[1]
                    attr_type: str = attr_parts[0]
                    writer.write(f"{TAB}{attr_name}: {attr_type}")
                    writer.write("\n")

                # Add new lines to the end of the child class's definition only
                # if not final child class to written.
                if idx != len(types) - 1:
                    writer.write("\n")
                    writer.write("\n")


if __name__ == "__main__":
    # Testing.
    GenerateAst.main(["expr"])
    with open("expr/expr.py", "r", encoding="utf-8") as file:
        print(file.read())
