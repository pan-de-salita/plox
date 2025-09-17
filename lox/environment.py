from dataclasses import dataclass, field
from typing import Self

from .runtime_exception import RuntimeException
from .token import Token


@dataclass()
class Environment:
    _values: dict[str, object] = field(default_factory=dict)
    enclosing: Self | None = None

    def define(self, name_lexeme: str, value: object) -> None:
        """Define a variable."""
        self._values[name_lexeme] = value

    def get(self, name: Token) -> object:
        """Gets a variable's value if it's name exists in the Environment's
        values, else raise a RuntimeException."""
        if name in self._values.keys():
            return self._values[name.lexeme]

        if self.enclosing:
            return self.enclosing.get(name=name)

        raise RuntimeException(
            token=name, message=f"Undefined variable: {name.lexeme}."
        )

    def assign(self, name: Token, value: object) -> None:
        """Assign a value to a name."""
        if name.lexeme in self._values.keys():
            self._values[name.lexeme] = value
            return

        if self.enclosing:
            self.enclosing.assign(name=name, value=value)
            return

        raise RuntimeException(
            token=name, message=f"Undefined variable: {name.lexeme}."
        )
