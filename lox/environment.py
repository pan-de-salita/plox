from dataclasses import dataclass, field

from .runtime_exception import RuntimeException
from .token import Token


@dataclass()
class Environment:
    _values: dict[str, object] = field(default_factory=dict)

    def define(self, name_lexeme: str, value: object) -> None:
        self._values[name_lexeme] = value

    def get(self, name: Token) -> object:
        """Gets a variable's value if it's name exists in the Environment's
        values, else raise a RuntimeException."""
        try:
            return self._values[name.lexeme]
        except Exception:
            raise RuntimeException(
                token=name, message=f"Undefined variable: {name.lexeme}."
            )

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self._values.keys():
            self._values[name.lexeme] = value

        raise RuntimeException(
            token=name, message=f"Undefined variable: {name.lexeme}."
        )
