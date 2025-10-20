from dataclasses import dataclass, field
from typing import Self

from .runtime_exception import RuntimeException
from .token import Token


@dataclass()
class Assigned:
    value: object
    is_initialized: bool


@dataclass()
class Environment:
    _values: dict[str, Assigned] = field(default_factory=dict)
    enclosing: Self | None = None

    def define(self, name: str, value: object, is_initialized: bool) -> None:
        """Define a variable."""
        self._values[name] = Assigned(value=value, is_initialized=is_initialized)

    def get(self, name: Token) -> object:
        """Gets a variable's value if it's name exists in the Environment's
        values, else raise a RuntimeException."""
        if name.lexeme in self._values:
            assigned: Assigned = self._values[name.lexeme]
            if assigned.is_initialized:
                return assigned.value

            raise RuntimeException(
                token=name, message=f"Uninitialized variable: {name.lexeme}."
            )

        if self.enclosing:
            return self.enclosing.get(name=name)

        raise RuntimeException(
            token=name, message=f"Undefined variable: {name.lexeme}."
        )

    def assign(self, name: Token, value: object) -> None:
        """Assign a value to a name."""
        if name.lexeme in self._values:
            self._values[name.lexeme].value = value
            self._values[name.lexeme].is_initialized = True
            return

        if self.enclosing:
            self.enclosing.assign(name=name, value=value)
            return

        raise RuntimeException(
            token=name, message=f"Undefined variable: {name.lexeme}."
        )
