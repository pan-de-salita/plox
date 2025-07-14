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
        return f"{self.type} {self.lexeme} {self.literal}"
