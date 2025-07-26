from dataclasses import dataclass
from typing import Any

from .token_type import TokenType


@dataclass(frozen=True)
class Token:
    type: TokenType
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
