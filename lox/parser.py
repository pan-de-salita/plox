from dataclasses import dataclass

from . import expr
from .token import Token
from .token_type import TokenType


@dataclass()
class Parser:
    """Using recursive descent parsing, parses a list of tokens and returns a
    corresponding syntax tree.

    Each method for parsing a grammar rule produces a syntax tree for that
    rule and returns it to the caller. When the body of the rule contains a
    nonterminal, we call that other rule's method."""

    # NOTE: Commented out code is for testing purposes.

    _tokens: list[Token]
    _current: int = 0

    def __expression(self) -> expr.Expr:
        return self.__equality()

    # For testing:
    # def equality(self) -> expr.Expr:
    def __equality(self) -> expr.Expr:
        # expression: expr.Expr = expr.Literal(value=self.__advance().lexeme)
        expression: expr.Expr = self.__comparison()

        while self.__match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator: Token = self.__previous()
            # right: expr.Expr = expr.Literal(value=self.__advance().lexeme)
            right: expr.Expr = self.__comparison()
            expression = expr.Binary(left=expression, operator=operator, right=right)

        return expression

    def __comparison(self):
        return

    def __match(self, *token_types: TokenType) -> bool:
        """Check if the current token has any of the given types. If so,
        consume the token and return True. Otherwise, ignore current token and
        return False."""
        for type in token_types:
            if self.__check(type):
                self.__advance()
                return True

        return False

    def __check(self, type: TokenType) -> bool:
        """Check if current token matches given type."""
        if self.__is_at_end():
            return False

        return self.__peek().type == type

    def __advance(self) -> Token:
        """Consume and return the current token."""
        if not self.__is_at_end():
            self._current += 1

        return self.__previous()

    def __is_at_end(self) -> bool:
        """Check if no more tokens to parse."""
        return self.__peek().type == TokenType.EOF

    def __peek(self) -> Token:
        """Return current yet-to-be-consumed token."""
        return self._tokens[self._current]

    def __previous(self) -> Token:
        """Return most recently consumed token."""
        return self._tokens[self._current - 1]


if __name__ == "__main__":
    parser = Parser(
        [
            Token(type=TokenType.NUMBER, lexeme="1", literal=float(1), line=1),
            Token(type=TokenType.EQUAL_EQUAL, lexeme="==", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="1", literal=float(1), line=1),
            Token(type=TokenType.EQUAL_EQUAL, lexeme="==", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="1", literal=float(1), line=1),
            Token(type=TokenType.EOF, lexeme="", literal=float(1), line=1),
        ]
    )

    # print(parser.equality())
