from dataclasses import dataclass
from typing import Callable

# Opportunity to use __init__.py?
from . import expr, stmt
from .parse_error import ParseError
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
    _error_callback: Callable[[str, Token], None]

    _current: int = 0

    def parse(self) -> list[stmt.Stmt]:
        """Parse a series of statements, as many as can be found until the end
        of the input."""
        statments: list[stmt.Stmt] = []
        while not self.__is_at_end():
            statments.append(self.__statement())

        return statments

    def __statement(self) -> stmt.Stmt:
        if self.__match(TokenType.PRINT):
            return self.__print_statement()

        return self.__expression_statment()

    def __print_statement(self) -> stmt.Stmt:
        value: expr.Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Print(expression=value)

    def __expression_statment(self) -> stmt.Stmt:
        value: expr.Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Expression(expression=value)

    def __expression(self) -> expr.Expr:
        """Parse expression rule: expression -> comma_expresiion

        This is the top-level rule for expressions. Currently just delegates
        to comma_expression since that's the lowest precedence binary operator.
        """
        return self.__comma_expression()

    def __comma_expression(self) -> expr.Expr:
        """Parse expression rule: comma_expression -> ternary ( "," ternary )

        Handles comma operators (,).
        These have lower precedence than ternary operators.
        Left-associative: a, b, c is parsed as ((a, b), c)
        """
        return self.__binary_left_associative(
            nonterminal=self.__ternary, token_types=[TokenType.COMMA]
        )

    def __ternary(self) -> expr.Expr:
        """Parse expression rule: ternary -> ( equality "?" equality ":" ternary ) | equality

        Handles ternary expressions.
        These have lower precedence than equality expressions.
        Right-associative: true ? 1 : 2 ? 3 : 4 is parsed as (? true (: 1 (? 2 (: 3 4))))
        """
        expression: expr.Expr = self.__equality()

        if self.__match(TokenType.QUESTION):
            # Question mark is consumed via call to __match().
            condition: expr.Expr = expression
            consequent: expr.Expr = self.__equality()

            # Check for colon.
            self.__consume(
                TokenType.COLON,
                "Expect binary branch after '?' for a ternary expression.",
            )

            alternative: expr.Expr = self.__ternary()
            expression = expr.Ternary(
                condition=condition, consequent=consequent, alternative=alternative
            )

        return expression

    def __equality(self) -> expr.Expr:
        """Parse equality rule: equality -> comparison ( ( "!=" | "==" ) comparison )*

        Handles equality and inequality operators (== and !=).
        These have lower precedence than comparison operators.
        Left-associative: a == b == c is parsed as ((a == b) == c)
        """
        return self.__binary_left_associative(
            nonterminal=self.__comparison,
            token_types=[TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL],
        )

    def __comparison(self) -> expr.Expr:
        """Parse comparison rule: comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )*

        Handles relational operators (>, >=, <, <=).
        These have higher precedence than equality but lower than arithmetic.
        Left-associative: a < b < c is parsed as ((a < b) < c)
        """
        return self.__binary_left_associative(
            nonterminal=self.__term,
            token_types=[
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
            ],
        )

    def __term(self) -> expr.Expr:
        """Parse term rule: term -> factor ( ( "-" | "+" ) factor )*

        Handles addition and subtraction operators.
        These have higher precedence than comparison but lower than multiplication/division.
        Left-associative: a + b - c is parsed as ((a + b) - c)
        """
        return self.__binary_left_associative(
            nonterminal=self.__factor,
            token_types=[
                TokenType.MINUS,
                TokenType.PLUS,
            ],
        )

    def __factor(self) -> expr.Expr:
        """Parse factor rule: factor -> unary ( ( "/" | "*" ) unary )*

        Handles multiplication and division operators.
        These have higher precedence than addition/subtraction but lower than unary.
        Left-associative: a * b / c is parsed as ((a * b) / c)

        Note: The commented code shows why left-recursion doesn't work in
        recursive descent - it would cause infinite recursion.
        """

        # expression: expr.Expr = self.__factor() # Triggers infinite recursion.
        #
        # # This never gets executed:
        # while self.__match(TokenType.STAR, TokenType.SLASH):
        #     operator: Token = self.__previous()
        #     right: expr.Expr = self.__unary()
        #     expression = expr.Binary(left=expression, operator=operator, right=right)
        #
        # return expression

        return self.__binary_left_associative(
            nonterminal=self.__unary,
            token_types=[
                TokenType.SLASH,
                TokenType.STAR,
            ],
        )

    def __unary(self) -> expr.Expr:
        """Parse unary rule: unary -> ( "!" | "-" ) unary | primary

        Handles unary operators (! and -).
        These have higher precedence than all binary operators.
        Right-associative: --a is parsed as -(-(a))

        If no unary operator is found, delegates to primary.
        """
        invalid_binary_operators: list[TokenType] = [
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.PLUS,
            TokenType.SLASH,
            TokenType.STAR,
            TokenType.BANG_EQUAL,
            TokenType.EQUAL,
            TokenType.EQUAL_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            # TokenType.AND,
            # TokenType.OR,
        ]

        if self.__match(*invalid_binary_operators, TokenType.MINUS, TokenType.BANG):
            operator: Token = self.__previous()

            if operator.type in invalid_binary_operators:
                self.__error(
                    operator,
                    f"Expressions beginning with '{operator.lexeme}' not allowed.",
                )
                return self.__primary()

            right: expr.Expr = self.__unary()

            return expr.Unary(operator=operator, right=right)
        else:
            return self.__primary()

    def __primary(self) -> expr.Expr:
        """Parse primary rule: primary -> "true" | "false" | "nil" | NUMBER | STRING | "(" expression ")"

        Handles the highest precedence expressions:
        - Literal values: true, false, nil, numbers, strings
        - Grouped expressions: (expression)

        This is the base case of the recursive descent - no further recursion
        except for grouped expressions which restart from the top.
        """
        if self.__match(TokenType.FALSE):
            return expr.Literal(value=False)
        elif self.__match(TokenType.TRUE):
            return expr.Literal(value=True)
        elif self.__match(TokenType.NIL):
            return expr.Literal(value=None)
        elif self.__match(TokenType.NUMBER, TokenType.STRING):
            return expr.Literal(value=self.__previous().literal)
        elif self.__match(TokenType.LEFT_PAREN):
            expression: expr.Expr = self.__expression()
            self.__consume(
                token_type=TokenType.RIGHT_PAREN, message="Expect ')' after expression."
            )
            return expr.Grouping(expression=expression)
        else:
            raise self.__error(self.__peek(), "Expect expression.")

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

    def __consume(self, token_type: TokenType, message: str) -> Token:
        """Consume current token if current token matches a given type."""
        if self.__check(token_type):
            return self.__advance()

        raise self.__error(self.__peek(), message)

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

    def __error(self, token: Token, message: str) -> ParseError:
        """Handle parse errors."""
        self._error_callback(message, token)

        # Since parse errors vary in severity, returning the error instead of
        # raising it to let the calling method inside the parser decide whether
        # to unwind or not.

        return ParseError()

    def __synchronize(self) -> None:
        """Discard tokens until a statement boundary is found. For discarding
        unwanted tokens and resyncing the Parser's state after a ParseError."""
        self.__advance()

        while not self.__is_at_end():
            if self.__previous().type == TokenType.SEMICOLON:
                return None

            match self.__peek().type:
                case (
                    TokenType.CLASS
                    | TokenType.FUN
                    | TokenType.VAR
                    | TokenType.FOR
                    | TokenType.IF
                    | TokenType.WHILE
                    | TokenType.PRINT
                    | TokenType.RETURN
                ):
                    return None

            self.__advance()
