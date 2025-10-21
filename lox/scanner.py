from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, ClassVar

from .token import Token
from .token_type import TokenType

KEYWORDS = [
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
    TokenType.BREAK,
]


@dataclass()
class Scanner:
    _source: str
    _error_callback: Callable[[str, int], None]

    _keywords: ClassVar[MappingProxyType[str, TokenType]] = MappingProxyType(
        {keyword.name.lower(): keyword for keyword in KEYWORDS}
    )
    _tokens: list[Token] = field(default_factory=list)
    _start: int = 0
    _current: int = 0
    _line: int = 1

    def scan_tokens(self) -> list[Token]:
        """Scan tokens from source."""
        # For inspection purposes.
        # print(f"Source length: {len(self._source)}")
        # print("Source:")
        # print(repr(self._source) + "\n")

        while not self.__is_at_end():
            self._start = self._current
            self.__scan_token()

        self._tokens += [Token(TokenType.EOF, "", None, self._line)]
        return self._tokens

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
            case ":":
                self.__add_token(TokenType.COLON)
            case ";":
                self.__add_token(TokenType.SEMICOLON)
            case "*":
                self.__add_token(TokenType.STAR)
            case "%":
                self.__add_token(TokenType.MODULO)
            case "?":
                self.__add_token(TokenType.QUESTION)
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
                self._line += 1
            case '"':
                self.__string()
            case _:
                if self.__is_digit(char):
                    self.__number()
                elif self.__is_alpha(char):
                    self.__identifier()
                else:
                    self._error_callback("Unexpected character.", self._line)

    def __add_token(self, type: TokenType, literal: Any = None) -> None:
        """
        Add a token to self._tokens.
        """
        # NOTE: self._current will be incremented to the right index because of
        # self.advance().
        text: str = self._source[self._start : self._current]
        self._tokens += [
            Token(type=type, lexeme=text, literal=literal, line=self._line)
        ]

    def __advance(self) -> str:
        """
        Advance current.
        Return current scanned character in source.
        """
        self._current += 1
        return self._source[self._current - 1]

    def __match(self, expected: str) -> bool:
        """
        Check if expected matches the current character being scanned.
        Advance current if True.
        """
        if self.__is_at_end():
            return False

        if self._source[self._current] != expected:
            return False

        self._current += 1
        return True

    def __peek(self) -> str:
        """
        Look ahead by one character in source.
        """
        if self.__is_at_end():
            return "\0"

        return self._source[self._current]

    def __peek_next(self) -> str:
        """
        Look ahead by two characters in source.
        """
        if self._current + 1 >= len(self._source):
            return "\0"

        return self._source[self._current + 1]

    # Iter 1 (own version).
    # Less explicit about advancing to consume second quote.
    # def __string(self):
    #     while not self.__match('"') and not self.__is_at_end():
    #         if self.__peek() == "\n":
    #             self._line += 1
    #         self.__advance()
    #
    #     if self.__is_at_end():
    #         self._error_callback(message="Unterminated string.", line=self._line)
    #         return
    #
    #     self.__add_token(
    #         TokenType.STRING, self._source[self._start + 1 : self._current - 1]
    #     )

    def __string(self) -> None:
        """
        Produce a string token.
        """
        # Use of self.__is_at_end() needed to avoid IndexError.
        while self.__peek() != '"' and not self.__is_at_end():
            if self.__peek() == "\n":
                self._line += 1
            self.__advance()

        if self.__is_at_end():
            self._error_callback("Unterminated string.", self._line)
            return

        # Consume the closing ".
        self.__advance()

        # Trim the surrounding quotes.
        string: str = self._source[self._start + 1 : self._current - 1]
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
            TokenType.NUMBER, float(self._source[self._start : self._current])
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

        identifier = self._source[self._start : self._current]
        keyword = self._keywords.get(identifier)

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
    #         self._error_callback(message="Unterminated block comment.", line=self._line)
    #         print(
    #             "Unterminated block comment: " + self._source[self._start : self._current]
    #         )
    #
    # def __is_two_chars_before_end(self) -> bool:
    #     return self._current + 1 == len(self._source)
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
        while open_block_comments > 0 and self._current + 1 < len(self._source):
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
                # NOTE: Use of self.__peek() is more defensive than self._source[self._current].
                if self.__peek() == "\n":
                    self._line += 1  # Track line number.

                self.__advance()

        # For inspection purposes.
        # print(f"Open block comments remaining: {open_block_comments}")
        # print("Block comment:")
        # print(self._source[self._start : self._current] + "\n")

        if open_block_comments != 0:
            self._error_callback("Unterminated block comment.", self._line)

    def __is_at_end(self) -> bool:
        """
        Check if current points to the end of source. Useful for preventing
        IndexError.
        """
        return self._current >= len(self._source)

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
        """Check if char is a digit."""
        # Iter 1:
        # return char in map(str, range(0, 10))

        # Iter 2:
        # Slightly faster than map/range.
        return "0" <= char <= "9"
