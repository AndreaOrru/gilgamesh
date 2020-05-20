from itertools import zip_longest
from typing import Dict, List, Optional, Set, Tuple

from methodtools import lru_cache  # type: ignore

from gilgamesh.disassembly.parser import (
    EDITABLE_TOKENS,
    EQUIVALENT_TOKENS,
    HEADER_TOKENS,
    Parser,
    Token,
)
from gilgamesh.disassembly.parser import TokenType as T
from gilgamesh.disassembly.renames import apply_local_renames
from gilgamesh.errors import ParserError
from gilgamesh.snes.instruction import Instruction, StackManipulation
from gilgamesh.snes.opcodes import Op
from gilgamesh.snes.state import StateChange
from gilgamesh.subroutine import Subroutine


class Disassembly:
    SEPARATOR_LINE = ";" + ("-" * 40)

    def __init__(
        self, subroutine: Subroutine, highlighted_labels: Optional[Set[str]] = None,
    ):
        self.log = subroutine.log
        self.subroutine = subroutine
        self.highlighted_labels = highlighted_labels or set()
        self.base_line_n = 1

    def get_html(self) -> str:
        return self._get_text(html=True)[1]

    def get_instruction_html(self, instruction: Instruction, verbose=False) -> str:
        tokens = self._instruction_to_tokens(instruction, verbose)
        return self._instruction_tokens_to_text(tokens, html=True)[1]

    def _get_text(self, html=False) -> Tuple[int, str, List[List[Token]]]:
        n_lines, s, tokens = 0, [], []

        for instruction in self.subroutine.instructions.values():
            instr_tokens = self._instruction_to_tokens(instruction)
            tokens.append(instr_tokens)

            instr_lines, text = self._instruction_tokens_to_text(instr_tokens, html)
            n_lines += instr_lines
            s.append(text)

        return n_lines, "".join(s), tokens

    def _instruction_to_tokens(self, instr: Instruction, verbose=True) -> List[Token]:
        """Convert an instruction into a list of token which describes it."""
        tokens = []

        def add(*args) -> None:
            tokens.append(Token(*args))

        def add_line(*args) -> None:
            add(*args)
            tokens.append(Token(T.NEWLINE))

        # Stack manipulation.
        if verbose and instr.stack_manipulation != StackManipulation.NONE:
            if instr.stack_manipulation == StackManipulation.CAUSES_UNKNOWN_STATE:
                add_line(T.FATAL_STACK_MANIPULATION_HEADER)
            else:
                add_line(T.STACK_MANIPULATION_HEADER)

        # Label.
        label = self.log.get_label(instr.pc, instr.subroutine_pc)
        if label:
            if instr.pc in self.log.jump_table_targets:
                add_line(T.JUMP_TABLE_LABEL, label)
            else:
                add_line(T.LABEL, label)
        # Operation + Operand.
        tokens.append(Token(T.OPERATION, instr.name))
        if instr.argument_alias:
            if instr.argument_alias in self.highlighted_labels:
                add(T.HIGHLIGHTED_OPERAND_LABEL, instr.argument_alias)
            elif instr.pc in self.log.jump_table_targets:
                add(T.JUMP_TABLE_OPERAND_LABEL, instr.argument_alias)
            else:
                add(T.OPERAND_LABEL, instr.argument_alias)
        else:
            add(T.OPERAND, instr.argument_string)
        # PC + Comment.
        add(T.PC, "${:06X}".format(instr.pc))
        comment = self.log.comments.get(instr.pc, "")
        add_line(T.COMMENT, comment)

        # Don't show extra information on state in non-verbose mode.
        if not verbose:
            return tokens

        # Jump table.
        if instr.is_jump_table:
            add_line(T.JUMP_TABLE_HEADER)
            for target in self.log.jump_assertions[instr.pc]:
                add_line(
                    T.JUMP_TABLE_ENTRY, self.log.get_label(target, self.subroutine.pc)
                )
            add_line(T.SEPARATOR_LINE)

        # Asserted or unknown state.
        state_change, assertion_type = self._get_unknown_state(instr)
        if assertion_type != "none" or state_change == "unknown":
            if state_change == "unknown":
                add_line(T.UNKNOWN_STATE_HEADER)
            else:
                add_line(T.ASSERTED_STATE_HEADER)
            add_line(T.LAST_KNOWN_STATE, str(instr.state_change_before))
            add_line(T.SEPARATOR_LINE)
            add_line(T.ASSERTION_TYPE, assertion_type)
            add_line(T.ASSERTION, state_change)
            add_line(T.SEPARATOR_LINE)
        # Normal return state.
        elif instr.is_return:
            add_line(T.KNOWN_STATE_HEADER)
            add_line(T.KNOWN_STATE, state_change)
            add_line(T.SEPARATOR_LINE)

        return tokens

    def _text_to_tokens(self, text: str) -> List[List[Token]]:
        """Parse a subroutines's disassembly into a list of lists of tokens."""

        p = Parser(text, self.base_line_n)
        while p.line_idx < len(p.lines):
            # Empty line.
            if not p.line:
                p.add_line()

            # Label line.
            elif len(p.words) == 1 and p.line[-1] == ":":
                p.new_instruction()
                p.add_line(T.LABEL, p.line[:-1])

            # Stack manipulation.
            elif p.maybe_match_line(self.string(T.STACK_MANIPULATION_HEADER)):
                p.new_instruction()
                p.add_line(T.STACK_MANIPULATION_HEADER)

            # Known return state.
            elif p.maybe_match_line(self.string(T.KNOWN_STATE_HEADER)):
                p.add_line(T.KNOWN_STATE_HEADER)
                p.add_line_rest(T.KNOWN_STATE, after=self.string(T.KNOWN_STATE))
                p.match_line(T.SEPARATOR_LINE, self.SEPARATOR_LINE)

            # Unknown or asserted (previously unknown) state.
            elif p.maybe_match_line(
                self.string(T.UNKNOWN_STATE_HEADER)
            ) or p.maybe_match_line(self.string(T.ASSERTED_STATE_HEADER)):
                if p.maybe_match_line(self.string(T.ASSERTED_STATE_HEADER)):
                    p.add_line(T.ASSERTED_STATE_HEADER)
                else:
                    p.add_line(T.UNKNOWN_STATE_HEADER)
                # TODO: validate state_expr and assertion_type.
                p.add_line_rest(T.LAST_KNOWN_STATE, self.string(T.LAST_KNOWN_STATE))
                p.match_line(T.SEPARATOR_LINE, self.SEPARATOR_LINE)
                p.add_line_rest(T.ASSERTION_TYPE, after=self.string(T.ASSERTION_TYPE))
                p.add_line_rest(T.ASSERTION, after=self.string(T.ASSERTION))
                p.match_line(T.SEPARATOR_LINE, self.SEPARATOR_LINE)

            # Instruction line.
            elif p.words[0].upper() in Op.__members__:
                p.maybe_new_instruction()
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
    def _instruction_tokens_to_text(
        cls, tokens: List[Token], html=False
    ) -> Tuple[int, str]:
        """Generate HTML or plain text from the list of tokens of an instruction."""
        colorize = lambda s, f, b=None: cls.colorize(s, html, f, b)  # noqa: E731
        string = lambda t: cls.string(t, html)  # noqa: E731

        s, n_lines = [], 0
        for t in tokens:
            if t.typ == T.NEWLINE:
                s.append("\n")
                n_lines += 1
            elif t.typ == T.LABEL:
                s.append(colorize(f"{t.val}:", "red"))
            elif t.typ == T.JUMP_TABLE_LABEL:
                s.append(colorize(f"{t.val}:", "blue"))
            elif t.typ == T.OPERATION:
                s.append(colorize(f"  {t.val:4}", "green"))
            elif t.typ == T.OPERAND:
                s.append(f"{t.val:25}")
            elif t.typ == T.OPERAND_LABEL:
                s.append(colorize(f"{t.val:25}", "red"))
            elif t.typ == T.JUMP_TABLE_OPERAND_LABEL:
                s.append(colorize(f"{t.val:25}", "blue"))
            elif t.typ == T.HIGHLIGHTED_OPERAND_LABEL:
                v = colorize(t.val, "black", "red")
                s.append(v + (25 - len(t.val)) * " ")
            elif t.typ == T.PC:
                s.append(colorize(f" ; {t.val}", "grey"))
            elif t.typ == T.COMMENT:
                s.append(colorize(f" | {t.val}", "grey"))
            elif t.typ in HEADER_TOKENS:
                s.append(f"  {string(t.typ)}")
            elif t.typ in (T.KNOWN_STATE, T.LAST_KNOWN_STATE):
                s.append(f'  {string(t.typ)} {colorize(t.val, "green")}')
            elif t.typ == T.ASSERTION_TYPE:
                color = "red" if t.val == "none" else "magenta"
                s.append(f"  {string(t.typ)} {colorize(t.val, color)}")
            elif t.typ == T.ASSERTION:
                color = "red" if t.val == "unknown" else "magenta"
                s.append(f"  {string(t.typ)} {colorize(t.val, color)}")
            elif t.typ == T.JUMP_TABLE_ENTRY:
                s.append(f'  {string(t.typ)} {colorize(t.val, "grey")}')

        return n_lines, "".join(s)

    def _apply_changes(
        self, original_tokens: List[List[Token]], new_tokens: List[List[Token]]
    ) -> Dict[str, str]:
        """Compare a collection of tokens describing a subroutine, with a new one
        with potentially updated content. Apply changes where possible."""
        line_n = self.base_line_n
        renamed_labels: Dict[str, str] = {}

        for orig_instr_tokens, new_instr_tokens in zip_longest(
            original_tokens, new_tokens
        ):
            if (orig_instr_tokens is None) or (new_instr_tokens is None):
                raise ParserError("Added or deleted an instruction.", line_n)
            line_n = self._apply_instruction_changes(
                line_n, orig_instr_tokens, new_instr_tokens, renamed_labels
            )

        global_renames = apply_local_renames(self.subroutine, renamed_labels)
        return global_renames

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
            # Handle equivalent tokens.
            if orig:
                orig.typ = EQUIVALENT_TOKENS.get(orig.typ, orig.typ)

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
                state_change = StateChange.from_expr(new.val)
                if anything_changed and state_change.unknown:
                    raise ParserError("Invalid assertion state.", line_n)
                if assertion_type_changed:
                    if "instruction".startswith(orig_assert_type):
                        self.log.deassert_instruction_state_change(pc)
                    elif "subroutine".startswith(orig_assert_type):
                        self.log.deassert_subroutine_state_change(
                            self.subroutine.pc, pc
                        )
                if anything_changed:
                    if new_assert_type == "":
                        continue
                    elif "instruction".startswith(new_assert_type):
                        self.log.assert_instruction_state_change(pc, state_change)
                    elif "subroutine".startswith(new_assert_type):
                        self.log.assert_subroutine_state_change(
                            self.subroutine, pc, state_change
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

    def _get_unknown_state(self, i: Instruction) -> Tuple[str, str]:
        if i.asserted_subroutine_state_change:
            assertion_type = "subroutine"
            state_change = str(i.asserted_subroutine_state_change)
        elif i.has_asserted_state_change:
            assertion_type = "instruction"
            state_change = str(i.state_change_after)
        else:
            assertion_type = "none"
            state_change = str(i.state_change_after)
        return state_change, assertion_type

    @staticmethod
    def colorize(
        s: str, html=False, fg: Optional[str] = None, bg: Optional[str] = None
    ) -> str:
        if html and fg:
            bg = f"ansi{bg}" if bg and not bg.startswith("ansi") else bg
            return "<{}{}>{}</{}>".format(fg, f' bg="{bg}"' if bg else "", s, fg)
        return s

    @lru_cache(None)
    @classmethod
    def center(cls, s: str, html=False, color: Optional[str] = None) -> str:
        n = cls.SEPARATOR_LINE.count("-")
        left = (n // 2) - (len(s) // 2)
        right = n - (left + len(s))

        s = cls.colorize(s, html, color)
        result = ";" + ("-" * left) + s + ("-" * right)
        return cls.colorize(result, html, "grey")

    @classmethod
    def string(cls, t: T, html=False) -> str:
        colorize = lambda s, c: cls.colorize(s, html, c)  # noqa: E731
        center = lambda s, c=None: cls.center(s, html, c)  # noqa: E731

        if t == T.SEPARATOR_LINE:
            return colorize(cls.SEPARATOR_LINE, "grey")
        elif t == T.STACK_MANIPULATION_HEADER:
            return center("[STACK MANIPULATION]")
        elif t == T.FATAL_STACK_MANIPULATION_HEADER:
            return center("[STACK MANIPULATION]", "red")
        elif t == T.ASSERTED_STATE_HEADER:
            return center("[ASSERTED STATE]", "magenta")
        elif t == T.JUMP_TABLE_HEADER:
            return center("[JUMP TABLE]", "blue")
        elif t == T.KNOWN_STATE_HEADER:
            return center("[KNOWN STATE]", "green")
        elif t == T.UNKNOWN_STATE_HEADER:
            return center("[UNKNOWN STATE]", "red")

        elif t == T.KNOWN_STATE:
            return colorize("; Known return state change:", "grey")
        elif t == T.LAST_KNOWN_STATE:
            return colorize("; Last known state change:", "grey")

        elif t == T.ASSERTION_TYPE:
            return colorize("; ASSERTION TYPE:", "grey")
        elif t == T.ASSERTION:
            return colorize("; ASSERTED STATE CHANGE:", "grey")

        elif t == T.JUMP_TABLE_ENTRY:
            return colorize(";", "grey")

        assert False
