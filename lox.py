import sys


class Lox:
    @staticmethod
    def main(args: list[str]):
        if len(args) > 1:
            print("Usage: jlox [script]")
            sys.exit(64)
        elif len(args) == 1:
            Lox.run_file(args[0])
        else:
            Lox.run_prompt()

    @staticmethod
    def run_file(arg: str):
        pass

    @staticmethod
    def run_prompt():
        pass
