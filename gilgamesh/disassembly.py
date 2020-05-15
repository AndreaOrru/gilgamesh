import os
from dataclasses import dataclass
from enum import Enum, auto
from itertools import zip_longest
from subprocess import check_call
from tempfile import NamedTemporaryFile
from typing import Dict, Iterable, List, Tuple
from uuid import uuid4

from gilgamesh.errors import ParserError
from gilgamesh.instruction import Instruction
from gilgamesh.log import Log
from gilgamesh.opcodes import Op
from gilgamesh.subroutine import Subroutine


class TokenType(Enum):
    ASSERTION = auto()
    COMMENT = auto()
    LABEL = auto()
    NEWLINE = auto()
    OPERAND = auto()
    OPERAND_LABEL = auto()
    OPERATION = auto()
    PC = auto()
    STACK_MANIPULATION = auto()
    UNKNOWN_STATE = auto()


EDITABLE_TOKENS = (TokenType.LABEL, TokenType.OPERAND_LABEL, TokenType.COMMENT)


@dataclass
class Token:
    typ: TokenType
    val: str = ""


def apply_renames(log: Log, renamed_labels: Dict[str, str]) -> None:
    def apply(labels: Dict[str, str], dry=False) -> None:
        """Naively perform label renames."""
        for old, new in labels.items():
            log.rename_label(old, new, dry=dry)

    # Rename labels to temporary unique labels.
    temp_renamed_labels = {old: unique_label(old) for old in renamed_labels.keys()}
    # Perform a dry run to make sure there are no errors
    # when renames are applied to the full disassembly.
    apply(temp_renamed_labels, dry=True)
    # Actually apply the renames if everything was ok.
    apply(temp_renamed_labels)

    # Re-rename the unique labels to the target labels.
    renamed_labels = {
        unique_label: renamed_labels[old]
        for old, unique_label in temp_renamed_labels.items()
    }
    apply(renamed_labels)
    # NOTE: this is needed when swapping pairs of labels.


def unique_label(orig_label: str) -> str:
    """Return a unique label. Respects locality (i.e. if orig_label
    starts with a dot, the generated label will also start with a dot."""
    return orig_label[0] + "l" + uuid4().hex
    # TODO: check for meteors.


class Disassembly:
    def __init__(self, subroutine: Subroutine):
        self.log = subroutine.log
        self.subroutine = subroutine

    def get_html(self) -> str:
        return self._get_text(html=True)[0]

    def get_instruction_html(self, instruction: Instruction) -> str:
        tokens = self._instruction_to_tokens(instruction)
        return self._instruction_tokens_to_text(tokens, html=True)

    def _get_text(self, html=False) -> Tuple[str, List[List[Token]]]:
        s, tokens = [], []
        for instruction in self.subroutine.instructions.values():
            instr_tokens = self._instruction_to_tokens(instruction)
            tokens.append(instr_tokens)
            s.append(self._instruction_tokens_to_text(instr_tokens, html))
        return "".join(s), tokens

    def _apply_changes(
        self, original_tokens: List[List[Token]], new_tokens: List[List[Token]]
    ) -> Dict[str, str]:
        """Compare a collection of tokens describing a subroutine, with a new one
        with potentially updated content. Apply changes where possible."""
        line_n = 1
        renamed_labels: Dict[str, str] = {}

        for orig_instr_tokens, new_instr_tokens in zip_longest(
            original_tokens, new_tokens
        ):
            if (orig_instr_tokens is None) or (new_instr_tokens is None):
                raise ParserError("Added or deleted an instruction.", line_n)
            line_n = self._apply_instruction_changes(
                line_n, orig_instr_tokens, new_instr_tokens, renamed_labels
            )

        return self._apply_renames(renamed_labels)

    def _apply_instruction_changes(
        self,
        line_n: int,
        original_tokens: List[Token],
        new_tokens: List[Token],
        renamed_labels: Dict[str, str],
    ) -> int:
        pc = 0
        for orig, new in zip_longest(original_tokens, new_tokens):
            # Count lines.
            if new and new.typ == TokenType.NEWLINE:
                line_n += 1

            # Error cases.
            elif (orig is None) or (new is None):
                raise ParserError("Added or deleted token.", line_n)
            elif orig.typ != new.typ:
                raise ParserError("Changed the type of a token.", line_n)
            elif orig.typ not in EDITABLE_TOKENS and orig.val != new.val:
                raise ParserError(
                    f'Can\'t edit token of type "{orig.typ.name}".', line_n
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
                        raise ParserError("Ambiguous label change.", line_n)
                    renamed_labels[orig.val] = new.val
        return line_n

    def _apply_renames(self, renamed_labels: Dict[str, str]) -> Dict[str, str]:
        """Safely perform bulk label renames."""

        # Separate local and global renames. Global renames
        # will be performed by the DisassemblyContainer.
        local_renames = {}
        global_renames = {}
        for old, new in renamed_labels.items():
            if old[0] == ".":
                local_renames[old] = new
            else:
                global_renames[old] = new

        apply_renames(self.log, local_renames)
        return global_renames

    @staticmethod
    def _instruction_tokens_to_text(tokens: List[Token], html=False) -> str:
        """Generate HTML or plain text from the list
        of tokens describing an instruction."""

        def o(color: str) -> str:
            return f"<{color}>" if html else ""

        def c(color: str) -> str:
            return f"</{color}>" if html else ""

        s = []
        for token in tokens:
            if token.typ == TokenType.NEWLINE:
                s.append("\n")
            elif token.typ == TokenType.LABEL:
                s.append("{}{}{}:".format(o("red"), token.val, c("red")))
            elif token.typ == TokenType.STACK_MANIPULATION:
                s.append("  {}; Stack manipulation{}".format(o("grey"), c("grey")))
            elif token.typ == TokenType.OPERATION:
                s.append("  {}{:4}{}".format(o("green"), token.val, c("green")))
            elif token.typ == TokenType.OPERAND:
                s.append("{:25}".format(token.val))
            elif token.typ == TokenType.OPERAND_LABEL:
                s.append("{}{:25}{}".format(o("red"), token.val, c("red")))
            elif token.typ == TokenType.PC:
                s.append(" {}; {}{}".format(o("grey"), token.val, c("grey")))
            elif token.typ == TokenType.COMMENT:
                s.append("{} | {}{}".format(o("grey"), token.val, c("grey")))
            elif token.typ == TokenType.ASSERTION:
                s.append(
                    "  {}; Asserted state change: {}{}".format(
                        o("grey"), token.val, c("grey")
                    )
                )
            elif token.typ == TokenType.UNKNOWN_STATE:
                s.append(
                    "  {}; Unknown state. Last known state change: {}{}".format(
                        o("grey"), token.val, c("grey")
                    )
                )

        return "".join(s)

    def _instruction_to_tokens(self, instruction: Instruction) -> List[Token]:
        """Convert an instruction into a list of token which describes it."""
        tokens = []

        # Label.
        subroutine_pc = instruction.subroutine
        label = self.log.get_label(instruction.pc, subroutine_pc)
        if label:
            tokens.append(Token(TokenType.LABEL, label))
            tokens.append(Token(TokenType.NEWLINE, "\n"))

        # Stack manipulation.
        if instruction.does_manipulate_stack:
            tokens.append(Token(TokenType.STACK_MANIPULATION))
            tokens.append(Token(TokenType.NEWLINE, "\n"))

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
        tokens.append(Token(TokenType.NEWLINE, "\n"))

        # Assertions or unknown state.
        subroutine = self.log.subroutines[subroutine_pc]
        if subroutine.has_asserted_state_change and (
            instruction.stopped_execution or instruction.is_return
        ):
            # Subroutine with asserted return state.
            state_expr = subroutine.state_change.state_expr
            tokens.append(Token(TokenType.ASSERTION, state_expr))
            tokens.append(Token(TokenType.NEWLINE, "\n"))

        elif instruction.pc in self.log.instruction_assertions:
            # Instruction with asserted state change.
            state_expr = self.log.instruction_assertions[instruction.pc].state_expr
            tokens.append(Token(TokenType.ASSERTION, state_expr))
            tokens.append(Token(TokenType.NEWLINE, "\n"))

        elif instruction.stopped_execution:
            # Unknown state.
            tokens.append(Token(TokenType.UNKNOWN_STATE, instruction.state_change))
            tokens.append(Token(TokenType.NEWLINE, "\n"))

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

            # Stack manipulation.
            elif len(words) == 3 and words[0:3] == "; Stack manipulation".split():
                # Could be the beginning of a new instruction.
                if tokens[-1][-2].typ != TokenType.LABEL:
                    tokens.append([])
                tokens[-1].append(Token(TokenType.STACK_MANIPULATION))

            # Instruction line.
            elif words[0].upper() in Op.__members__:
                # Could be the beginning of a new instruction.
                if tokens[-1][-2].typ not in (
                    TokenType.LABEL,
                    TokenType.STACK_MANIPULATION,
                ):
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
                    raise ParserError("Missing comment section.", line_n)
                tokens[-1].append(Token(TokenType.PC, words[i + 1]))
                try:
                    comment = line.split("|", maxsplit=1)[1].strip()
                except IndexError:
                    raise ParserError("Expected | before comment.", line_n)
                tokens[-1].append(Token(TokenType.COMMENT, comment))

            # Assertion/state line.
            elif words[0] == ";":
                if words[1:4] == "Asserted state change:".split():
                    tokens[-1].append(Token(TokenType.ASSERTION, words[4]))
                elif words[1:7] == "Unknown state. Last known state change:".split():
                    tokens[-1].append(Token(TokenType.UNKNOWN_STATE, words[7]))
            else:
                raise ParserError("Unable to parse line.", line_n)

            # Signal end of line.
            tokens[-1].append(Token(TokenType.NEWLINE, "\n"))
            line_n += 1

        return tokens


class DisassemblyContainer(Disassembly):
    HEADER = ";; ========================================\n"

    def __init__(self, log: Log, subroutines: Iterable[Subroutine]):
        super().__init__(next(iter(subroutines)))
        self.disassemblies = [Disassembly(sub) for sub in subroutines]

    def edit(self) -> None:
        # Save the subroutines' disassembly in a temporary file.
        original_tokens: List[List[List[Token]]] = []
        with NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
            for disassembly in self.disassemblies:
                f.write(self.HEADER)
                text, tokens = disassembly._get_text()
                original_tokens.append(tokens)
                f.write(text)
                f.write("\n\n")
            filename = f.name

        # Edit the file in an editor.
        check_call([*os.environ["EDITOR"].split(), filename])
        new_text = open(filename).read()
        os.remove(filename)

        global_renames: Dict[str, str] = {}
        subroutine_texts = new_text.split(self.HEADER)

        for i, disassembly in enumerate(self.disassemblies):
            new_tokens = disassembly._text_to_tokens(subroutine_texts[i + 1])
            renames = disassembly._apply_changes(original_tokens[i], new_tokens)

            for old, new in renames.items():
                if global_renames.get(old, new) != new:
                    raise ParserError(
                        'Ambiguous label change: "{}" -> "{}".'.format(old, new)
                    )
                global_renames[old] = new

        apply_renames(self.log, global_renames)


class SubroutineDisassembly(DisassemblyContainer):
    def __init__(self, subroutine: Subroutine):
        super().__init__(subroutine.log, [subroutine])


class ROMDisassembly(DisassemblyContainer):
    def __init__(self, log: Log):
        super().__init__(log, log.subroutines.values())
