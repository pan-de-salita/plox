from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, ClassVar

from .token import Token
from .token_type import TokenType


@dataclass()
class Scanner:
    _KEYWORDS = [
        TokenType.AND,
        TokenType.CLASS,
        TokenType.ELSE,
        TokenType.FALSE,
        TokenType.FOR,
        TokenType.FUN,
        TokenType.IF,
        TokenType.NIL,
        TokenType.OR,
        TokenType.PRINT,
        TokenType.RETURN,
        TokenType.SUPER,
        TokenType.THIS,
        TokenType.TRUE,
        TokenType.VAR,
        TokenType.WHILE,
    ]
    keywords: ClassVar[MappingProxyType[str, TokenType]] = MappingProxyType(
        {keyword.name.lower(): keyword for keyword in _KEYWORDS}
    )

    source: str
    tokens: list[Token] = field(default_factory=list)
    start: int = 0
    current: int = 0
    line: int = 1

    def scan_tokens(self) -> list[Token]:
        """
        Scan tokens from source.
        """
        # For inspection purposes.
        print(f"Source length: {len(self.source)}")
        print("Source:")
        print(repr(self.source) + "\n")

        while not self.__is_at_end():
            self.start = self.current
            self.__scan_token()

        self.tokens += [Token(TokenType.EOF, "", None, self.line)]
        return self.tokens

    def __scan_token(self) -> None:
        """
        Scan an individual token.
        """
        char: str = self.__advance()

        match char:
            case "(":
                self.__add_token(TokenType.LEFT_PAREN)
            case ")":
                self.__add_token(TokenType.RIGHT_PAREN)
            case "{":
                self.__add_token(TokenType.LEFT_BRACE)
            case "}":
                self.__add_token(TokenType.RIGHT_BRACE)
            case ",":
                self.__add_token(TokenType.COMMA)
            case ".":
                self.__add_token(TokenType.DOT)
            case "-":
                self.__add_token(TokenType.MINUS)
            case "+":
                self.__add_token(TokenType.PLUS)
            case ";":
                self.__add_token(TokenType.SEMICOLON)
            case "*":
                self.__add_token(TokenType.STAR)
            case "!":
                self.__add_token(
                    TokenType.BANG_EQUAL if self.__match("=") else TokenType.BANG
                )
            case "=":
                self.__add_token(
                    TokenType.EQUAL_EQUAL if self.__match("=") else TokenType.EQUAL
                )
            case "<":
                self.__add_token(
                    TokenType.LESS_EQUAL if self.__match("=") else TokenType.LESS
                )
            case ">":
                self.__add_token(
                    TokenType.GREATER_EQUAL if self.__match("=") else TokenType.GREATER
                )
            case "/":
                if self.__match("/"):
                    while self.__peek() != "\n" and not self.__is_at_end():
                        self.__advance()
                elif self.__match("*"):
                    self.__block_comments()
                else:
                    self.__add_token(TokenType.SLASH)
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
                    from .lox import Lox

                    Lox.error(self.line, "Unexpected character.")

    def __add_token(self, type: TokenType, literal: Any = None) -> None:
        """
        Add a token to self.tokens.
        """
        # NOTE: self.current will be incremented to the right index because of
        # self.advance().
        text: str = self.source[self.start : self.current]
        self.tokens += [Token(type, text, literal, self.line)]

    def __advance(self) -> str:
        """
        Advance current.
        Return current scanned character in source.
        """
        self.current += 1
        return self.source[self.current - 1]

    def __match(self, expected: str) -> bool:
        """
        Check if expected matches the current character being scanned.
        Advance current if True.
        """
        if self.__is_at_end():
            return False

        if self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def __peek(self) -> str:
        """
        Look ahead by one character in source.
        """
        if self.__is_at_end():
            return "\0"

        return self.source[self.current]

    def __peek_next(self) -> str:
        """
        Look ahead by two characters in source.
        """
        if self.current + 1 >= len(self.source):
            return "\0"

        return self.source[self.current + 1]

    # Iter 1 (own version).
    # Less explicit about advancing to consume second quote.
    # def __string(self):
    #     while not self.__match('"') and not self.__is_at_end():
    #         if self.__peek() == "\n":
    #             self.line += 1
    #         self.__advance()
    #
    #     if self.__is_at_end():
    #         from .lox import Lox
    #
    #         Lox.error(self.line, "Unterminated string.")
    #         return
    #
    #     self.__add_token(
    #         TokenType.STRING, self.source[self.start + 1 : self.current - 1]
    #     )

    def __string(self) -> None:
        """
        Produce a string token.
        """
        # Use of self.__is_at_end() needed to avoid IndexError.
        while self.__peek() != '"' and not self.__is_at_end():
            if self.__peek() == "\n":
                self.line += 1
            self.__advance()

        if self.__is_at_end():
            from .lox import Lox

            Lox.error(self.line, "Unterminated string.")
            return

        # Consume the closing ".
        self.__advance()

        # Trim the surrounding quotes.
        string: str = self.source[self.start + 1 : self.current - 1]
        self.__add_token(TokenType.STRING, string)

    def __number(self) -> None:
        """
        Produce a number token.
        """
        while self.__is_digit(self.__peek()):
            self.__advance()

        if self.__peek() == "." and self.__is_digit(self.__peek_next()):
            self.__advance()

            while self.__is_digit(self.__peek()):
                self.__advance()

        self.__add_token(
            TokenType.NUMBER, float(self.source[self.start : self.current])
        )

    def __identifier(self) -> None:
        """
        Produce an identifier token.

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
            self.__add_token(TokenType.IDENTIFIER)

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
    def __block_comments(self) -> None:
        """
        Check for block comments.
        """
        # Track open block comments.
        open_block_comments: int = 1

        # Loop until:
        # - No more open block comments
        # - Fewer than two characters to scan
        while open_block_comments > 0 and self.current + 1 < len(self.source):
            two_chars_ahead = self.__peek() + self.__peek_next()

            # Check for new depth.
            if two_chars_ahead == "/*":
                self.__advance()  # Consume /.
                self.__advance()  # Consume *.
                open_block_comments += 1

            # Check for closing */.
            elif two_chars_ahead == "*/":
                self.__advance()  # Consume *.
                self.__advance()  # Consume /.
                open_block_comments -= 1

            # Advance by one character only if no /* or */ registered.
            else:
                # NOTE: Use of self.__peek() is more defensive than self.source[self.current].
                if self.__peek() == "\n":
                    self.line += 1  # Track line number.

                self.__advance()

        # For inspection purposes.
        print(f"Open block comments remaining: {open_block_comments}")
        print("Block comment:")
        print(self.source[self.start : self.current] + "\n")

        if open_block_comments != 0:
            from .lox import Lox

            Lox.error(self.line, "Unterminated block comment.")

    def __is_at_end(self) -> bool:
        """
        Check if current points to the end of source. Useful for preventing
        IndexError.
        """
        return self.current >= len(self.source)

    def __is_alpha_numeric(self, char: str) -> bool:
        """
        Check if char is alphanumeric.
        """
        return self.__is_alpha(char) or self.__is_digit(char)

    def __is_alpha(self, char: str) -> bool:
        """
        Check if char is alphabetical or an underscore.
        """
        import string

        return char in string.ascii_letters + "_"

    def __is_digit(self, char: str) -> bool:
        """
        Check if char is a digit.
        """
        # Iter 1:
        # return char in map(str, range(0, 10))

        # Iter 2:
        # Slightly faster than map/range.
        return "0" <= char <= "9"
