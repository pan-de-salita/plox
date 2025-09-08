import sys

from . import expr
from .interpreter import Interpreter
from .parser import Parser
from .runtime_exception import RuntimeException
from .scanner import Scanner
from .token import Token
from .token_type import TokenType


class Lox:
    _interpreter: Interpreter = Interpreter()
    _had_error: bool = False
    _had_runtime_error: bool = False

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

            if Lox._had_error:
                sys.exit(65)  # UNIX/POSIX convention for data format error.
            if Lox._had_runtime_error:
                sys.exit(70)

    @staticmethod
    def __run_prompt() -> None:
        while True:
            line = input("> ")

            if not line:
                break

            Lox.__run(line)
            Lox._had_error = False

    @staticmethod
    def __run(source: str) -> None:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        parser: Parser = Parser(tokens=tokens)
        expression: expr.Expr | None = parser.parse()

        if Lox._had_error:
            return

        Lox._interpreter.interpret(expression)  # type: ignore[arg-type]

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
        else:
            raise RuntimeError("Lox.error called without line or token.")

    @staticmethod
    def runtime_error(error: RuntimeException) -> None:
        print(f"{str(error)}\n[line {error.token.line}]", file=sys.stderr)
        Lox._had_runtime_error = True

    @staticmethod
    def __report(line: int, where: str, message: str) -> None:
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        Lox._had_error = True


if __name__ == "__main__":
    Lox.main([])
