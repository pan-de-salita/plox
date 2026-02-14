# Generated from GenerateAst class (2026-02-14 19:03:29.326485).

from __future__ import annotations

from abc import ABC, abstractmethod
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
    def visit_class_stmt(self, class_: Class) -> R:
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


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        pass


class Var(Stmt):
    def __init__(self, name: Token, is_initialized: bool, initializer: Expr | None = None) -> None:
        self.name = name
        self.is_initialized = is_initialized
        self.initializer = initializer

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_var_stmt(self)


class Expression(Stmt):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_expression_stmt(self)


class Function(Stmt):
    def __init__(self, name: Token, params: list[Token], body: list[Stmt], is_static: bool = False, is_getter: bool = False) -> None:
        self.name = name
        self.params = params
        self.body = body
        self.is_static = is_static
        self.is_getter = is_getter

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_function_stmt(self)


class Class(Stmt):
    def __init__(self, name: Token, methods: list[Function], superclass: Expr.Variable | None = None) -> None:
        self.name = name
        self.methods = methods
        self.superclass = superclass

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_class_stmt(self)


class If(Stmt):
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt | None = None) -> None:
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_if_stmt(self)


class While(Stmt):
    def __init__(self, condition: Expr, body: Stmt) -> None:
        self.condition = condition
        self.body = body

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_while_stmt(self)


class Break(Stmt):
    def __init__(self, token: Token) -> None:
        self.token = token

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_break_stmt(self)


class Print(Stmt):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_print_stmt(self)


class Return(Stmt):
    def __init__(self, keyword: Token, value: Expr | None = None) -> None:
        self.keyword = keyword
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_return_stmt(self)


class Block(Stmt):
    def __init__(self, statements: list[Stmt]) -> None:
        self.statements = statements

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_block_stmt(self)
