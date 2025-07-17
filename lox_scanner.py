from dataclasses import dataclass, field

from lox_token import LoxToken
from lox_token_type import LoxTokenType


@dataclass()
class LoxScanner:
    source: str
    tokens: list[LoxToken] = field(default_factory=list)
    start: int = 0
    current: int = 0
    line: int = 1

    def scan_tokens(self) -> list[LoxToken]:
        # For inspection purposes.
        print(repr(self.source))

        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens += [LoxToken(LoxTokenType.EOF, "", None, self.line)]
        return self.tokens

    def scan_token(self) -> None:
        char: str = self.advance()

        match char:
            case "(":
                self.add_token(LoxTokenType.LEFT_PAREN)
            case ")":
                self.add_token(LoxTokenType.RIGHT_PAREN)
            case "{":
                self.add_token(LoxTokenType.LEFT_BRACE)
            case "}":
                self.add_token(LoxTokenType.RIGHT_PAREN)
            case ",":
                self.add_token(LoxTokenType.COMMA)
            case ".":
                self.add_token(LoxTokenType.DOT)
            case "-":
                self.add_token(LoxTokenType.MINUS)
            case "+":
                self.add_token(LoxTokenType.PLUS)
            case ";":
                self.add_token(LoxTokenType.SEMICOLON)
            case "*":
                self.add_token(LoxTokenType.STAR)
            case "!":
                self.add_token(
                    LoxTokenType.BANG_EQUAL if self.__match("=") else LoxTokenType.BANG
                )
            case "=":
                self.add_token(
                    LoxTokenType.EQUAL_EQUAL
                    if self.__match("=")
                    else LoxTokenType.EQUAL
                )
            case "<":
                self.add_token(
                    LoxTokenType.LESS_EQUAL if self.__match("=") else LoxTokenType.LESS
                )
            case ">":
                self.add_token(
                    LoxTokenType.GREATER_EQUAL
                    if self.__match("=")
                    else LoxTokenType.GREATER
                )
            case " ":
                pass
            case "\n":
                self.line += 1
            case _:
                from lox import Lox

                Lox.error(self.line, "Unexpected character.")

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        self.current += 1
        return self.source[self.current - 1]

    def add_token(self, type: LoxTokenType, literal: str | None = None) -> None:
        # NOTE: self.current will be incremented to the right index because of
        # self.advance().
        text: str = self.source[self.start : self.current]
        self.tokens += [LoxToken(type, text, literal, self.line)]

    def __match(self, expected: str) -> bool:
        if self.is_at_end():
            return False

        if self.source[self.current] == expected:
            return False

        self.current += 1
        return True
