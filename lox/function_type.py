from __future__ import annotations

from enum import Enum


class FunctionType(Enum):
    NONE = None
    FUNCTION = "function"
    INITIALIZER = "initializer"
    METHOD = "method"
