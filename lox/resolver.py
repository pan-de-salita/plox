from dataclasses import dataclass, field
from functools import singledispatchmethod

from . import expr, stmt
from .interpreter import Interpreter
from .token import Token


@dataclass
class Resolver(expr.Visitor, stmt.Visitor):
    __interpreter: Interpreter
    __scopes: list[dict[str, bool]] = field(default_factory=list)

    def visit_block_stmt(self, block: stmt.Block) -> None:
        self.__begin_scope()
        self.resolve(block.statements)
        self.__end_scope()

    def visit_var_stmt(self, var_: stmt.Var) -> None:
        self.__declare(var_.name)
        if var_.initializer:
            self.__resolve(var_.initializer)
        self.__define(var_.name)

    def resolve(self, statements: list[stmt.Stmt]) -> None:
        for statement in statements:
            self.__resolve(statement)

    @singledispatchmethod
    def __resolve(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    @__resolve.register(expr.Expr)
    def _(self, expression: expr.Expr) -> None:
        expression.accept(self)

    def __begin_scope(self) -> None:
        self.__scopes.append({})

    def __end_scope(self) -> None:
        self.__scopes.pop()

    def __declare(self, name: Token) -> None:
        if not self.__scopes:
            return

        scope: dict[str, bool] = self.__scopes[-1]
        scope[name.lexeme] = False

    def __define(self, name: Token) -> None:
        if not self.__scopes:
            return

        scope: dict[str, bool] = self.__scopes[-1]
        scope[name.lexeme] = True
