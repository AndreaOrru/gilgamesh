from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from cached_property import cached_property  # type: ignore

from gilgamesh.errors import ParserError
from gilgamesh.utils.cached_property import invalidate


class TokenType(Enum):
    ASSERTED_STATE_HEADER = auto()
    ASSERTION = auto()
    ASSERTION_TYPE = auto()
    COMMENT = auto()
    LABEL = auto()
    LAST_KNOWN_STATE = auto()
    NEWLINE = auto()
    OPERAND = auto()
    OPERAND_LABEL = auto()
    OPERATION = auto()
    PC = auto()
    KNOWN_STATE = auto()
    KNOWN_STATE_HEADER = auto()
    SEPARATOR_LINE = auto()
    STACK_MANIPULATION_HEADER = auto()
    UNKNOWN_STATE_HEADER = auto()


EDITABLE_TOKENS = {
    TokenType.ASSERTION,
    TokenType.ASSERTION_TYPE,
    TokenType.LABEL,
    TokenType.OPERAND_LABEL,
    TokenType.COMMENT,
}


@dataclass
class Token:
    typ: TokenType
    val: str = ""


class Parser:
    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.line_idx = 0
        self.tokens: List[List[Token]] = []

    @property
    def line_n(self) -> int:
        return self.line_idx + 2

    @cached_property
    def line(self) -> str:
        return self.lines[self.line_idx].strip()

    @cached_property
    def words(self) -> List[str]:
        return self.line.split()

    def lookahead_words(self, lookahead: int) -> List[str]:
        lookahead_line = self.lines[self.line_idx + lookahead].strip()
        return lookahead_line.split()

    def add(self, *args):
        self.tokens[-1].append(Token(*args))

    def add_line(self, *args) -> None:
        if args:
            self.add(*args)
        self.tokens[-1].append(Token(TokenType.NEWLINE, "\n"))
        self.line_idx += 1
        invalidate(self, "line")
        invalidate(self, "words")

    def maybe_match_line(self, s: str, lookahead=0) -> bool:
        return self.lookahead_words(lookahead) == s.split()

    def match_line(self, token_typ: TokenType, s: str) -> None:
        if not self.maybe_match_line(s):
            raise ParserError("Unable to parse line.", self.line_n)
        self.add_line(token_typ)

    def maybe_match_part(self, s: str, lookahead=0) -> bool:
        parts = s.split()
        lookahead_words = self.lookahead_words(lookahead)
        return lookahead_words[: len(parts)] == parts

    def match_part(self, s: str) -> None:
        if not self.maybe_match_part(s):
            raise ParserError("Unable to parse line.", self.line_n)

    def add_instr(self) -> None:
        self.tokens.append([])

    def maybe_add_instr(self, *args) -> None:
        if self.tokens[-1][-2].typ not in (
            TokenType.LABEL,
            TokenType.STACK_MANIPULATION_HEADER,
        ):
            self.add_instr()
