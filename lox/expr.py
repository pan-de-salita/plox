# Generated from GenerateAst class (2025-11-28 12:24:38.658727).

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from lox.token import Token

R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    @abstractmethod
    def visit_assign_expr(self, assign: Assign) -> R:
        pass

    @abstractmethod
    def visit_logical_expr(self, logical: Logical) -> R:
        pass

    @abstractmethod
    def visit_ternary_expr(self, ternary: Ternary) -> R:
        pass

    @abstractmethod
    def visit_binary_expr(self, binary: Binary) -> R:
        pass

    @abstractmethod
    def visit_call_expr(self, call: Call) -> R:
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

    @abstractmethod
    def visit_variable_expr(self, variable: Variable) -> R:
        pass

    @abstractmethod
    def visit_lambda_expr(self, lambda_: Lambda) -> R:
        pass

    @abstractmethod
    def visit_get_expr(self, get: Get) -> R:
        pass

    @abstractmethod
    def visit_set_expr(self, set: Set) -> R:
        pass

    @abstractmethod
    def visit_this_expr(self, this_: This) -> R:
        pass


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        pass


class Assign(Expr):
    def __init__(self, name: Token, value: Expr) -> None:
        self.name = name
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_assign_expr(self)


class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_logical_expr(self)


class Ternary(Expr):
    def __init__(self, condition: Expr, consequent: Expr, alternative: Expr) -> None:
        self.condition = condition
        self.consequent = consequent
        self.alternative = alternative

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_ternary_expr(self)


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_binary_expr(self)


class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]) -> None:
        self.callee = callee
        self.paren = paren
        self.arguments = arguments

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_call_expr(self)


class Grouping(Expr):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_grouping_expr(self)


class Literal(Expr):
    def __init__(self, value: object) -> None:
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_literal_expr(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr) -> None:
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_unary_expr(self)


class Variable(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_variable_expr(self)


class Lambda(Expr):
    from lox.stmt import Stmt

    def __init__(self, params: list[Token], body: list[Stmt]) -> None:
        self.params = params
        self.body = body

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_lambda_expr(self)


class Get(Expr):
    def __init__(self, object: Expr, name: Token) -> None:
        self.object = object
        self.name = name

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_get_expr(self)


class Set(Expr):
    def __init__(self, object: Expr, name: Token, value: Expr) -> None:
        self.object = object
        self.name = name
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_set_expr(self)


class This(Expr):
    def __init__(self, keyword: Token) -> None:
        self.keyword = keyword

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_this_expr(self)
