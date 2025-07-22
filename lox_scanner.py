from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from lox_token import LoxToken
from lox_token_type import LoxTokenType


@dataclass()
class LoxScanner:
    source: str
    tokens: list[LoxToken] = field(default_factory=list)
    start: int = 0
    current: int = 0
    line: int = 1
    keywords: MappingProxyType[str, LoxTokenType] = MappingProxyType(
        {
            keyword.name.lower(): keyword
            for keyword in [
                LoxTokenType.AND,
                LoxTokenType.CLASS,
                LoxTokenType.ELSE,
                LoxTokenType.FALSE,
                LoxTokenType.FOR,
                LoxTokenType.FUN,
                LoxTokenType.IF,
                LoxTokenType.NIL,
                LoxTokenType.OR,
                LoxTokenType.PRINT,
                LoxTokenType.RETURN,
                LoxTokenType.SUPER,
                LoxTokenType.THIS,
                LoxTokenType.TRUE,
                LoxTokenType.VAR,
                LoxTokenType.WHILE,
            ]
        }
    )

    def scan_tokens(self) -> list[LoxToken]:
        """
        Scans tokens from source.
        """
        # For inspection purposes.
        print(repr(self.source))

        while not self.__is_at_end():
            self.start = self.current
            self.__scan_token()

        self.tokens += [LoxToken(LoxTokenType.EOF, "", None, self.line)]
        return self.tokens

    def __scan_token(self) -> None:
        """
        Scan an individual token.
        """
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
                elif self.__match("*"):
                    self.__block_comment()
                else:
                    self.__add_token(LoxTokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                self.line += 1
            case '"':
                self.__string()
            case _:
                if self.__is_digit(char):
                    self.__number()
                elif self.__is_alpha(char):
                    self.__identifier()
                else:
                    from lox import Lox

                    Lox.error(self.line, "Unexpected character.")

    def __is_at_end(self) -> bool:
        """
        Checks if current points to the end of source. Useful for preventing
        IndexError.
        """
        return self.current >= len(self.source)

    def __advance(self) -> str:
        """
        Advances current.
        Returns current scanned character in source.
        """
        self.current += 1
        return self.source[self.current - 1]

    def __add_token(self, type: LoxTokenType, literal: Any = None) -> None:
        """
        Adds a token to self.tokens.
        """
        # NOTE: self.current will be incremented to the right index because of
        # self.advance().
        text: str = self.source[self.start : self.current]
        self.tokens += [LoxToken(type, text, literal, self.line)]

    def __match(self, expected: str) -> bool:
        """
        Checks if expected matches the current character being scanned.
        Advances current if True.
        """
        if self.__is_at_end():
            return False

        if self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def __peek(self) -> str:
        """
        Looks ahead by one character in source.
        """
        if self.__is_at_end():
            return "\0"

        return self.source[self.current]

    def __string(self) -> None:
        """
        Produces a string token.
        """
        # Use of self.__is_at_end() needed to avoid IndexError.
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

    # Own version.
    # Less explicit about advancing to consume second quote.
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

    def __is_digit(self, char: str) -> bool:
        """
        Checks if char is a digit.
        """
        return char in map(str, range(0, 10))

    def __number(self) -> None:
        """
        Produces a number token.
        """
        while self.__is_digit(self.__peek()):
            self.__advance()

        if self.__peek() == "." and self.__is_digit(self.__peek_next()):
            self.__advance()

            while self.__is_digit(self.__peek()):
                self.__advance()

        self.__add_token(
            LoxTokenType.NUMBER, float(self.source[self.start : self.current])
        )

    def __peek_next(self) -> str:
        """
        Looks ahead by two characters in source.
        """
        if self.current + 1 >= len(self.source):
            return "\0"

        return self.source[self.current + 1]

    def __identifier(self) -> None:
        """
        Produces an identifier token.

        NOTE: An identifier can be:
        - An identifier proper
        - A reserved keyword
        """
        while self.__is_alpha_numeric(self.__peek()):
            self.__advance()

        identifier = self.source[self.start : self.current]
        keyword = self.keywords.get(identifier)

        if keyword:
            self.__add_token(keyword)
        else:
            self.__add_token(LoxTokenType.IDENTIFIER)

    def __is_alpha_numeric(self, char: str) -> bool:
        """
        Checks if char is alphanumeric.
        """
        return self.__is_alpha(char) or self.__is_digit(char)

    def __is_alpha(self, char: str) -> bool:
        """
        Checks if char is alphabetical or an underscore.
        """
        import string

        return char in string.ascii_letters + "_"

    # Iter 1:
    # def __block_comment(self) -> None:
    #     while (
    #         not self.__is_two_chars_before_end() and not self.__is_block_comment_close()
    #     ):
    #         self.__advance()
    #
    #     if not self.__is_two_chars_before_end() and self.__is_block_comment_close():
    #         self.__advance()
    #         self.__advance()
    #         return
    #     else:
    #         from lox import Lox
    #
    #         Lox.error(self.line, "Unterminated block comment.")
    #         print(
    #             "Unterminated block comment: " + self.source[self.start : self.current]
    #         )
    #
    # def __is_two_chars_before_end(self) -> bool:
    #     return self.current + 1 == len(self.source)
    #
    # def __is_block_comment_close(self) -> bool:
    #     return self.__peek() + self.__peek_next() == "*/"

    # Iter 2:
    def __block_comment(self) -> None:
        # Loop until we find */ or reach end.
        while self.current + 1 < len(self.source):
            if self.__peek() + self.__peek_next() == "*/":
                self.__advance()  # Consume *.
                self.__advance()  # Consume /.
                return

            # Use of __peek() is more defensive.
            if self.__peek() == "\n":
                self.line += 1  # Track line number.

            self.__advance()

        from lox import Lox

        Lox.error(self.line, "Unterminated block comment.")
