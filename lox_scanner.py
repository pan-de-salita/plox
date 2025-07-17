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

        while not self.__is_at_end():
            self.start = self.current
            self.__scan_token()

        self.tokens += [LoxToken(LoxTokenType.EOF, "", None, self.line)]
        return self.tokens

    def __scan_token(self) -> None:
        char: str = self.__advance()

        match char:
            case "(":
                self.__add_token(LoxTokenType.LEFT_PAREN)
            case ")":
                self.__add_token(LoxTokenType.RIGHT_PAREN)
            case "{":
                self.__add_token(LoxTokenType.LEFT_BRACE)
            case "}":
                self.__add_token(LoxTokenType.RIGHT_PAREN)
            case ",":
                self.__add_token(LoxTokenType.COMMA)
            case ".":
                self.__add_token(LoxTokenType.DOT)
            case "-":
                self.__add_token(LoxTokenType.MINUS)
            case "+":
                self.__add_token(LoxTokenType.PLUS)
            case ";":
                self.__add_token(LoxTokenType.SEMICOLON)
            case "*":
                self.__add_token(LoxTokenType.STAR)
            case "!":
                self.__add_token(
                    LoxTokenType.BANG_EQUAL if self.__match("=") else LoxTokenType.BANG
                )
            case "=":
                self.__add_token(
                    LoxTokenType.EQUAL_EQUAL
                    if self.__match("=")
                    else LoxTokenType.EQUAL
                )
            case "<":
                self.__add_token(
                    LoxTokenType.LESS_EQUAL if self.__match("=") else LoxTokenType.LESS
                )
            case ">":
                self.__add_token(
                    LoxTokenType.GREATER_EQUAL
                    if self.__match("=")
                    else LoxTokenType.GREATER
                )
            case "/":
                if self.__match("/"):
                    while self.__peek() != "\n" and not self.__is_at_end():
                        self.__advance()
                else:
                    self.__add_token(LoxTokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                self.line += 1
            case '"':
                self.__string()
            case _:
                from lox import Lox

                Lox.error(self.line, "Unexpected character.")

    def __is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def __advance(self) -> str:
        self.current += 1
        return self.source[self.current - 1]

    def __add_token(self, type: LoxTokenType, literal: str | None = None) -> None:
        # NOTE: self.current will be incremented to the right index because of
        # self.advance().
        text: str = self.source[self.start : self.current]
        self.tokens += [LoxToken(type, text, literal, self.line)]

    def __match(self, expected: str) -> bool:
        if self.__is_at_end():
            return False

        if self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def __peek(self) -> str:
        if self.__is_at_end():
            return "\0"

        return self.source[self.current]

    def __string(self):
        while self.__peek() != '"' and not self.__is_at_end():
            if self.__peek() == "\n":
                self.line += 1
            self.__advance()

        if self.__is_at_end():
            from lox import Lox

            Lox.error(self.line, "Unterminated string.")
            return

        # Consume the closing ".
        self.__advance()

        # Trim the surrounding quotes.
        string: str = self.source[self.start + 1 : self.current - 1]
        self.__add_token(LoxTokenType.STRING, string)

    # Own version
    # Less explicit about advancing to consume second quote
    # def __string(self):
    #     while not self.__match('"') and not self.__is_at_end():
    #         if self.__peek() == "\n":
    #             self.line += 1
    #         self.__advance()
    #
    #     if self.__is_at_end():
    #         from lox import Lox
    #
    #         Lox.error(self.line, "Unterminated string.")
    #         return
    #
    #     self.__add_token(
    #         LoxTokenType.STRING, self.source[self.start + 1 : self.current - 1]
    #     )
