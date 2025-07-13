from dataclasses import dataclass
from token import Token


@dataclass(frozen=True)
class Scanner:
    source: str
    tokens: list[Token] = []
