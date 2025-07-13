import sys


class Lox:
    @staticmethod
    def main(args: list[str]) -> None:
        if len(args) > 1:
            print("Usage: jlox [script]")

            # 64 is code for "command line usage error" in Unix/POSIX conventions
            sys.exit(64)
        elif len(args) == 1:
            Lox.fun_file(args[0])
        else:
            Lox.run_prompt()

    @staticmethod
    def run_file(path: str) -> None:
        """File runner"""
        with open(path, encoding="utf-8") as bytes:
            Lox.run(bytes)

    @staticmethod
    def run_prompt() -> None:
        """Prompt"""
        while True:
            user_input = input("> ")
            if not user_input:
                break
            Lox.run(user_input)

    @staticmethod
    def run(source: str) -> None:
        scanner = Scanner(source)  # Scanner class not yet defined
        tokens = scanner.scan_tokens()

        for token in tokens:
            print(token)
