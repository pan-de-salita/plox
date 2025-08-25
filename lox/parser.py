from dataclasses import dataclass
from typing import Callable

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

    _tokens: list[Token]
    _current: int = 0

    def expression(self) -> expr.Expr:
        return self.__equality()

    def __equality(self) -> expr.Expr:
        return self.__binary_left_associative(
            nonterminal=self.__comparison,
            types=[TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL],
        )

    def __comparison(self) -> expr.Expr:
        return self.__binary_left_associative(
            nonterminal=self.__term,
            types=[
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
            ],
        )

    def __term(self) -> expr.Expr:
        return self.__binary_left_associative(
            nonterminal=self.__factor,
            types=[
                TokenType.MINUS,
                TokenType.PLUS,
            ],
        )

    def __factor(self) -> expr.Expr:
        # NOTE: Infinite recursion if we use a left-recursive approach.
        #
        # expression: expr.Expr = self.__factor()
        #
        # while self.__match(TokenType.STAR, TokenType.SLASH):
        #     operator: Token = self.__previous()
        #     right: expr.Expr = self.__unary()
        #     expression = expr.Binary(left=expression, operator=operator, right=right)
        #
        # return expression

        return self.__binary_left_associative(
            nonterminal=self.__unary,
            types=[
                TokenType.SLASH,
                TokenType.STAR,
            ],
        )

    def __unary(self) -> expr.Expr:
        if not self.__match(TokenType.MINUS, TokenType.BANG):
            return self.__primary()

        operator: Token = self.__previous()
        right: expr.Expr = self.__unary()

        return expr.Unary(operator=operator, right=right)

    def __primary(self) -> expr.Expr:
        if self.__match(TokenType.FALSE):
            return expr.Literal(value=False)
        elif self.__match(TokenType.TRUE):
            return expr.Literal(value=True)
        elif self.__match(TokenType.NIL):
            return expr.Literal(value=None)
        elif self.__match(TokenType.NUMBER, TokenType.STRING):
            return expr.Literal(value=self.__previous().literal)
        elif self.__match(TokenType.LEFT_PAREN):
            expression: expr.Expr = self.expression()
            self.__consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expr.Grouping(expression=expression)
        else:
            raise RuntimeError("Expected expression, but none found.")

    def __binary_left_associative(
        self, nonterminal: Callable, token_types: list[TokenType]
    ) -> expr.Expr:
        """Return a left-associative binary syntax tree."""
        expression: expr.Expr = nonterminal()

        # Rolling accumulator for building appropriate Binary expression.
        #
        # The fact that the parser looks ahead at upcoming tokens to decide how
        # to parse puts recursive descent into the category of predictive parsers.
        while self.__match(*token_types):
            operator: Token = self.__previous()
            right: expr.Expr = nonterminal()
            expression = expr.Binary(left=expression, operator=operator, right=right)

        return expression

    def __match(self, *token_types: TokenType) -> bool:
        """Check if the current token is of the given types. If so, consume the
        token and return True. Otherwise, ignore current token and return False."""
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

    def __consume(self, type: TokenType, message: str) -> Token:
        """Consume current token if current token matches a given type."""
        if self.__check(type):
            return self.__advance()

        raise RuntimeError(message)


if __name__ == "__main__":
    parser = Parser(
        [
            Token(type=TokenType.LEFT_PAREN, lexeme="(", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="1", literal=float(1), line=1),
            Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="2", literal=float(2), line=1),
            Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="2", literal=float(2), line=1),
            Token(type=TokenType.RIGHT_PAREN, lexeme=")", literal=None, line=1),
            Token(type=TokenType.EQUAL_EQUAL, lexeme="==", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="1", literal=float(1), line=1),
            Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
            Token(type=TokenType.MINUS, lexeme="-", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="2", literal=float(2), line=1),
            Token(type=TokenType.EOF, lexeme="", literal=float(1), line=1),
        ]
    )

    print(parser.expression())
