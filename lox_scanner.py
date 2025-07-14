from dataclasses import dataclass, field

from lox_token import LoxToken
from lox_token_type import LoxTokenType


@dataclass()
class LoxScanner:
    source: str
    tokens: list[LoxToken] = field(default_factory=list)
    start: int = 0
    current: int = 0
    line: int = 1

    def scan_tokens(self) -> list[LoxToken]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens += [LoxToken(LoxTokenType.EOF, "", None, self.line)]
        return self.tokens

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def scan_token() -> None:
        return None
