from dataclasses import dataclass
from typing import Any

from lox_token_type import LoxTokenType


@dataclass(frozen=True)
class LoxToken:
    type: LoxTokenType
    lexeme: str
    literal: Any
    line: int

    def __str__(self) -> str:
        return (
            f"Type: {self.type.name} "
            + f"Lexeme: {self.lexeme} "
            + f"Literal: {self.literal if self.literal else 'None'} "
            + f"Line: {self.line}"
        )
