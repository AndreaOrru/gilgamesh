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
    FATAL_STACK_MANIPULATION_HEADER = auto()
    HIGHLIGHTED_OPERAND_LABEL = auto()
    HW_REGISTER = auto()
    JUMP_TABLE_COMPLETE_ENTRY = auto()
    JUMP_TABLE_ENTRY = auto()
    JUMP_TABLE_HEADER = auto()
    JUMP_TABLE_LABEL = auto()
    JUMP_TABLE_OPERAND_LABEL = auto()
    JUMP_TABLE_UNKNOWN_ENTRY = auto()
    KNOWN_STATE_CHANGE = auto()
    KNOWN_STATE_HEADER = auto()
    LABEL = auto()
    LAST_KNOWN_STATE = auto()
    LAST_KNOWN_STATE_CHANGE = auto()
    NEWLINE = auto()
    OPERAND = auto()
    OPERAND_LABEL = auto()
    OPERATION = auto()
    PC = auto()
    SEPARATOR_LINE = auto()
    STACK_MANIPULATION_HEADER = auto()
    SUGGESTED_ASSERTION = auto()
    SUGGESTED_ASSERTION_TYPE = auto()
    UNKNOWN_REASON = auto()
    UNKNOWN_STATE_HEADER = auto()


HEADER_TOKENS = {
    TokenType.ASSERTED_STATE_HEADER,
    TokenType.FATAL_STACK_MANIPULATION_HEADER,
    TokenType.JUMP_TABLE_HEADER,
    TokenType.KNOWN_STATE_HEADER,
    TokenType.SEPARATOR_LINE,
    TokenType.STACK_MANIPULATION_HEADER,
    TokenType.UNKNOWN_STATE_HEADER,
}

EDITABLE_TOKEN_TYPES = {
    TokenType.SUGGESTED_ASSERTION: TokenType.ASSERTION,
    TokenType.SUGGESTED_ASSERTION_TYPE: TokenType.ASSERTION_TYPE,
}

EDITABLE_TOKENS = {
    *EDITABLE_TOKEN_TYPES.keys(),
    TokenType.ASSERTION,
    TokenType.ASSERTION_TYPE,
    TokenType.COMMENT,
    TokenType.JUMP_TABLE_ENTRY,
    TokenType.LABEL,
    TokenType.OPERAND_LABEL,
}

EQUIVALENT_TOKENS = {
    TokenType.FATAL_STACK_MANIPULATION_HEADER: TokenType.STACK_MANIPULATION_HEADER,
    TokenType.HIGHLIGHTED_OPERAND_LABEL: TokenType.OPERAND_LABEL,
    TokenType.JUMP_TABLE_COMPLETE_ENTRY: TokenType.JUMP_TABLE_ENTRY,
    TokenType.JUMP_TABLE_LABEL: TokenType.LABEL,
    TokenType.JUMP_TABLE_OPERAND_LABEL: TokenType.OPERAND_LABEL,
    TokenType.JUMP_TABLE_UNKNOWN_ENTRY: TokenType.JUMP_TABLE_ENTRY,
    TokenType.JUMP_TABLE_UNKNOWN_ENTRY: TokenType.JUMP_TABLE_ENTRY,
}


@dataclass
class Token:
    typ: TokenType
    val: str = ""


class Parser:
    def __init__(self, text: str, base_line_n: int):
        self.lines = text.splitlines()
        self.line_idx = 0
        self.base_line_n = base_line_n
        self.tokens: List[List[Token]] = []

    @property
    def line_n(self) -> int:
        return self.line_idx + self.base_line_n

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
        self.add(TokenType.NEWLINE)
        self.line_idx += 1
        invalidate(self, "line")
        invalidate(self, "words")

    def maybe_match_line(self, s: str) -> bool:
        return self.words == s.split()

    def match_line(self, token_typ: TokenType, s: str) -> None:
        if not self.maybe_match_line(s):
            raise ParserError("Unable to parse line.", self.line_n)
        self.add_line(token_typ)

    def add_line_rest(self, token_typ: TokenType, after: str, words_limit=1) -> None:
        parts = after.split()
        if not self.words[: len(parts)] == parts:
            raise ParserError("Unable to parse line.", self.line_n)

        after_parts = self.words[len(parts) :]
        if words_limit > 0 and len(after_parts) > words_limit:
            raise ParserError("Unable to parse line.", self.line_n)

        rest = " ".join(after_parts)
        self.add_line(token_typ, rest)

    def new_instruction(self) -> None:
        self.tokens.append([])

    def maybe_new_instruction(self, *args) -> None:
        if self.tokens[-1][-2].typ not in (
            TokenType.LABEL,
            TokenType.STACK_MANIPULATION_HEADER,
        ):
            self.new_instruction()
