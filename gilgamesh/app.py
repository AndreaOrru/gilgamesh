import pickle
from copy import deepcopy
from os import path
from typing import Any, Callable, Dict, List, Optional, Tuple

from prompt_toolkit import HTML  # type: ignore

from gilgamesh.disassembly import ROMDisassembly, SubroutineDisassembly
from gilgamesh.errors import GilgameshError
from gilgamesh.log import Log
from gilgamesh.repl import Repl, argument, command, print_error, print_html
from gilgamesh.snes.instruction import Instruction
from gilgamesh.snes.opcodes import Op, descriptions
from gilgamesh.snes.rom import ROM
from gilgamesh.snes.state import State, StateChange
from gilgamesh.subroutine import Subroutine

HISTORY_FILE = "~/.local/share/gilgamesh/history.log"


class App(Repl):
    def __init__(self, rom_path: str):
        super().__init__(history_file=HISTORY_FILE)

        self.rom = ROM(rom_path)
        self.log = Log(self.rom)

        # The subroutine currently under analysis.
        self.subroutine_pc: Optional[int] = None

        # Try to automatically load an existing analysis.
        if not self._do_load():
            self.log.analyze()

    @property
    def subroutine(self) -> Optional[Subroutine]:
        if self.subroutine_pc is None:
            return None
        if self.subroutine_pc not in self.log.subroutines:
            self.subroutine_pc = None
            return None
        return self.log.subroutines[self.subroutine_pc]

    @subroutine.setter
    def subroutine(self, subroutine: Subroutine) -> None:
        self.subroutine_pc = subroutine.pc

    @property
    def prompt(self) -> str:
        color = "red" if self.log.dirty else "yellow"
        prompt = "*>" if self.log.dirty else ">"
        if self.subroutine is None:
            return HTML("<{}>{}</{}> ".format(color, prompt, color))
        # Show the current subroutine in the prompt if there's one.
        return HTML(
            "<{}>[{}]{}</{}> ".format(color, self.subroutine.label, prompt, color)
        )

    def complete_opcode(self) -> List[str]:
        return [op.lower() for op in Op.__members__]

    def complete_subroutine(self) -> List[str]:
        return sorted(self.log.subroutines_by_label.keys())

    def complete_label(self) -> List[str]:
        subroutines = self.complete_subroutine()
        if not self.subroutine:
            return subroutines
        local_labels = sorted(f".{x}" for x in self.subroutine.local_labels.keys())
        return local_labels + subroutines

    @command()
    def do_analyze(self) -> None:
        """Run the analysis on the ROM."""
        n_suspect = self.log.n_suspect_subroutines
        self.log.analyze()

        new_suspect = self.log.n_suspect_subroutines - n_suspect
        if new_suspect > 0:
            print_html(
                f"<yellow>Discovered {new_suspect} new suspect subroutine(s).</yellow>\n"  # noqa
            )

    @command(container=True)
    def do_assert(self) -> None:
        """Define known processor states for instructions and subroutines."""
        ...

    @command()
    @argument("label_or_pc", complete_label)
    @argument("state_expr")
    def do_assert_instruction(self, label_or_pc: str, state_expr: str) -> None:
        """Define how the processor state changes after an instruction's execution.

        STATE_EXPR can accept the following values:
          - "none"         -> The subroutine does not change the state.
          - "m=0" or "m=1" -> The subroutine changes the state of m to 0 or 1.
          - "x=0" or "x=1" -> The subroutine changes the state of x to 0 or 1.
          - "m=0,x=0"      -> The subroutine changes the state of m to 0 and x to 0.
          - "m=0,x=1"      -> The subroutine changes the state of m to 0 and x to 1.
          - "m=1,x=0"      -> The subroutine changes the state of m to 1 and x to 0.
          - "m=1,x=1"      -> The subroutine changes the state of m to 1 and x to 1."""
        state_change = StateChange.from_expr(state_expr)
        instruction_pc = self._label_to_pc(label_or_pc)
        self.log.assert_instruction_state_change(instruction_pc, state_change)

    @command()
    @argument("label_or_pc", complete_label)
    @argument("state_expr")
    def do_assert_subroutine(self, label_or_pc: str, state_expr: str) -> None:
        """Define a known processor return state for a given subroutine.

        STATE_EXPR can accept the following values:
          - "none"         -> The subroutine does not change the state.
          - "m=0" or "m=1" -> The subroutine changes the state of m to 0 or 1.
          - "x=0" or "x=1" -> The subroutine changes the state of x to 0 or 1.
          - "m=0,x=0"      -> The subroutine changes the state of m to 0 and x to 0.
          - "m=0,x=1"      -> The subroutine changes the state of m to 0 and x to 1.
          - "m=1,x=0"      -> The subroutine changes the state of m to 1 and x to 0.
          - "m=1,x=1"      -> The subroutine changes the state of m to 1 and x to 1."""
        if not self.subroutine:
            raise GilgameshError("No selected subroutine.")
        # TODO: check that pc is an instruction inside the subroutine.
        instr_pc = self._label_to_pc(label_or_pc)
        state_change = StateChange.from_expr(state_expr)
        self.log.assert_subroutine_state_change(self.subroutine, instr_pc, state_change)

    @command()
    @argument("label_or_pc", complete_label)
    @argument("comment")
    def do_comment(self, label_or_pc: str, comment="") -> None:
        """Add comment to an instruction.
        If no comment is specified, delete the existing comment."""
        pc = self._label_to_pc(label_or_pc)
        if comment:
            self.log.comments[pc] = comment
        else:
            self.log.comments.pop(pc, None)

    @command()
    def do_debug(self) -> None:
        """Debug Gilgamesh itself."""
        breakpoint()

    @command(container=True)
    def do_deassert(self) -> None:
        """Remove previously defined assertions."""
        ...

    @command()
    @argument("label_or_pc", complete_label)
    def do_deassert_instruction(self, label_or_pc: str) -> None:
        """Remove previously defined instruction assertions."""
        pc = self._label_to_pc(label_or_pc)
        self.log.deassert_instruction_state_change(pc)

    @command()
    @argument("label_or_pc", complete_label)
    def do_deassert_subroutine(self, label_or_pc: str) -> None:
        """Remove previously defined subroutine assertions."""
        if self.subroutine_pc is None:
            raise GilgameshError("No selected subroutine.")
        instr_pc = self._label_to_pc(label_or_pc)
        self.log.deassert_subroutine_state_change(self.subroutine_pc, instr_pc)

    @command()
    @argument("opcode", complete_opcode)
    def do_describe(self, opcode: str):
        """Describe an opcode."""
        op = Op.__members__[opcode.upper()]
        description = descriptions[op] + "\n"
        print_html(description)

    @command()
    def do_disassembly(self) -> None:
        """Show disassembly of selected subroutine."""
        if not self.subroutine:
            raise GilgameshError("No selected subroutine.")
        disassembly = SubroutineDisassembly(self.subroutine)
        print_html(disassembly.get_html())

    @command()
    def do_edit(self) -> None:
        """Interactively edit the subroutine(s) using an external editor."""
        if not self.subroutine:
            raise GilgameshError("No selected subroutine.")
        disassembly = SubroutineDisassembly(self.subroutine)
        disassembly.edit()
        if self.log.dirty:
            self.do_analyze()

    @command()
    def do_edit_all(self) -> None:
        """Interactively edit all subroutines using an external editor."""
        disassembly = ROMDisassembly(self.log)
        disassembly.edit()
        if self.log.dirty:
            self.do_analyze()

    @command()
    @argument("pc")
    @argument("name")
    @argument("state_expr")
    def do_entrypoint(self, pc: str, name: str, state_expr: str) -> None:
        """Add an entry point to the analysis.

        STATE_EXPR can accept the following values:
          - "m=0,x=0" -> The subroutine changes the state of m to 0 and x to 0.
          - "m=0,x=1" -> The subroutine changes the state of m to 0 and x to 1.
          - "m=1,x=0" -> The subroutine changes the state of m to 1 and x to 0.
          - "m=1,x=1" -> The subroutine changes the state of m to 1 and x to 1."""
        if not pc.startswith("$"):
            raise GilgameshError("Please specify a valid address.")
        pc_int = self._label_to_pc(pc)
        state = State.from_expr(state_expr)
        self.log.add_entry_point(pc_int, name, state)

    @command(container=True)
    def do_jumptable(self) -> None:
        """Manage jump tables."""
        ...

    @command()
    @argument("caller_pc", complete_label)
    @argument("range_or_target_pc")
    def do_jumptable_add(self, caller_pc: str, range_or_target_pc: str) -> None:
        """Add a jump table entry."""
        self._do_jumptable_op(self.log.assert_jump, caller_pc, range_or_target_pc)

    @command()
    @argument("caller_pc", complete_label)
    @argument("range_or_target_pc")
    def do_jumptable_delete(self, caller_pc: str, range_or_target_pc: str) -> None:
        """Remove a jump table entry."""
        self._do_jumptable_op(self.log.deassert_jump, caller_pc, range_or_target_pc)

    @command()
    @argument("caller_pc", complete_label)
    @argument("range_expr")
    def do_jumptable_preview(self, caller_pc: str, range_expr: str) -> None:
        """Preview the branches of a jumptable without affecting the analysis."""

        def gather_targets(caller_pc: int, target_pc: int, x: int) -> None:
            target_pcs.append(target_pc)

        target_pcs: List[int] = []
        self._do_jumptable_op(gather_targets, caller_pc, range_expr)

        caller_pc_int = self._label_to_pc(caller_pc)
        caller = self.log.any_instruction(caller_pc_int)
        disassemblies = self._print_preview_many(target_pcs, str(caller.state))
        separator = "\n\n\n<grey>{}</grey>".format(ROMDisassembly.HEADER)
        print_html(separator.join(disassemblies))

    @command()
    @argument("caller_pc", complete_label)
    def do_jumptable_complete(self, caller_pc: str) -> None:
        """Flag a jumptable as completely explored."""
        caller_pc_int = self._label_to_pc(caller_pc)
        self.log.complete_jump_tables.add(caller_pc_int)

    def _do_jumptable_op(self, op: Callable, caller_pc: str, range_or_target_pc: str):
        caller_pc_int = self._label_to_pc(caller_pc)
        if range_or_target_pc.startswith("$"):
            target_pc = self._label_to_pc(range_or_target_pc)
            op(caller_pc_int, target_pc)
        else:
            caller = self.log.any_instruction(caller_pc_int)
            assert caller.is_call or caller.is_jump
            assert caller.argument_size == 2
            assert caller.argument is not None

            first, last = self._parse_range(range_or_target_pc)
            for x in range(first, last + 1, 2):
                offset = caller.argument + x
                bank = caller.pc & 0xFF0000
                target_pc = bank | (self.rom.read_word(bank | offset))
                op(caller.pc, target_pc, x)

    @command(container=True)
    def do_list(self) -> None:
        """List various types of entities."""
        ...

    @command()
    def do_list_assertions(self) -> None:
        """List assertions provided by the user.
        If called with no arguments, display all assertions."""
        self.do_list_assertions_subroutines()
        self.do_list_assertions_instructions()

    @command()
    def do_list_assertions_instructions(self) -> None:
        """List all instruction assertions provided by the user."""
        if not self.log.instruction_assertions:
            return

        s = ["<red>ASSERTED INSTRUCTION STATE CHANGES:</red>\n"]
        for pc, change in self.log.instruction_assertions.items():
            subroutines = self.log.instruction_subroutines(pc)
            instruction = self.log.any_instruction(pc)
            disassembly = self._print_instruction(instruction)

            s.append("  <magenta>${:06X}</magenta>  {}-> ".format(pc, disassembly))
            s.append(self._print_state_change(change))
            if subroutines:
                s.append(
                    "    <grey>{}</grey>\n".format(
                        ", ".join(s.label for s in subroutines)
                    )
                )
        print_html("".join(s))

    @command()
    def do_list_assertions_subroutines(self) -> None:
        """List all subroutine assertions provided by the user."""
        self._do_list_assertions_subroutines()

    def _do_list_assertions_subroutines(self, indent=False) -> None:
        if not self.log.subroutine_assertions:
            return

        s = ["<red>ASSERTED SUBROUTINE STATE CHANGES:</red>\n"]
        last_sub = None

        for sub_pc, state_changes in self.log.subroutine_assertions.items():
            subroutine = self.log.subroutines[sub_pc]

            for instr_pc, change in state_changes.items():
                if not last_sub or sub_pc != last_sub.pc:
                    try:
                        sub = "<magenta>{:16}</magenta>".format(subroutine.label + ":")
                    except KeyError:
                        sub = "<red>${:06X}{:5}</red>".format(sub_pc, "")
                    s.append("{}  {}".format("\n" if last_sub else "", sub))
                else:
                    s.append("  {:16}".format(""))

                instruction = subroutine.instructions[instr_pc]
                code = self._print_instruction(instruction)
                s.append(f"  ${instr_pc:06X}  {code}-> ")
                s.append(self._print_state_change(change, show_asserted=False))

                last_sub = subroutine

        print_html("".join(s))

    @command()
    def do_list_subroutines(self) -> None:
        """List subroutines according to various criteria.
        If called with no arguments, display all subroutines.
        Subroutines with unknown return states are shown in red.
        Entry points are shown with a colored background.

        Subroutines can be flagged with various symbols:
          [!] -> Suspect instructions
          [?] -> Stack manipulation
          [*] -> Jump table
          [∞] -> Recursion
          [+] -> Multiple return states
"""
        s = []
        for subroutine in self.log.subroutines.values():
            s.append(self._print_subroutine(subroutine))
        print_html("".join(s))

    @command()
    def do_list_subroutines_unknown(self) -> None:
        """List subroutines with unknown return states.

        Subroutines can be flagged with various symbols:
          [!] -> Suspect instructions
          [?] -> Stack manipulation
          [*] -> Jump table
          [∞] -> Recursion
          [+] -> Multiple return states"""
        s = []
        for subroutine in self.log.subroutines.values():
            if subroutine.has_unknown_return_state:
                s.append(self._print_subroutine(subroutine))
        print_html("".join(s))

    @command()
    def do_load(self) -> None:
        """Load the state of the analysis from a .glm file."""
        if not path.exists(self.rom.glm_path):
            print_error(f'"{self.rom.glm_name}" does not exist.')
        elif self.yes_no_prompt("Are you sure you want to load the saved analysis?"):
            self._do_load()

    def _do_load(self) -> bool:
        try:
            with open(self.rom.glm_path, "rb") as f:
                data = pickle.load(f)
            self.log.load(data)
            self.subroutine_pc = data["current_subroutine"]
        except OSError:
            return False
        else:
            print_html(f'<green>"{self.rom.glm_name}" loaded successfully.</green>\n')
            return True

    @command()
    @argument("addr", complete_label)
    @argument("size", complete_label)
    @argument("step", complete_label)
    def do_memory(self, addr: str, size: str, step: str) -> None:
        """Show an hex view of a region of ROM, starting from
        ADDR and spanning SIZE bytes, in groups of STEP bytes."""

        def build_header(step: int) -> str:
            s = []
            for n in range(0, (16 // step) * step, step):
                s.append(f"{n:02X}")
            s.append("")
            return (" " * ((2 * step) - 1)).join(s)

        addr_int = self._label_to_pc(addr)
        size_int = int(size[1:] if size[0] == "$" else int(size))
        step_int = int(step)
        if step_int > 16:
            raise GilgameshError("Can only build groups up to 16 bytes.")

        s = []
        header = build_header(step_int)
        s += ["<grey>" + (" " * 8) + "│ "]
        s += [header]
        s += ["\n" + ("─" * 8) + "┼" + ("─" * len(header)) + "</grey>\n"]

        colors, color_idx = ["lightgrey", "cyan"], 0
        nl_threshold = (16 // step_int) * step_int

        for i in range(addr_int, addr_int + size_int, step_int):
            if (i - addr_int) % nl_threshold == 0:
                if i - addr_int:
                    s.append("\n")
                s.append("<grey>${:06X} │</grey> ".format(i))

            for j, b in enumerate(self.rom.read(i, step_int)):
                color = (
                    "yellow"
                    if self.log.find_instruction(i + j) is not None
                    else colors[color_idx % len(colors)]
                )
                s.append("<{}>{:02X}</{}>".format(color, b, color))

            s.append(" ")
            color_idx += 1

        s.append("\n")
        print_html("".join(s))

    @command(container=True)
    def do_query(self) -> None:
        """Query the analysis log in various ways."""
        ...

    @command()
    @argument("label_or_pc", complete_label)
    def do_query_instruction(self, label_or_pc: str) -> None:
        """Query various info on an instruction.

        Includes the subroutine it belongs to, and all the possible
        states it was encountered at."""
        pc = self._label_to_pc(label_or_pc)
        instr_ids = self.log.instructions.get(pc, None)
        if instr_ids is None:
            actual_pc = self.log.find_instruction(pc)
            if actual_pc is not None:
                print_html(
                    "The given PC belongs to an instruction that "
                    + f"starts at <red>${actual_pc:06X}</red>.\n"
                )
            return

        s = ["<red>DISASSEMBLY:</red>\n"]
        instruction = self.log.any_instruction(pc)
        s.append("  " + self._print_instruction(instruction))

        s.append("\n\n<red>STATES:</red>\n")
        states = {State(x.p) for x in instr_ids}
        for state in states:
            s.append(f"  <yellow>M</yellow>=<green>{state.m}</green>, ")
            s.append(f"<yellow>X</yellow>=<green>{state.x}</green>\n")

        s.append("\n<red>SUBROUTINES:</red>\n")
        subroutines = {i.subroutine_pc for i in instr_ids}
        for subroutine_pc in sorted(subroutines):
            subroutine = self.log.subroutines[subroutine_pc]
            s.append("  " + self._print_subroutine(subroutine))

        print_html("".join(s))

    @command()
    @argument("label_or_pc", complete_label)
    def do_query_references(self, label_or_pc: str) -> None:
        """Given an address, list the instructions pointing to it."""
        pc = self._label_to_pc(label_or_pc)
        references = self.log.references[pc]

        s, last_sub = [], None
        for instr_pc, sub_pc in references:
            subroutine = self.log.subroutines[sub_pc]
            instruction = subroutine.instructions[instr_pc]
            disassembly = SubroutineDisassembly(subroutine)
            if not last_sub or sub_pc != last_sub.pc:
                s.append(
                    "{}<red>{:16}</red>".format(
                        "\n" if last_sub else "", subroutine.label + ":"
                    )
                )
            else:
                s.append("{:16}".format(""))
            s.append(disassembly.get_instruction_html(instruction))
            last_sub = subroutine
        print_html("".join(s))

    @command()
    @argument("subroutine_or_pc", complete_subroutine)
    def do_query_subroutine(self, subroutine_or_pc: Optional[str] = None) -> None:
        """Show information on a subroutine (such as state and stack trace)."""
        if (subroutine_or_pc is None) and self.subroutine:
            subroutine = self.subroutine
        elif subroutine_or_pc is not None:
            pc = self._label_to_pc(subroutine_or_pc)
            subroutine = self.log.subroutines[pc]
        else:
            raise GilgameshError("No selected subroutine.")

        print_html(self._print_stacktrace(subroutine))
        print_html(self._print_statechange(subroutine))

    def _print_stacktrace(self, sub: Subroutine) -> str:
        """Given a subroutine, show its stack of calling subroutines."""
        s = ["<red>STACK TRACES:</red>"]

        if sub.is_entry_point:
            s.append("  Entry point.\n")
        else:
            for stack_trace in sub.stack_traces:
                ss = []
                for caller_pc in stack_trace:
                    caller = self.log.subroutines[caller_pc]
                    ss.append("  " + self._print_subroutine(caller))
                s.append("".join(ss))

        return "\n".join(s)

    def _print_statechange(self, sub: Subroutine) -> str:
        """Show the change in processor state caused by executing a subroutine."""
        s = ["<red>STATE CHANGES:</red>\n"]
        for instr_pc, change in self.log.subroutines[sub.pc].state_changes.items():
            s.append("  ${:06X}  ".format(instr_pc))
            s.append(self._print_state_change(change))
        return "".join(s)

    @command()
    @argument("old", complete_label)
    @argument("new")
    def do_rename(self, old: str, new: str) -> None:
        """Rename a label or subroutine."""
        self.log.rename_label(old, new, self.subroutine)

    @command()
    def do_reset(self) -> None:
        """Reset the analysis (start from scratch)."""
        if self.yes_no_prompt("Are you sure you want to reset the entire analysis?"):
            self.log.reset()
            self.log.analyze()
            self.subroutine_pc = None

    @command()
    def do_rom(self) -> None:
        """Show general information on the ROM."""
        s = []
        s.append("<green>Title:</green>    {}\n".format(self.rom.title))
        s.append("<green>Type:</green>     {}\n".format(self.rom.type.name))
        s.append("<green>Size:</green>     {} KiB\n".format(self.rom.size // 1024))
        s.append("<green>Vectors:</green>\n")
        s.append("  <green>RESET:</green>  ${:06X}\n".format(self.rom.reset_vector))
        s.append("  <green>NMI:</green>    ${:06X}\n".format(self.rom.nmi_vector))
        print_html("".join(s))

    @command()
    def do_save(self) -> None:
        """Save the state of the analysis to a .glm file."""

        def save() -> None:
            data: Dict[str, Any] = {
                **self.log.save(),
                "current_subroutine": self.subroutine_pc,
            }
            with open(self.rom.glm_path, "wb") as f:
                pickle.dump(data, f, pickle.DEFAULT_PROTOCOL)
            print_html(f'<green>"{self.rom.glm_name}" saved successfully.</green>\n')

        if not path.exists(self.rom.glm_path):
            save()
        elif self.yes_no_prompt(
            "Are you sure you want to overwrite the saved analysis?"
        ):
            save()

    @command()
    @argument("target_pc")
    @argument("state_expr")
    def do_preview(self, target_pc: str, state_expr: str) -> None:
        """Preview a subroutine disassembly without affecting the current analysis."""
        if not target_pc.startswith("$"):
            raise GilgameshError("Please specify a valid address.")
        pc_int = self._label_to_pc(target_pc)
        print_html(self._print_preview_many([pc_int], state_expr)[0])

    def _print_preview_many(self, target_pcs: List[int], state_expr: str) -> List[str]:
        disassemblies = []
        # Save a copy of the current state of the analysis.
        old_labels = set(self.log.subroutines_by_label.keys())
        saved_log = deepcopy(self.log.save())

        # Add the target pcs as entry point.
        for pc in target_pcs:
            label = self.log.preserved_labels.get(pc, f"sub_{pc:06X}")
            self.do_entrypoint(f"${pc:06X}", label, state_expr)
        # Execute the analysis again.
        self.log.analyze()
        new_labels = self.log.subroutines_by_label.keys() - old_labels

        # Get the disassembly of the target subroutines,
        # highlighting new undiscovered subroutines in red.
        for pc in target_pcs:
            subroutine = self.log.subroutines[pc]
            disassembly = SubroutineDisassembly(subroutine, new_labels)
            disassemblies.append(disassembly.get_html())

        # Restore previous log.
        self.log.load(saved_log)
        return disassemblies

    @command()
    @argument("label", complete_subroutine)
    def do_subroutine(self, label: str) -> None:
        """Select which subroutine to inspect."""
        if not label:
            self.subroutine = None
        elif label in self.log.subroutines_by_label:
            self.subroutine = self.log.subroutines_by_label[label]
        else:
            print_error("No such subroutine.")

    @command()
    @argument("label_or_pc", complete_label)
    def do_translate(self, label_or_pc: str) -> None:
        """Translate a SNES address to a PC address."""
        pc = self._label_to_pc(label_or_pc)
        s = []
        s.append("<green>SNES:</green> ${:06X}\n".format(pc))
        s.append("<green>PC:</green>   ${:06X}\n".format(self.rom._translate(pc)))
        print_html("".join(s))

    def _label_to_pc(self, label_or_pc: str) -> int:
        if label_or_pc.startswith("$"):
            try:
                pc = sum(int(x, 16) for x in label_or_pc[1:].split("+"))
            except ValueError:
                raise GilgameshError("Provided value is not a label or an address.")
            try:
                self.rom._translate(pc)
            except ValueError:
                raise GilgameshError("The given PC is not valid for this ROM.")
            return pc

        label_pc = self.log.get_label_value(label_or_pc, self.subroutine)
        if label_pc is None:
            raise GilgameshError("Unknown label.")
        return label_pc

    def _parse_range(self, range_expr: str) -> Tuple[int, int]:
        parts = tuple(int(n, 16) for n in range_expr.split(".."))
        first = parts[0]
        last = parts[1] if len(parts) == 2 else first
        return first, last

    @staticmethod
    def _print_instruction(instruction: Instruction) -> str:
        try:
            operation = "<green>{:4}</green>".format(instruction.name)
            disassembly = f"{operation}{instruction.argument_string} "
            if not instruction.argument_string:
                disassembly = disassembly[:-1]  # Delete extra space.
        except IndexError:
            disassembly = "<red>unknown</red> "

        return disassembly

    @staticmethod
    def _print_state_change(change: StateChange, show_asserted=True) -> str:
        # TODO: use state expressions inside the StateChange class.
        s = []

        if change.unknown:
            s.append("<red>unknown</red>")
        elif (change.m is None) and (change.x is None):
            s.append("<green>none</green>")
        else:
            if change.m is not None:
                s.append(f"<yellow>m</yellow>=<green>{change.m}</green>")
            if change.x is not None:
                if change.m is not None:
                    s.append(", ")
                s.append(f"<yellow>x</yellow>=<green>{change.x}</green>")

        if show_asserted and change.asserted:
            s.append(" <magenta>(asserted)</magenta>")

        s.append("\n")
        return "".join(s)

    @staticmethod
    def _print_subroutine(sub: Subroutine) -> str:
        if sub.has_unknown_return_state:
            open_color = close_color = "red"
        elif sub.has_asserted_state_change or sub.instruction_has_asserted_state_change:
            open_color = close_color = "magenta"
        elif sub.is_jump_table_target:
            open_color = close_color = "blue"
        else:
            open_color = close_color = "green"

        if sub.is_entry_point:
            open_color = f'black bg="ansi{open_color}"'
            close_color = "black"

        comment = ""
        if sub.has_suspect_instructions:
            comment += ' <black bg="ansired">[!]</black>'
        if sub.has_stack_manipulation:
            comment += " <red>[?]</red>"
        if sub.indirect_jumps:
            color = "red" if sub.has_incomplete_jump_table else "green"
            comment += f" <{color}>[*]</{color}>"
        if sub.is_recursive:
            comment += " <yellow>[∞]</yellow>"
        if sub.has_multiple_known_state_changes:
            comment += " <yellow>[+]</yellow>"

        return "${:06X}  <{}>{}</{}>{}\n".format(
            sub.pc, open_color, sub.label, close_color, comment,
        )
