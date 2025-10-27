from collections import deque
from dataclasses import dataclass, field
from functools import singledispatchmethod

from . import expr, stmt
from .interpreter import Interpreter


@dataclass
class Resolver(expr.Visitor, stmt.Visitor):
    __interpreter: Interpreter
    __scopes: deque[dict[str, bool]] = field(default_factory=lambda: deque())

    def visit_block_stmt(self, block: stmt.Block) -> None:
        self.__begin_scope()
        self.resolve(block.statements)
        self.__end_scope()

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
