import os
from dataclasses import dataclass
from enum import Enum, auto
from itertools import zip_longest
from subprocess import check_call
from tempfile import NamedTemporaryFile
from typing import Dict, List
from uuid import uuid4

from bs4 import BeautifulSoup as BS  # type: ignore

from gilgamesh.instruction import Instruction
from gilgamesh.log import Log
from gilgamesh.opcodes import Op
from gilgamesh.subroutine import Subroutine


class TokenType(Enum):
    ASSERTION = auto()
    COMMENT = auto()
    LABEL = auto()
    OPERAND = auto()
    OPERAND_LABEL = auto()
    OPERATION = auto()
    PC = auto()
    UNKNOWN_STATE = auto()


EDITABLE_TOKENS = (TokenType.LABEL, TokenType.OPERAND_LABEL, TokenType.COMMENT)


@dataclass
class Token:
    typ: TokenType
    val: str


class ParserError(Exception):
    ...


class Disassembly:
    def __init__(self, log: Log, subroutine: Subroutine):
        self.log = log
        self.subroutine = subroutine

    @property
    def html(self) -> str:
        s = []
        for instruction in self.subroutine.instructions.values():
            tokens = self._instruction_to_tokens(instruction)
            s.append(self._instruction_html(tokens))
        return "".join(s)

    @property
    def text(self) -> str:
        return BS(f"<pre>{self.html}</pre>", "html.parser").get_text()

    def edit(self) -> None:
        original_text = self.text
        with NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            f.write(original_text)
            filename = f.name

        check_call([*os.environ["EDITOR"].split(), filename])
        new_text = open(filename).read()
        os.remove(filename)

        original_tokens = self._text_to_tokens(
            original_text
        )  # TODO: take tokens directly.
        new_tokens = self._text_to_tokens(new_text)
        self._apply_changes(original_tokens, new_tokens)

    def _apply_changes(
        self, original_tokens: List[List[Token]], new_tokens: List[List[Token]]
    ) -> None:
        renamed_labels: Dict[str, str] = {}
        for orig_instr_tokens, new_instr_tokens in zip_longest(
            original_tokens, new_tokens
        ):
            if (orig_instr_tokens is None) or (new_instr_tokens is None):
                raise ParserError("Added or deleted an instruction.")
            self._apply_instruction_changes(
                orig_instr_tokens, new_instr_tokens, renamed_labels
            )
        self._apply_renamed_labels(renamed_labels)

    def _apply_instruction_changes(
        self,
        original_tokens: List[Token],
        new_tokens: List[Token],
        renamed_labels: Dict[str, str],
    ) -> None:
        pc = 0
        for orig, new in zip_longest(original_tokens, new_tokens):
            if (orig is None) or (new is None):
                raise ParserError("Added or deleted token.")
            elif orig.typ != new.typ:
                raise ParserError("Changed the type of a token.")
            elif orig.typ not in EDITABLE_TOKENS and orig.val != new.val:
                raise ParserError(f'Can\'t edit token of type "{orig.typ.name}".')

            elif orig.typ == TokenType.PC:
                pc = int(orig.val[1:], 16)

            elif orig.val != new.val:
                if orig.typ == TokenType.COMMENT:
                    if new.val:
                        self.log.comments[pc] = new.val
                    else:
                        self.log.comments.pop(pc, None)
                elif orig.typ in (TokenType.LABEL, TokenType.OPERAND_LABEL):
                    if renamed_labels.get(orig.val, new.val) != new.val:
                        raise ParserError("Ambiguous label change.")
                    renamed_labels[orig.val] = new.val

    def _apply_renamed_labels(self, renamed_labels: Dict[str, str]) -> None:
        def apply(labels: Dict[str, str]) -> None:
            for old, new in labels.items():
                if old[0] == ".":
                    if new[0] != ".":
                        raise ParserError(
                            "Tried to transform a local label into a global one."
                        )
                    old, new = old[1:], new[1:]
                self.log.rename_label(old, new, self.subroutine.pc)

        temp_renamed_labels = {
            old: self._unique_label(old) for old in renamed_labels.keys()
        }
        apply(temp_renamed_labels)
        renamed_labels = {
            unique_label: renamed_labels[old]
            for old, unique_label in temp_renamed_labels.items()
        }
        apply(renamed_labels)

    @staticmethod
    def _instruction_html(tokens: List[Token]) -> str:
        s = []
        for token in tokens:
            if token.typ == TokenType.LABEL:
                s.append(f"<red>{token.val}</red>:\n")
            elif token.typ == TokenType.OPERATION:
                s.append("  <green>{:4}</green>".format(token.val))
            elif token.typ == TokenType.OPERAND:
                s.append("{:16}".format(token.val))
            elif token.typ == TokenType.OPERAND_LABEL:
                s.append("<red>{:16}</red>".format(token.val))
            elif token.typ == TokenType.PC:
                s.append(f"<grey>; {token.val} | </grey>")
            elif token.typ == TokenType.COMMENT:
                s.append(f"<grey>{token.val}</grey>")
            elif token.typ == TokenType.ASSERTION:
                s.append(f"\n  <grey>; Asserted state change: {token.val}</grey>")
            elif token.typ == TokenType.UNKNOWN_STATE:
                s.append(f"\n  <grey>; Unknown state at {token.val}</grey>")
        s.append("\n")
        return "".join(s)

    def _instruction_to_tokens(self, instruction: Instruction) -> List[Token]:
        tokens = []

        subroutine_pc = instruction.subroutine
        label = self.log.get_label(instruction.pc, subroutine_pc)
        if label:
            tokens.append(Token(TokenType.LABEL, label))

        tokens.append(Token(TokenType.OPERATION, instruction.name))
        if instruction.argument_alias:
            tokens.append(Token(TokenType.OPERAND_LABEL, instruction.argument_alias))
        else:
            tokens.append(Token(TokenType.OPERAND, instruction.argument_string))

        tokens.append(Token(TokenType.PC, "${:06X}".format(instruction.pc)))
        comment = self.log.comments.get(instruction.pc, "")
        tokens.append(Token(TokenType.COMMENT, comment))

        subroutine = self.log.subroutines[subroutine_pc]
        if subroutine.has_asserted_state_change and (
            instruction.stopped_execution or instruction.is_return
        ):
            state_expr = subroutine.state_change.state_expr
            tokens.append(Token(TokenType.ASSERTION, state_expr))
        elif instruction.pc in self.log.instruction_assertions:
            state_expr = self.log.instruction_assertions[instruction.pc].state_expr
            tokens.append(Token(TokenType.ASSERTION, state_expr))
        elif instruction.stopped_execution:
            next_pc = "${:06X}".format(instruction.next_pc)
            tokens.append(Token(TokenType.UNKNOWN_STATE, next_pc))

        return tokens

    def _text_to_tokens(self, text: str) -> List[List[Token]]:
        tokens = []

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            words = line.split()

            # Label line.
            if len(words) == 1 and line[-1] == ":":
                tokens.append([Token(TokenType.LABEL, line[:-1])])

            # Instruction line.
            elif words[0].upper() in Op.__members__:
                if tokens[-1][-1].typ != TokenType.LABEL:
                    tokens.append([])
                tokens[-1].append(Token(TokenType.OPERATION, words[0].lower()))
                i = 1

                # Operand section.
                if words[i] == ";":
                    tokens[-1].append(Token(TokenType.OPERAND, ""))
                else:
                    word = words[i]
                    if ("a" == word) or ("$" in word) or ("," in word):
                        tokens[-1].append(Token(TokenType.OPERAND, word))
                    elif word.isidentifier() or (
                        word[0] == "." and word[1:].isidentifier()
                    ):
                        tokens[-1].append(Token(TokenType.OPERAND_LABEL, word))
                    i += 1

                # Comment section.
                if words[i] != ";":
                    raise ParserError("Missing comment section.")
                tokens[-1].append(Token(TokenType.PC, words[i + 1]))
                try:
                    comment = line.split("|", maxsplit=1)[1].strip()
                except IndexError:
                    raise ParserError("Expected | before comment.")
                tokens[-1].append(Token(TokenType.COMMENT, comment))

            # Assertion/state line.
            elif words[0] == ";":
                if words[1:4] == "Asserted state change:".split():
                    tokens[-1].append(Token(TokenType.ASSERTION, words[4]))
                elif words[1:4] == "Unknown state at".split():
                    tokens[-1].append(Token(TokenType.UNKNOWN_STATE, words[4]))

            else:
                raise ParserError("Unable to parse line.")

        return tokens

    def _unique_label(self, orig_label: str) -> str:
        # TODO: check for collisions.
        return orig_label[0] + "l" + uuid4().hex
