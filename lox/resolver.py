from dataclasses import dataclass, field
from functools import singledispatchmethod
from typing import Callable

from . import expr, stmt
from .interpreter import Interpreter
from .token import Token


@dataclass
class Resolver(expr.Visitor, stmt.Visitor):
    _interpreter: Interpreter
    _error_callback: Callable[[str, Token], None]
    _scopes: list[dict[str, bool]] = field(default_factory=list)

    def visit_block_stmt(self, block: stmt.Block) -> None:
        self.__begin_scope()
        self.resolve(block.statements)
        self.__end_scope()

    def visit_function_stmt(self, function: stmt.Function) -> None:
        # Define the function name eagerly, before resolving its body. This
        # lets a function recursively refer to itself inside its own body.
        self.__declare(function.name)
        self.__define(function.name)

        self.__resolve_function(function)

    def visit_var_stmt(self, var_: stmt.Var) -> None:
        self.__declare(var_.name)
        if var_.initializer:
            self.__resolve(var_.initializer)
        self.__define(var_.name)

    def visit_assign_expr(self, assign: expr.Assign) -> None:
        # Resolve the expression for the assigned value in case it also contains
        # references to other variables.
        self.__resolve(assign.value)

        # Resolve the variable that's being assigned to.
        self.__resolve_local(assign, assign.name)

    def visit_var_expr(self, variable: expr.Variable) -> None:
        # Disallow access of variable inside its own initializer.
        # If the variable exists in the current scope but its value is false,
        # that means we have declared it but not yet defined it. This we treat
        # as an error.
        if self._scopes and self.__peek_scope().get(variable.name.lexeme) is False:
            self._error_callback(
                "Can't read local variable in its own initializer.", variable.name
            )

        self.__resolve_local(variable, variable.name)

    def resolve(self, statements: list[stmt.Stmt]) -> None:
        for statement in statements:
            self.__resolve(statement)

    @singledispatchmethod
    def __resolve(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    @__resolve.register(expr.Expr)
    def _(self, expression: expr.Expr) -> None:
        expression.accept(self)

    def __resolve_function(self, function: stmt.Function) -> None:
        self.__begin_scope()

        for param in function.params:
            self.__declare(param)
            self.__define(param)

        self.resolve(function.body)

        self.__end_scope()

    def __begin_scope(self) -> None:
        self._scopes.append({})

    def __end_scope(self) -> None:
        self._scopes.pop()

    def __declare(self, name: Token) -> None:
        if not self._scopes:
            return

        scope: dict[str, bool] = self.__peek_scope()
        scope[name.lexeme] = False

    def __define(self, name: Token) -> None:
        if not self._scopes:
            return

        scope: dict[str, bool] = self.__peek_scope()
        scope[name.lexeme] = True

    def __peek_scope(self) -> dict[str, bool]:
        return self._scopes[-1]

    def __resolve_local(self, variable: expr.Expr, variable_name: Token) -> None:
        # We start at the innermost scope and work outwards, looking in each
        # map for a matching name. If we find the variable, we resolve it,
        # passing in the number of scopes between the current innermost scope
        # and the scope where the variable was found (the distance). E.g., if
        # the the variable was found in the current scope, we pass in 0. If it's
        # in the immediately enclosing scope, 1.
        #
        # If we walk through all of the block scopes and never find the variable,
        # we leave it unresolved and assume it's global.
        for i, scope in enumerate(self._scopes):
            if variable_name in scope:
                self._interpreter.resolve(variable, len(self._scopes) - 1 - i)
                break
