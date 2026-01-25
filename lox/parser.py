from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from . import expr, stmt
from .function_type import FunctionType
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
    _loop_count: int = 0
    _function_count: int = 0

    def parse(self) -> list[stmt.Stmt]:
        """Parse a series of statements, as many as can be found until the end
        of the input, generating a syntax tree."""
        statements: list[stmt.Stmt] = []
        while not self.__is_at_end():
            statement: stmt.Stmt | None = self.__declaration()
            if not statement:
                continue
            statements.append(statement)

        return statements

    def __declaration(self) -> stmt.Stmt | None:
        try:
            if self.__match(TokenType.FUN):
                if self.__check(TokenType.IDENTIFIER):
                    return self.__function(FunctionType.FUNCTION.value)
                else:
                    # Decrement for lambda expressions as expression statements.
                    self._current -= 1

            if self.__match(TokenType.CLASS):
                return self.__class_declaration()

            if self.__match(TokenType.VAR):
                return self.__var_declaration()

            return self.__statement()
        except ParseError:
            self.__synchronize()
            return None

    def __function(self, kind: str) -> stmt.Function:
        self._function_count += 1

        name: Token = self.__consume(TokenType.IDENTIFIER, f"Expect {kind} name.")

        self.__consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        params: list[Token] = []
        if not self.__check(TokenType.RIGHT_PAREN):
            while True:
                if len(params) >= 255:
                    self.__error(self.__peek(), "Can't have more than 255 parameters.")

                params.append(
                    self.__consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )

                if not self.__match(TokenType.COMMA):
                    break
        self.__consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.__consume(TokenType.LEFT_BRACE, "Expr '{' after parameters.")
        body: list[stmt.Stmt] = self.__block_statement()

        self._function_count -= 1

        return stmt.Function(name, params, body)

    def __class_declaration(self) -> stmt.Class:
        name: Token = self.__consume(TokenType.IDENTIFIER, "Expect class name.")
        self.__consume(TokenType.LEFT_BRACE, "Expect left brace.")

        methods: list[stmt.Function] = []
        while not self.__check(TokenType.RIGHT_BRACE) and not self.__is_at_end():
            methods.append(self.__function(FunctionType.METHOD.value))

        self.__consume(TokenType.RIGHT_BRACE, "Expect right brace.")

        return stmt.Class(name, methods)

    def __var_declaration(self) -> stmt.Var:
        name: Token = self.__consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer: expr.Expr | None = None
        is_initialized: bool = False
        if self.__match(TokenType.EQUAL):
            initializer = self.__expression()
            is_initialized = True

        self.__consume(
            TokenType.SEMICOLON,
            "Expect ';' after variable declaration.",
        )

        return stmt.Var(name, is_initialized, initializer)

    def __statement(self) -> stmt.Stmt:
        if self.__match(TokenType.WHILE):
            return self.__while_statement()

        if self.__match(TokenType.FOR):
            return self.__for_statement()

        if self.__match(TokenType.BREAK):
            return self.__break_statement()

        if self.__match(TokenType.IF):
            return self.__if_statement()

        if self.__match(TokenType.LEFT_BRACE):
            return stmt.Block(self.__block_statement())

        if self.__match(TokenType.PRINT):
            return self.__print_statement()

        if self.__match(TokenType.RETURN):
            return self.__return_statement()

        return self.__expression_statement()

    def __while_statement(self) -> stmt.While:
        self._loop_count += 1

        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition: expr.Expr = self.__expression()
        self.__consume(
            TokenType.RIGHT_PAREN,
            "Expect ')' after while condition.",
        )
        body: stmt.Stmt = self.__statement()

        self._loop_count -= 1

        return stmt.While(condition=condition, body=body)

    def __for_statement(self) -> stmt.Stmt:
        self._loop_count += 1

        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        initializer: stmt.Var | stmt.Expression | None
        if self.__match(TokenType.SEMICOLON):
            initializer = None
        elif self.__match(TokenType.VAR):
            initializer = self.__var_declaration()
        else:
            initializer = self.__expression_statement()

        condition: expr.Expr = expr.Literal(value=True)
        if not self.__check(TokenType.SEMICOLON):
            condition = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after for-loop condition.")

        increment: stmt.Expr | None = None
        if not self.__check(TokenType.RIGHT_PAREN):
            increment = self.__expression()
        self.__consume(TokenType.RIGHT_PAREN, "Expect ')' after for-loop clauses.")

        body: stmt.Stmt = self.__statement()
        # if increment:
        #     if isinstance(body, stmt.Block):
        #         body.statements.append(stmt.Expression(increment))
        #     else:
        #         body = stmt.Block(statements=[body, stmt.Expression(increment)])
        # else:
        #     if not isinstance(body, stmt.Block):
        #         body = stmt.Block(statements=[body])
        if increment:
            body = stmt.Block(statements=[body, stmt.Expression(increment)])

        self._loop_count -= 1

        if isinstance(initializer, stmt.Stmt):
            return stmt.Block(
                statements=[initializer, stmt.While(condition=condition, body=body)]
            )
        else:
            return stmt.Block(statements=[stmt.While(condition=condition, body=body)])

    def __break_statement(self) -> stmt.Break:
        token: Token = self.__previous()

        if not self._loop_count:
            raise self.__error(token, "'break' outside loop.")

        self.__consume(
            TokenType.SEMICOLON,
            "Expect ';' after break statement.",
        )

        return stmt.Break(token)

    def __if_statement(self) -> stmt.If:
        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition: expr.Expr = self.__expression()
        self.__consume(
            TokenType.RIGHT_PAREN,
            "Expect ')' after if condition.",
        )

        # The else branch is bound to the nearest if that precedes it. This is
        # our solution to the dangling else problem.
        then_branch: stmt.Stmt = self.__statement()
        else_branch: stmt.Stmt | None = None
        if self.__match(TokenType.ELSE):
            else_branch = self.__statement()

        return stmt.If(condition, then_branch, else_branch)

    def __block_statement(self) -> list[stmt.Stmt]:
        statements: list[stmt.Stmt] = []
        while not self.__check(TokenType.RIGHT_BRACE) and not self.__is_at_end():
            statement: stmt.Stmt | None = self.__declaration()

            if not statement:
                continue

            statements.append(statement)

        self.__consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")

        return statements

    def __print_statement(self) -> stmt.Print:
        value: expr.Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Print(value)

    def __return_statement(self) -> stmt.Return:
        keyword: Token = self.__previous()
        value: expr.Expr | None = None

        if not self.__check(TokenType.SEMICOLON):
            value = self.__expression()

        self.__consume(TokenType.SEMICOLON, "Expect ';' after return value.")

        return stmt.Return(keyword=keyword, value=value)

    def __expression_statement(self) -> stmt.Expression:
        value: expr.Expr = self.__expression()
        self.__consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Expression(value)

    def __expression(self) -> expr.Expr:
        """Parse expression rule: expression -> comma

        This is the top-level rule for expressions. Currently just delegates
        to comma.
        """
        return self.__comma()

    def __comma(self) -> expr.Expr:
        """Parse expression rule: comma_expression -> ternary ( "," ternary )

        Handles comma operators (,).
        These have lower precedence than assignment.
        Left-associative: a, b, c is parsed as ((a, b), c)
        """

        # TODO: Fix erroneous parsing of callables.
        # return self.__binary_left_associative(self.__assignment, [TokenType.COMMA])

        return self.__binary_left_associative(self.__assignment, [])

    def __assignment(self) -> expr.Expr:
        """Parse expression rule: assignment -> IDENTIFIER '=' assignment
        | logic_or"""
        expression: expr.Expr = (
            self.__logic_or()
        )  # Or whatever is of higher precedence.

        if self.__match(TokenType.EQUAL):
            equals: Token = self.__previous()
            value: expr.Expr = self.__assignment()

            # Convert r-value expression node into an l-value representation.
            # Important because if there was no match for TokenType.EQUAL -- i.e.
            # the parser isn't handling an assignment expression -- the r-value
            # expression could be validly evaluated. Example:
            #
            # NewPoint(x + 2, 0).y = 3      # Sets the field
            # NewPoint(x + 2, 0).y          # Gets the field
            #
            # NOTE: Right now, the only valid target is a simple variable
            # expression, but we'll add fields later. The end result of this
            # trick is an assignment expression tree node that knows what it
            # is assigning to and has an expression subtree for the value
            # being assigned.
            if isinstance(expression, expr.Variable):
                return expr.Assign(expression.name, value)

            elif isinstance(expression, expr.Get):
                return expr.Set(expression.object, expression.name, value)

            # We report an error if the left-hand side isn't a valid assignment
            # target, but we don't throw it because the parser isn't in a
            # confused state where we need to go into panic mode and synchronize.
            self.__error(equals, "Invalid assignment target.")

        return expression

    def __logic_or(self) -> expr.Expr:
        return self.__logical_left_associative(
            nonterminal=self.__logic_and, token_types=[TokenType.OR]
        )

    def __logic_and(self) -> expr.Expr:
        return self.__logical_left_associative(
            nonterminal=self.__ternary, token_types=[TokenType.AND]
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
            expression = expr.Ternary(condition, consequent, alternative)

        return expression

    def __equality(self) -> expr.Expr:
        """Parse equality rule: equality -> comparison ( ( "!=" | "==" ) comparison )*

        Handles equality and inequality operators (== and !=).
        These have lower precedence than comparison operators.
        Left-associative: a == b == c is parsed as ((a == b) == c)
        """
        return self.__binary_left_associative(
            self.__comparison,
            [TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL],
        )

    def __comparison(self) -> expr.Expr:
        """Parse comparison rule: comparison -> term ( ( ">" | ">=" | "<" | "<=" ) term )*

        Handles relational operators (>, >=, <, <=).
        These have higher precedence than equality but lower than arithmetic.
        Left-associative: a < b < c is parsed as ((a < b) < c)
        """
        return self.__binary_left_associative(
            self.__term,
            [
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
            self.__factor,
            [
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
            self.__unary,
            [
                TokenType.SLASH,
                TokenType.STAR,
                TokenType.MODULO,
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
                return self.__call()

            right: expr.Expr = self.__unary()

            return expr.Unary(operator, right)
        else:
            return self.__call()

    def __call(self) -> expr.Expr:
        # Own non-working attempt. Does not work because it doesn't account for
        # successive calls, e.g. func(x)(y):
        #
        # callee: expr.Expr = self.__primary()
        #
        # if self.__match(TokenType.LEFT_PAREN):
        #     paren: Token = self.__previous()
        #
        #     arguments: list[expr.Expr] = []
        #     while not self.__match(TokenType.RIGHT_PAREN):
        #         arguments.append(self.__expression())
        #
        #     return expr.Call(callee, paren, arguments)
        #
        # return callee

        # Rewrite:
        # expression: expr.Expr = self.__primary()
        #
        # while self.__match(TokenType.LEFT_PAREN):
        #     arguments: list[expr.Expr] = []
        #     while not self.__check(TokenType.RIGHT_PAREN):
        #         arguments.append(self.__expression())
        #
        #         if not self.__match(TokenType.COMMA):
        #             break
        #
        #     paren: Token = self.__consume(
        #         TokenType.COMMA, "Expect ')' after arguments."
        #     )
        #     expression = expr.Call(expression, paren, arguments)
        #
        # return expression

        # Keeping current structure to facilitate implementation of properties
        # on objects.
        expression: expr.Expr = self.__primary()

        while True:
            if self.__match(TokenType.LEFT_PAREN):
                expression = self.__finish_call(expression)
            if self.__match(TokenType.DOT):
                name: Token = self.__consume(
                    TokenType.IDENTIFIER, "Expected property name after '.'."
                )
                expression = expr.Get(expression, name)
            else:
                break

        return expression

    def __finish_call(self, callee: expr.Expr) -> expr.Expr:
        arguments: list[expr.Expr] = []
        if not self.__check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self.__error(self.__peek(), "Can't have more than 255 arguments.")

                arguments.append(self.__expression())

                if not self.__match(TokenType.COMMA):
                    break

        paren: Token = self.__consume(
            TokenType.RIGHT_PAREN, "Expect ')' after arguments."
        )

        return expr.Call(callee, paren, arguments)

    def __primary(self) -> expr.Expr:
        """Parse primary rule: primary -> "true" | "false" | "nil" | NUMBER | STRING | "(" expression ")"

        Handles the highest precedence expressions:
        - Literal values: true, false, nil, numbers, strings
        - Grouped expressions: (expression)

        This is the base case of the recursive descent - no further recursion
        except for grouped expressions which restart from the top.
        """
        if self.__match(TokenType.FALSE):
            return expr.Literal(False)
        elif self.__match(TokenType.TRUE):
            return expr.Literal(True)
        elif self.__match(TokenType.NIL):
            return expr.Literal(None)
        elif self.__match(TokenType.NUMBER, TokenType.STRING):
            return expr.Literal(self.__previous().literal)
        elif self.__match(TokenType.IDENTIFIER):
            return expr.Variable(self.__previous())
        elif self.__match(TokenType.THIS):
            return expr.This(self.__previous())
        elif self.__match(TokenType.FUN):
            return self.__lambda()
        elif self.__match(TokenType.LEFT_PAREN):
            expression: expr.Expr = self.__expression()
            self.__consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return expr.Grouping(expression)
        else:
            self.__peek()
            raise self.__error(self.__peek(), "Expect expression.")

    def __lambda(self) -> expr.Lambda:
        self.__consume(TokenType.LEFT_PAREN, "Expect '(' after lambda.")

        params: list[Token] = []
        if self.__peek().type != TokenType.RIGHT_PAREN:
            while True:
                if len(params) >= 255:
                    self.__error(self.__peek(), "Can't have more than 255 arguments.")

                params.append(self.__advance())

                if not self.__match(TokenType.COMMA):
                    break
        self.__consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.__consume(TokenType.LEFT_BRACE, "Expect '{' after parameters.")
        body: list[stmt.Stmt] = self.__block_statement()

        return expr.Lambda(params=params, body=body)

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
            expression = expr.Binary(expression, operator, right)

        return expression

    def __logical_left_associative(
        self, nonterminal: Callable, token_types: list[TokenType]
    ) -> expr.Expr:
        """Return a left-associative logical syntax tree."""
        expression: expr.Expr = nonterminal()

        while self.__match(*token_types):
            operator: Token = self.__previous()
            right: expr.Expr = nonterminal()
            expression = expr.Logical(expression, operator, right)

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

    def __check(self, type_: TokenType) -> bool:
        """Check if current token matches given type."""
        if self.__is_at_end():
            return False

        return self.__peek().type == type_

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
        while not self.__is_at_end():
            self.__advance()

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
