import os
from dataclasses import dataclass
from enum import Enum, auto
from itertools import zip_longest
from subprocess import check_call
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional
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
    def __init__(self, message: str, line: Optional[int] = None):
        self.message = message
        self.line = line

    def __str__(self) -> str:
        if self.line is None:
            return f"{self.message}."
        return f"Line {self.line}: {self.message}."


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
        # Save the subroutines's disassembly in a temporary file.
        original_text = self.text
        with NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            f.write(original_text)
            filename = f.name

        # Edit the file in an editor.
        check_call([*os.environ["EDITOR"].split(), filename])
        new_text = open(filename).read()
        os.remove(filename)

        # Compare the two files and apply the changes.
        original_tokens = self._text_to_tokens(
            original_text
        )  # TODO: take tokens directly.
        new_tokens = self._text_to_tokens(new_text)
        self._apply_changes(original_tokens, new_tokens)

    def _apply_changes(
        self, original_tokens: List[List[Token]], new_tokens: List[List[Token]]
    ) -> None:
        """Compare a collection of tokens describing a subroutine, with a new one
        with potentially updated content. Apply changes where possible."""
        line_n = 1
        renamed_labels: Dict[str, str] = {}

        for orig_instr_tokens, new_instr_tokens in zip_longest(
            original_tokens, new_tokens
        ):
            if (orig_instr_tokens is None) or (new_instr_tokens is None):
                raise ParserError("Added or deleted an instruction", line_n)
            self._apply_instruction_changes(
                line_n, orig_instr_tokens, new_instr_tokens, renamed_labels
            )
            line_n += 1

        self._apply_renamed_labels(renamed_labels)

    def _apply_instruction_changes(
        self,
        line_n: int,
        original_tokens: List[Token],
        new_tokens: List[Token],
        renamed_labels: Dict[str, str],
    ) -> None:
        pc = 0
        for orig, new in zip_longest(original_tokens, new_tokens):
            # Error cases.
            if (orig is None) or (new is None):
                raise ParserError("Added or deleted token", line_n)
            elif orig.typ != new.typ:
                raise ParserError("Changed the type of a token", line_n)
            elif orig.typ not in EDITABLE_TOKENS and orig.val != new.val:
                raise ParserError(
                    f'Can\'t edit token of type "{orig.typ.name}"', line_n
                )

            # Keep track of the PC of the instruction.
            elif orig.typ == TokenType.PC:
                pc = int(orig.val[1:], 16)

            # If the value of the current token has been changed:
            elif orig.val != new.val:
                # Comments.
                if orig.typ == TokenType.COMMENT:
                    if new.val:
                        self.log.comments[pc] = new.val
                    else:
                        self.log.comments.pop(pc, None)
                # Labels.
                elif orig.typ in (TokenType.LABEL, TokenType.OPERAND_LABEL):
                    if renamed_labels.get(orig.val, new.val) != new.val:
                        raise ParserError("Ambiguous label change", line_n)
                    renamed_labels[orig.val] = new.val

    def _apply_renamed_labels(self, renamed_labels: Dict[str, str]) -> None:
        """Safely perform bulk label renames."""

        def apply(labels: Dict[str, str]) -> None:
            """Naively perform label renames."""
            for old, new in labels.items():
                if old[0] == ".":
                    old, new = old[1:], new[1:]
                self.log.rename_label(old, new, self.subroutine.pc)

        # Make sure we are keeping the dots at the beginning of the local labels.
        for old, new in renamed_labels.items():
            if old[0] == "." and new[0] != ".":
                raise ParserError("Tried to transform a local label into a global one")

        # Rename labels to temporary unique labels.
        temp_renamed_labels = {
            old: self._unique_label(old) for old in renamed_labels.keys()
        }
        apply(temp_renamed_labels)
        # Re-rename the unique labels to the target labels.
        renamed_labels = {
            unique_label: renamed_labels[old]
            for old, unique_label in temp_renamed_labels.items()
        }
        apply(renamed_labels)
        # NOTE: this is needed when swapping pairs of labels.

    @staticmethod
    def _instruction_html(tokens: List[Token]) -> str:
        """Generate HTML from the list of tokens describing an instruction."""
        s = []
        for token in tokens:
            if token.typ == TokenType.LABEL:
                s.append(f"<red>{token.val}</red>:\n")
            elif token.typ == TokenType.OPERATION:
                s.append("  <green>{:4}</green>".format(token.val))
            elif token.typ == TokenType.OPERAND:
                s.append("{:20}".format(token.val))
            elif token.typ == TokenType.OPERAND_LABEL:
                s.append("<red>{:20}</red>".format(token.val))
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
        """Convert an instruction into a list of token which describes it."""
        tokens = []

        # Label.
        subroutine_pc = instruction.subroutine
        label = self.log.get_label(instruction.pc, subroutine_pc)
        if label:
            tokens.append(Token(TokenType.LABEL, label))

        # Operation + Operand.
        tokens.append(Token(TokenType.OPERATION, instruction.name))
        if instruction.argument_alias:
            tokens.append(Token(TokenType.OPERAND_LABEL, instruction.argument_alias))
        else:
            tokens.append(Token(TokenType.OPERAND, instruction.argument_string))

        # PC + Comment.
        tokens.append(Token(TokenType.PC, "${:06X}".format(instruction.pc)))
        comment = self.log.comments.get(instruction.pc, "")
        tokens.append(Token(TokenType.COMMENT, comment))

        # Assertions or unknown state.
        subroutine = self.log.subroutines[subroutine_pc]
        if subroutine.has_asserted_state_change and (
            instruction.stopped_execution or instruction.is_return
        ):
            # Subroutine with asserted return state.
            state_expr = subroutine.state_change.state_expr
            tokens.append(Token(TokenType.ASSERTION, state_expr))
        elif instruction.pc in self.log.instruction_assertions:
            # Instruction with asserted state change.
            state_expr = self.log.instruction_assertions[instruction.pc].state_expr
            tokens.append(Token(TokenType.ASSERTION, state_expr))
        elif instruction.stopped_execution:
            # Unknown state.
            next_pc = "${:06X}".format(instruction.next_pc)
            tokens.append(Token(TokenType.UNKNOWN_STATE, next_pc))

        return tokens

    @staticmethod
    def _text_to_tokens(text: str) -> List[List[Token]]:
        """Parse a subroutines's disassembly into a list of lists of tokens."""
        tokens = []
        line_n = 1

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
                    raise ParserError("Missing comment section", line_n)
                tokens[-1].append(Token(TokenType.PC, words[i + 1]))
                try:
                    comment = line.split("|", maxsplit=1)[1].strip()
                except IndexError:
                    raise ParserError("Expected | before comment", line_n)
                tokens[-1].append(Token(TokenType.COMMENT, comment))

            # Assertion/state line.
            elif words[0] == ";":
                if words[1:4] == "Asserted state change:".split():
                    tokens[-1].append(Token(TokenType.ASSERTION, words[4]))
                elif words[1:4] == "Unknown state at".split():
                    tokens[-1].append(Token(TokenType.UNKNOWN_STATE, words[4]))

            else:
                raise ParserError("Unable to parse line", line_n)

            line_n += 1

        return tokens

    @staticmethod
    def _unique_label(orig_label: str) -> str:
        """Return a unique label. Respects locality (i.e. if orig_label
        starts with a dot, the generated label will also start with a dot."""
        return orig_label[0] + "l" + uuid4().hex
        # TODO: check for meteors.
