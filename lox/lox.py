import sys

from . import expr
from .ast_printer import AstPrinter
from .scanner import Scanner
from .token import Token
from .token_type import TokenType


class Lox:
    had_error: bool = False

    @staticmethod
    def main(args: list[str]) -> None:
        if len(args) > 1:
            print("Usage: jlox [script]", file=sys.stderr)
            sys.exit(64)  # UNIX/POSIX convention for command line usage error.
        elif len(args) == 1:
            Lox.__run_file(args[0])
        else:
            Lox.__run_prompt()

    @staticmethod
    def __run_file(path: str) -> None:
        with open(path, encoding="utf-8") as file:
            bytes = file.read()
            Lox.__run(bytes)
            if Lox.had_error:
                sys.exit(65)  # UNIX/POSIX convention for data format error.

    @staticmethod
    def __run_prompt() -> None:
        while True:
            line = input("> ")
            if not line:
                break
            Lox.__run(line)
            Lox.had_error = False

    @staticmethod
    def __run(source: str) -> None:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        from .parser import Parser

        parser: Parser = Parser(tokens=tokens)
        expression: expr.Expr | None = parser.parse()

        if expression:
            print(AstPrinter().print(expression))

    @staticmethod
    def error(
        message: str,
        line: int | None = None,
        token: Token | None = None,
    ) -> None:
        if line:
            Lox.__report(line, "", message)
        elif token:
            if token.type == TokenType.EOF:
                Lox.__report(token.line, " at end", message)
            else:
                Lox.__report(token.line, f" at {token.lexeme}", message)

    @staticmethod
    def __report(line: int, where: str, message: str) -> None:
        print(f"[line {line}] Error{where}: {message}", sys.stderr)
        Lox.had_error = True


if __name__ == "__main__":
    Lox.main([])
