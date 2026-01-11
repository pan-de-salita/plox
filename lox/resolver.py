from dataclasses import dataclass, field
from functools import singledispatchmethod
from typing import Callable

from . import expr, stmt
from .class_type import ClassType
from .function_type import FunctionType
from .interpreter import Interpreter
from .token import Token


class LocalVar:
    def __init__(self, name: Token, is_defined: bool, is_used: bool) -> None:
        self.name = name
        self.is_defined = is_defined
        self.is_used = is_used


@dataclass
class Resolver(expr.Visitor, stmt.Visitor):
    # Each time the Resolver visits a variable, it tells the interpreter how
    # many scopes there are between the current scope and the scope where the
    # variable is defined. At runtime, this corresponds exactly to the number
    # of environments between the current one and the enclosing one where the
    # interpreter can find the variable's value. The resolver hands this number
    # to the interpreter by calling self._interpreter.resolve(expr, depth).

    _interpreter: Interpreter
    _error_callback: Callable[[str, Token], None]
    _scopes: list[dict[str, LocalVar]] = field(default_factory=list)
    _current_function: FunctionType = FunctionType.NONE
    _current_class: ClassType = ClassType.NONE

    def resolve(self, statements: list[stmt.Stmt]) -> None:
        for statement in statements:
            self.__resolve(statement)

    def visit_block_stmt(self, block: stmt.Block) -> None:
        self.__begin_scope()
        self.__resolve(block.statements)
        self.__check_unused_variables()
        self.__end_scope()

    def visit_expression_stmt(self, expression: stmt.Expression) -> None:
        self.__resolve(expression.expression)

    def visit_function_stmt(self, function: stmt.Function) -> None:
        # Define the function name eagerly, before resolving its body. This
        # lets a function recursively refer to itself inside its own body.
        self.__declare(function.name)
        self.__define(function.name)

        self.__resolve_function(function, FunctionType.FUNCTION)

    def visit_class_stmt(self, class_: stmt.Class) -> None:
        enclosing_class: ClassType = self._current_class
        self._current_class = ClassType.CLASS

        self.__declare(class_.name)
        self.__define(class_.name)

        self.__begin_scope()
        self.__peek_scope()["this"] = LocalVar(class_.name, True, False)

        declaration: FunctionType = FunctionType.METHOD
        for method in class_.methods:
            self.__resolve_function(method, declaration)

        self.__end_scope()
        self._current_class = enclosing_class

    def visit_if_stmt(self, if_: stmt.If) -> None:
        # Here we see how resolution is different from interpretation. When we
        # resolve an if statement, there is no control flow. We resolve the
        # condition and both branches. A static analysis is conservative -- it
        # analyzes any branch that could be run. Since either one could be
        # reached at runtime, we resolve both.
        self.__resolve(if_.condition)
        self.__resolve(if_.then_branch)
        if if_.else_branch:
            self.__resolve(if_.else_branch)

    def visit_print_stmt(self, print_: stmt.Print) -> None:
        self.__resolve(print_.expression)

    def visit_return_stmt(self, return_: stmt.Return) -> None:
        if self._current_function == FunctionType.NONE:
            self._error_callback("Can't return from top-level code.", return_.keyword)

        if return_.value:
            self.__resolve(return_.value)

    def visit_var_stmt(self, var_: stmt.Var) -> None:
        self.__declare(var_.name)
        if var_.initializer:
            self.__resolve(var_.initializer)
        self.__define(var_.name)

    def visit_while_stmt(self, while_: stmt.While) -> None:
        self.__resolve(while_.condition)
        self.__resolve(while_.body)

    def visit_break_stmt(self, break_: stmt.Break) -> None:
        return

    def visit_variable_expr(self, variable: expr.Variable) -> None:
        # Disallow access of variable inside its own initializer.
        # If the variable exists in the current scope but its value is false,
        # that means we have declared it but not yet defined it. This we treat
        # as an error.
        if self._scopes and self.__peek_scope().get(variable.name.lexeme) is False:
            self._error_callback(
                "Can't read local variable in its own initializer.", variable.name
            )

        self.__resolve_local(variable, variable.name)

    def visit_assign_expr(self, assign: expr.Assign) -> None:
        # Resolve the expression for the assigned value in case it also contains
        # references to other variables.
        self.__resolve(assign.value)

        # Resolve the variable that's being assigned to.
        self.__resolve_local(assign, assign.name)

    def visit_binary_expr(self, binary: expr.Binary) -> None:
        self.__resolve(binary.left)
        self.__resolve(binary.right)

    def visit_call_expr(self, call: expr.Call) -> None:
        self.__resolve(call.callee)
        for arg in call.arguments:
            self.__resolve(arg)

    def visit_get_expr(self, get: expr.Get) -> None:
        self.__resolve(get.object)

    def visit_set_expr(self, set: expr.Set) -> None:
        self.__resolve(set.value)
        self.__resolve(set.object)

    def visit_grouping_expr(self, grouping: expr.Grouping) -> None:
        self.__resolve(grouping.expression)

    def visit_literal_expr(self, literal: expr.Literal) -> None:
        # A literal expression doesn't mention any variables and doesn't contain
        # any subexpressions so there is no work to do.
        return

    def visit_this_expr(self, this_: expr.This) -> None:
        if self._current_class == ClassType.NONE:
            self._error_callback("Can't use 'this' outside of a class.", this_.keyword)

        # `this` should already be initialized in visit_class_stmt.
        self.__resolve_local(this_, this_.keyword)

    def visit_logical_expr(self, logical: expr.Logical) -> None:
        self.__resolve(logical.left)
        self.__resolve(logical.right)

    def visit_unary_expr(self, unary: expr.Unary) -> None:
        self.__resolve(unary.right)

    def visit_lambda_expr(self, lambda_: expr.Lambda) -> None:
        self.__resolve_function(lambda_, FunctionType.FUNCTION)

    def visit_ternary_expr(self, ternary: expr.Ternary) -> None:
        self.__resolve(ternary.condition)
        self.__resolve(ternary.consequent)
        self.__resolve(ternary.alternative)

    @singledispatchmethod
    def __resolve(self, statements: list[stmt.Stmt]) -> None:
        for statement in statements:
            statement.accept(self)

    @__resolve.register(stmt.Stmt)
    def _(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    @__resolve.register(expr.Expr)
    def _(self, expression: expr.Expr) -> None:
        expression.accept(self)

    def __resolve_function(
        self, function: stmt.Function | expr.Lambda, type_: FunctionType
    ) -> None:
        # Lox has local functions, so function declarations can be nested
        # arbitrarily deeply. We need to track not just that we're in a function,
        # but how many we're in.
        enclosing_function: FunctionType = self._current_function
        self._current_function = type_

        self.__begin_scope()
        for param in function.params:
            self.__declare(param)
            self.__define(param)
        self.__resolve(function.body)
        self.__check_unused_variables()
        self.__end_scope()

        self._current_function = enclosing_function

    def __begin_scope(self) -> None:
        self._scopes.append({})

    def __end_scope(self) -> None:
        self._scopes.pop()

    def __check_unused_variables(self) -> None:
        for local_var in self.__peek_scope().values():
            if not local_var.is_used:
                self._error_callback("Unused variable.", local_var.name)

    def __declare(self, name: Token) -> None:
        if not self._scopes:
            return

        scope: dict[str, LocalVar] = self.__peek_scope()
        if name.lexeme in scope:
            self._error_callback(
                "Already a variable with this name in this scope.", name
            )

        scope[name.lexeme] = LocalVar(name=name, is_defined=False, is_used=False)

    def __define(self, name: Token) -> None:
        if not self._scopes:
            return

        scope: dict[str, LocalVar] = self.__peek_scope()
        scope[name.lexeme].is_defined = True

    def __peek_scope(self) -> dict[str, LocalVar]:
        return self._scopes[-1]

    def __peek_prior_scope(self) -> dict[str, LocalVar]:
        return self._scopes[-2]

    def __resolve_local(
        self, variable: expr.Variable | expr.Assign | expr.This, name: Token
    ) -> None:
        # We start at the innermost scope and work outwards, looking in each
        # map for a matching name. If we find the variable, we resolve it,
        # passing in the number of scopes between the current innermost scope
        # and the scope where the variable was found (the distance). E.g., if
        # the variable was found in the current scope, we pass in 0. If it's
        # in the immediately enclosing scope, 1.
        #
        # If we walk through all of the block scopes and never find the variable,
        # we leave it unresolved and assume it's global.

        # For testing:
        # print([[v for v in s.keys()] for s in self._scopes])
        for i, scope in enumerate(self._scopes):
            if name.lexeme in scope:
                scope[name.lexeme].is_used = True
                self._interpreter.resolve(variable, len(self._scopes) - 1 - i)
                break
