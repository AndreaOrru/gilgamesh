from typing import Optional


class GilgameshError(Exception):
    ...


class ParserError(GilgameshError):
    def __init__(self, message: str, line: Optional[int] = None):
        self.message = message
        self.line = line

    def __str__(self) -> str:
        if self.line is None:
            return self.message
        return f"Line {self.line}: {self.message}"
