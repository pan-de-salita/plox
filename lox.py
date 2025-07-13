import sys

from scanner import Scanner


class Lox:
    had_error: bool = False

    @staticmethod
    def main(args: list[str]) -> None:
        if len(args) > 1:
            print("Usage: jlox [script]")
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

        for token in tokens:
            print(token)
            # Handle errors here?

    # NOTE: Separate the code that generates the errors from the code that reports them. Separate
    # phases of the front end will detect errors, but it's not really their job to know how to
    # present that to a user.

    @staticmethod
    def error(line: int, message: str) -> None:
        Lox.__report(line, "", message)

    @staticmethod
    def __report(line: int, where: str, message: str) -> None:
        print(f"[line {line}] Error {where}: {message}")
        Lox.had_error = True
