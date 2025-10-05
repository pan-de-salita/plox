import sys
from datetime import datetime

from .interpreter import Interpreter
from .parser import Parser
from .runtime_exception import RuntimeException
from .scanner import Scanner
from .stmt import Stmt
from .token import Token
from .token_type import TokenType

LANGUAGE_VERSION = 0.9


class Lox:
    def __init__(self) -> None:
        self._interpreter: Interpreter = Interpreter(self.runtime_error)
        self._had_error: bool = False
        self._had_runtime_error: bool = False

    def main(self, args: list[str]) -> None:
        if len(args) > 1:
            print("Usage: jlox [script]", file=sys.stderr)
            sys.exit(64)  # UNIX/POSIX convention for command line usage error.
        elif len(args) == 1:
            self.__run_file(args[0])
        else:
            self.__run_prompt()

    def __run_file(self, path: str) -> None:
        with open(path, encoding="utf-8") as file:
            bytes = file.read()
            self.__run(bytes)

            if self._had_error:
                sys.exit(65)  # UNIX/POSIX convention for data format error.
            if self._had_runtime_error:
                sys.exit(70)

    def __run_prompt(self) -> None:
        print(f"Lox (v{LANGUAGE_VERSION} as of {datetime.now()})")
        while True:
            try:
                line = input("> ")
            except EOFError:
                print()
                return
            except KeyboardInterrupt:
                print()
                continue

            if not line:
                break

            # Set _is_run_prompt to True so evaluated expressions are
            # automatically printed.
            self._interpreter._is_run_prompt = True

            self.__run(line)

            # Set _is_run_prompt back to False.
            self._interpreter._is_run_prompt = False

            self._had_error = False
            self._had_runtime_error = False

    def __run(self, source: str) -> None:
        scanner = Scanner(_source=source, _error_callback=self.lexical_error)
        tokens = scanner.scan_tokens()
        parser: Parser = Parser(_tokens=tokens, _error_callback=self.parse_error)
        statements: list[Stmt] = parser.parse()

        if self._had_error:
            return

        self._interpreter.interpret(statements)

    def lexical_error(self, message: str, line: int) -> None:
        self.__report("Lexical", line, "", message)

    def parse_error(self, message: str, token: Token) -> None:
        if token.type == TokenType.EOF:
            self.__report("Parse", token.line, " at end", message)
        else:
            self.__report("Parse", token.line, f" at {token.lexeme}", message)

    def runtime_error(self, error: RuntimeException) -> None:
        print(
            f"\nRuntimeError: {str(error)}\n[line {error.token.line}]", file=sys.stderr
        )
        self._had_runtime_error = True

    def __report(self, type: str, line: int, where: str, message: str) -> None:
        print(f"[line {line}] {type.title()}Error{where}: {message}", file=sys.stderr)
        self._had_error = True


if __name__ == "__main__":
    Lox().main(sys.argv[1:])
