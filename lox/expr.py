# Generated from GenerateAst class (2025-07-30 21:16:57.222633).

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from lox.token import Token

R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    @abstractmethod
    def visit_binary_expr(self, binary: Binary) -> R:
        pass

    @abstractmethod
    def visit_grouping_expr(self, grouping: Grouping) -> R:
        pass

    @abstractmethod
    def visit_literal_expr(self, literal: Literal) -> R:
        pass

    @abstractmethod
    def visit_unary_expr(self, unary: Unary) -> R:
        pass


@dataclass(frozen=True)
class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        pass


@dataclass(frozen=True)
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_binary_expr(self)


@dataclass(frozen=True)
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_grouping_expr(self)


@dataclass(frozen=True)
class Literal(Expr):
    value: object

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_literal_expr(self)


@dataclass(frozen=True)
class Unary(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_unary_expr(self)
