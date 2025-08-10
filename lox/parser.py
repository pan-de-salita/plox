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

    _tokens: list[Token]
    _current: int = 0

    def expression(self) -> expr.Expr:
        return self.__equality()

    def __equality(self) -> expr.Expr:
        expression: expr.Expr = self.__comparison()
        while self.__match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator: Token = self.__previous()
            right: expr.Expr = self.__comparison()
            expression = expr.Binary(left=expression, operator=operator, right=right)

        return expression

    def __comparison(self) -> expr.Expr:
        expression: expr.Expr = self.__term()
        while self.__match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator: Token = self.__previous()
            right: expr.Expr = self.__term()
            expression = expr.Binary(left=expression, operator=operator, right=right)

        return expression

    def __term(self) -> expr.Expr:
        expression: expr.Expr = self.__factor()
        while self.__match(
            TokenType.MINUS,
            TokenType.PLUS,
        ):
            operator: Token = self.__previous()
            right: expr.Expr = self.__factor()
            expression = expr.Binary(left=expression, operator=operator, right=right)

        return expression

    def __factor(self) -> expr.Expr:
        expression: expr.Expr = self.__unary()
        while self.__match(
            TokenType.STAR,
            TokenType.SLASH,
        ):
            operator: Token = self.__previous()
            right: expr.Expr = self.__unary()
            expression = expr.Binary(left=expression, operator=operator, right=right)

        return expression

    def __unary(self) -> expr.Expr:
        if not self.__match(TokenType.MINUS, TokenType.BANG):
            return self.__primary()

        operator: Token = self.__previous()
        right: expr.Expr = self.__unary()

        return expr.Unary(operator=operator, right=right)

    def __primary(self) -> expr.Expr:
        token: Token = self.__advance()
        expression: expr.Expr = self.__literal(token.literal)

        match token.type:
            # case TokenType.NUMBER | TokenType.STRING:
            #     return self.__literal(token.literal)

            # TODO:
            # Handle true, false, and nil

            case TokenType.LEFT_PAREN:
                expression = self.__parenthesize()

        return expression

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

    def __literal(self, literal: object) -> expr.Literal:
        return expr.Literal(value=literal)

    def __parenthesize(self) -> expr.Expr:
        expression: expr.Expr = expr.Grouping(expression=self.expression())

        if self.__peek().type != TokenType.RIGHT_PAREN:
            raise RuntimeError("Expected ')' after expression")

        self.__advance()  # Consume the closing parenthesis

        return expression


if __name__ == "__main__":
    parser = Parser(
        [
            Token(type=TokenType.LEFT_PAREN, lexeme="(", literal=None, line=1),
            Token(type=TokenType.NUMBER, lexeme="1", literal=float(1), line=1),
            Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
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
