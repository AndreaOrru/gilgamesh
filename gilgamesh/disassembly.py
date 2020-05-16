import os
from itertools import zip_longest
from subprocess import check_call
from tempfile import NamedTemporaryFile
from typing import Dict, Iterable, List, Tuple
from uuid import uuid4

from gilgamesh.errors import ParserError
from gilgamesh.instruction import Instruction
from gilgamesh.log import Log
from gilgamesh.opcodes import Op
from gilgamesh.parser import EDITABLE_TOKENS, HEADER_TOKENS, Parser, Token
from gilgamesh.parser import TokenType as T
from gilgamesh.state import StateChange
from gilgamesh.subroutine import Subroutine


class Disassembly:
    SEPARATOR_LINE = ";" + ("-" * 40)

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

    def _instruction_to_tokens(self, instruction: Instruction) -> List[Token]:
        """Convert an instruction into a list of token which describes it."""
        tokens = []

        def add(*args) -> None:
            tokens.append(Token(*args))

        def add_line(*args) -> None:
            add(*args)
            tokens.append(Token(T.NEWLINE))

        # Stack manipulation.
        if instruction.does_manipulate_stack:
            add_line(T.STACK_MANIPULATION_HEADER)

        # Label.
        subroutine_pc = instruction.subroutine
        label = self.log.get_label(instruction.pc, subroutine_pc)
        if label:
            add_line(T.LABEL, label)
        # Operation + Operand.
        tokens.append(Token(T.OPERATION, instruction.name))
        if instruction.argument_alias:
            add(T.OPERAND_LABEL, instruction.argument_alias)
        else:
            add(T.OPERAND, instruction.argument_string)
        # PC + Comment.
        add(T.PC, "${:06X}".format(instruction.pc))
        comment = self.log.comments.get(instruction.pc, "")
        add_line(T.COMMENT, comment)

        # Asserted or unknown state.
        state_change, assertion_type = self._get_unknown_state(instruction)
        if state_change == "unknown" or assertion_type != "none":
            if state_change == "unknown":
                add_line(T.UNKNOWN_STATE_HEADER)
            else:
                add_line(T.ASSERTED_STATE_HEADER)
            add_line(T.LAST_KNOWN_STATE, instruction.state_change)
            add_line(T.SEPARATOR_LINE)
            add_line(T.ASSERTION_TYPE, assertion_type)
            add_line(T.ASSERTION, state_change)
            add_line(T.SEPARATOR_LINE)
        # Normal return state.
        elif instruction.is_return:
            add_line(T.KNOWN_STATE_HEADER)
            add_line(T.KNOWN_STATE, state_change)
            add_line(T.SEPARATOR_LINE)

        return tokens

    @classmethod
    def _text_to_tokens(self, text: str) -> List[List[Token]]:
        """Parse a subroutines's disassembly into a list of lists of tokens."""

        p = Parser(text)
        while p.line_idx < len(p.lines):
            # Empty line.
            if not p.line:
                p.add_line()

            # Label line.
            elif len(p.words) == 1 and p.line[-1] == ":":
                p.add_instr()
                p.add_line(T.LABEL, p.line[:-1])

            # Stack manipulation.
            elif p.maybe_match_line(self.string(T.STACK_MANIPULATION_HEADER)):
                p.add_instr()
                p.add_line(T.STACK_MANIPULATION_HEADER)

            # Known return state.
            elif p.maybe_match_line(self.string(T.KNOWN_STATE_HEADER)):
                p.add_line(T.KNOWN_STATE_HEADER)
                state_expr = p.match_part(self.string(T.KNOWN_STATE))
                p.add_line(T.KNOWN_STATE, state_expr)
                p.match_line(T.SEPARATOR_LINE, self.SEPARATOR_LINE)

            # Unknown or asserted (previously unknown) state.
            elif p.maybe_match_line(
                self.string(T.UNKNOWN_STATE_HEADER)
            ) or p.maybe_match_line(self.string(T.ASSERTED_STATE_HEADER)):
                if p.maybe_match_line(self.string(T.ASSERTED_STATE_HEADER)):
                    p.add_line(T.ASSERTED_STATE_HEADER)
                else:
                    p.add_line(T.UNKNOWN_STATE_HEADER)

                # TODO: validate the state_expr.
                state_expr = p.match_part(self.string(T.LAST_KNOWN_STATE))
                p.add_line(T.LAST_KNOWN_STATE, state_expr)
                p.match_line(T.SEPARATOR_LINE, self.SEPARATOR_LINE)

                # TODO: validate the assertion type.
                assertion_type = p.match_part(self.string(T.ASSERTION_TYPE))
                p.add_line(T.ASSERTION_TYPE, assertion_type)

                # TODO: validate the state_expr.
                assertion = p.match_part(self.string(T.ASSERTION))
                p.add_line(T.ASSERTION, assertion)
                p.match_line(T.SEPARATOR_LINE, self.SEPARATOR_LINE)

            # Instruction line.
            elif p.words[0].upper() in Op.__members__:
                p.maybe_add_instr()
                p.add(T.OPERATION, p.words[0].lower())
                i = 1

                # Operand section.
                if p.words[i] == ";":
                    p.add(T.OPERAND, "")
                else:
                    word = p.words[i]
                    if ("a" == word) or ("$" in word) or ("," in word):
                        p.add(T.OPERAND, word)
                    elif word.isidentifier() or (
                        word[0] == "." and word[1:].isidentifier()
                    ):
                        p.add(T.OPERAND_LABEL, word)
                    i += 1

                # Comment section.
                if p.words[i] != ";":
                    raise ParserError("Missing comment section.", p.line_n)
                p.add(T.PC, p.words[i + 1])
                try:
                    comment = p.line.split("|", maxsplit=1)[1].strip()
                except IndexError:
                    raise ParserError("Expected | before comment.", p.line_n)
                p.add_line(T.COMMENT, comment)

            else:
                raise ParserError("Unable to parse line.", p.line_n)

        return p.tokens

    @classmethod
    def _instruction_tokens_to_text(self, tokens: List[Token], html=False) -> str:
        """Generate HTML or plain text from the list of tokens of an instruction."""

        fmt = lambda s, c: f"<{c}>{s}</{c}>" if html else s  # noqa: E731
        s = lambda t: self.string(t, html)  # noqa: E731

        r = []
        for t in tokens:
            if t.typ == T.NEWLINE:
                r.append("\n")
            elif t.typ == T.LABEL:
                r.append("{}:".format(fmt(t.val, "red")))
            elif t.typ == T.OPERATION:
                r.append(fmt(f"  {t.val:4}", "green"))
            elif t.typ == T.OPERAND:
                r.append(f"{t.val:25}")
            elif t.typ == T.OPERAND_LABEL:
                r.append(fmt(f"{t.val:25}", "red"))
            elif t.typ == T.PC:
                r.append(fmt(f" ; {t.val}", "grey"))
            elif t.typ == T.COMMENT:
                r.append(fmt(f" | {t.val}", "grey"))
            elif t.typ in HEADER_TOKENS:
                r.append(f"  {s(t.typ)}")
            elif t.typ in (T.KNOWN_STATE, T.LAST_KNOWN_STATE):
                r.append(f'  {s(t.typ)} {fmt(t.val, "green")}')
            elif t.typ in (T.ASSERTION, T.ASSERTION_TYPE):
                if t.typ == T.ASSERTION:
                    color = "red" if t.val == "unknown" else "magenta"
                elif t.typ == T.ASSERTION_TYPE:
                    color = "red" if t.val == "none" else "magenta"
                r.append(f"  {s(t.typ)} {fmt(t.val, color)}")
        return "".join(r)

    def _apply_changes(
        self, original_tokens: List[List[Token]], new_tokens: List[List[Token]]
    ) -> Dict[str, str]:
        """Compare a collection of tokens describing a subroutine, with a new one
        with potentially updated content. Apply changes where possible."""
        line_n = 2  # First line is the separator.
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
        """Compare a collection of tokens describing an instruction, with a new one
        with potentially updated content. Apply changes where possible."""
        for orig, new in zip_longest(original_tokens, new_tokens):
            # Count lines.
            if new and new.typ == T.NEWLINE:
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
            elif orig.typ == T.PC:
                pc = int(orig.val[1:], 16)

            # Assertion type.
            elif orig.typ == T.ASSERTION_TYPE:
                orig_assert_type = orig.val
                new_assert_type = new.val
                assertion_type_changed = orig_assert_type != new_assert_type
            # Assertion.
            elif orig.typ == T.ASSERTION:
                assertion_changed = orig.val != new.val
                anything_changed = assertion_type_changed or assertion_changed
                state_change = StateChange.from_state_expr(new.val)
                if anything_changed and state_change.unknown:
                    raise ParserError("Invalid assertion state.", line_n)
                if assertion_type_changed:
                    if orig_assert_type == "instruction":
                        self.log.deassert_instruction_state_change(pc)
                    elif orig_assert_type == "subroutine":
                        self.log.deassert_subroutine_state_change(self.subroutine.pc)
                if anything_changed:
                    if new_assert_type == "instruction":
                        self.log.assert_instruction_state_change(pc, state_change)
                    elif new_assert_type == "subroutine":
                        self.log.assert_subroutine_state_change(
                            self.subroutine, state_change
                        )

            # Comments.
            elif orig.typ == T.COMMENT and orig.val != new.val:
                if new.val:
                    self.log.comments[pc] = new.val
                else:
                    self.log.comments.pop(pc, None)
            # Labels.
            elif orig.typ in (T.LABEL, T.OPERAND_LABEL) and orig.val != new.val:
                if renamed_labels.get(orig.val, new.val) != new.val:
                    raise ParserError(
                        f'Ambiguous label change: "{orig.val}" -> "{new.val}".', line_n,
                    )
                renamed_labels[orig.val] = new.val
        # Return the updated line index.
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

    @classmethod
    def string(self, t: T, html=False) -> str:
        def fmt(s: str, color=None) -> str:
            if html and color:
                s = f"<{color}>{s}</{color}>"
            return s

        def center(s: str, color=None) -> str:
            n = self.SEPARATOR_LINE.count("-")
            left = (n // 2) - (len(s) // 2)
            right = n - (left + len(s))
            s = fmt(s, color)
            return fmt(";" + ("-" * left) + s + ("-" * right), "grey")

        if t == T.SEPARATOR_LINE:
            return fmt(self.SEPARATOR_LINE, "grey")
        elif t == T.STACK_MANIPULATION_HEADER:
            return center("[STACK MANIPULATION]")
        elif t == T.ASSERTED_STATE_HEADER:
            return center("[ASSERTED STATE]", "magenta")
        elif t == T.KNOWN_STATE_HEADER:
            return center("[KNOWN STATE]", "green")
        elif t == T.UNKNOWN_STATE_HEADER:
            return center("[UNKNOWN STATE]", "red")

        elif t == T.KNOWN_STATE:
            return fmt("; Known return state change:", "grey")
        elif t == T.LAST_KNOWN_STATE:
            return fmt("; Last known state change:", "grey")

        elif t == T.ASSERTION_TYPE:
            return fmt("; ASSERTION TYPE:", "grey")
        elif t == T.ASSERTION:
            return fmt("; ASSERTED STATE CHANGE:", "grey")

        breakpoint()
        assert False

    def _get_unknown_state(self, instruction: Instruction):
        # TODO: what if there are both subroutine and instruction assertions?
        subroutine = self.log.subroutines[instruction.subroutine]

        assertion_type = "none"
        state_change = instruction.state_change

        # Subroutine assertion.
        if subroutine.has_asserted_state_change and (
            instruction.stopped_execution or instruction.is_return
        ):
            assertion = self.log.subroutine_assertions.get(subroutine.pc)
            state_change = (
                assertion.state_expr if assertion else instruction.state_change
            )
            if assertion:
                assertion_type = "subroutine"
        # Instruction assertion or unknown state.
        elif (
            instruction.pc in self.log.instruction_assertions
            or instruction.stopped_execution
        ):
            assertion = self.log.instruction_assertions.get(instruction.pc)
            state_change = assertion.state_expr if assertion else "unknown"
            if assertion:
                assertion_type = "instruction"

        return state_change, assertion_type


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


class DisassemblyContainer(Disassembly):
    HEADER = ";;" + ("=" * 41) + "\n"

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
                f.write("\n\n\n")
            filename = f.name

        # Edit the file in an editor.
        check_call([*os.environ["EDITOR"].split(), filename])
        new_text = open(filename).read()
        os.remove(filename)

        global_renames: Dict[str, str] = {}
        subroutine_texts = new_text.split(self.HEADER)

        # Apply all the changes local to the individual subroutines.
        for i, disassembly in enumerate(self.disassemblies):
            new_tokens = disassembly._text_to_tokens(subroutine_texts[i + 1])
            renames = disassembly._apply_changes(original_tokens[i], new_tokens)

            # Gather global renames.
            for old, new in renames.items():
                if global_renames.get(old, new) != new:
                    raise ParserError(f'Ambiguous label change: "{old}" -> "{new}".')
                global_renames[old] = new

        # Apply the global renames.
        apply_renames(self.log, global_renames)


class SubroutineDisassembly(DisassemblyContainer):
    def __init__(self, subroutine: Subroutine):
        super().__init__(subroutine.log, [subroutine])


class ROMDisassembly(DisassemblyContainer):
    def __init__(self, log: Log):
        super().__init__(log, log.subroutines.values())
