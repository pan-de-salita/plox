# Generated from GenerateAst class (2025-07-28 22:40:54.624208).

from abc import ABC
from dataclasses import dataclass

from lox.token import Token


@dataclass(frozen=True)
class Expr(ABC):
    pass


@dataclass(frozen=True)
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass(frozen=True)
class Grouping(Expr):
    expression: Expr


@dataclass(frozen=True)
class Literal(Expr):
    value: object


@dataclass(frozen=True)
class Unary(Expr):
    operator: Token
    right: Expr
