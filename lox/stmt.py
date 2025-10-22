# Generated from GenerateAst class (2025-10-22 23:12:16.924274).

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from lox.expr import Expr
from lox.token import Token

R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    @abstractmethod
    def visit_var_stmt(self, var_: Var) -> R:
        pass

    @abstractmethod
    def visit_expression_stmt(self, expression: Expression) -> R:
        pass

    @abstractmethod
    def visit_function_stmt(self, function: Function) -> R:
        pass

    @abstractmethod
    def visit_if_stmt(self, if_: If) -> R:
        pass

    @abstractmethod
    def visit_while_stmt(self, while_: While) -> R:
        pass

    @abstractmethod
    def visit_break_stmt(self, break_: Break) -> R:
        pass

    @abstractmethod
    def visit_print_stmt(self, print_: Print) -> R:
        pass

    @abstractmethod
    def visit_return_stmt(self, return_: Return) -> R:
        pass

    @abstractmethod
    def visit_block_stmt(self, block: Block) -> R:
        pass


@dataclass(frozen=True)
class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        pass


@dataclass(frozen=True)
class Var(Stmt):
    name: Token
    expression: Expr | None
    is_initialized: bool

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_var_stmt(self)


@dataclass(frozen=True)
class Expression(Stmt):
    expression: Expr

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_expression_stmt(self)


@dataclass(frozen=True)
class Function(Stmt):
    name: Token
    params: list[Token]
    body: list[Stmt]

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_function_stmt(self)


@dataclass(frozen=True)
class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_if_stmt(self)


@dataclass(frozen=True)
class While(Stmt):
    condition: Expr
    body: Stmt

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_while_stmt(self)


@dataclass(frozen=True)
class Break(Stmt):
    token: Token

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_break_stmt(self)


@dataclass(frozen=True)
class Print(Stmt):
    expression: Expr

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_print_stmt(self)


@dataclass(frozen=True)
class Return(Stmt):
    keyword: Token
    value: Expr | None

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_return_stmt(self)


@dataclass(frozen=True)
class Block(Stmt):
    statements: list[Stmt]

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_block_stmt(self)
