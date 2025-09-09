# Generated from GenerateAst class (2025-09-09 21:20:12.012143).

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from lox.expr import Expr

R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    @abstractmethod
    def visit_expression_stmt(self, expression: Expression) -> R:
        pass

    @abstractmethod
    def visit_print_stmt(self, print: Print) -> R:
        pass


@dataclass(frozen=True)
class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        pass


@dataclass(frozen=True)
class Expression(Stmt):
    expression: Expr

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_expression_stmt(self)


@dataclass(frozen=True)
class Print(Stmt):
    expression: Expr

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_print_stmt(self)
