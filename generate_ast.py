import sys


class GenerateAst:
    def main(self, args: list[str]) -> None:
        if len(args) != 1:
            print("Usage: generate_ast <output directory>", file=sys.stderr)
            sys.exit(64)

        output_dir = args[0]
