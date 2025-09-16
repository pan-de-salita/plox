from dataclasses import dataclass, field

from .runtime_exception import RuntimeException
from .token import Token


@dataclass()
class Environment:
    _values: dict[str, object] = field(default_factory=dict)

    def define(self, name: str, value: object) -> None:
        self._values[name] = value

    def get(self, name: Token) -> object:
        """Gets a variable's value if it's name exists in the Environment's
        values, else raise a RuntimeException."""
        try:
            return self._values[name.lexeme]
        except Exception:
            raise RuntimeException(
                token=name, message=f"Undefined variable: {name.lexeme}."
            )
