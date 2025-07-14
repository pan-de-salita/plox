from dataclasses import dataclass, field

from lox_token import LoxToken


@dataclass(frozen=True)
class LoxScanner:
    source: str
    tokens: list[LoxToken] = field(default_factory=list)
