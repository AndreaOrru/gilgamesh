from os import path
from typing import List, Optional

from prompt_toolkit import HTML  # type: ignore

from gilgamesh.disassembly import Disassembly
from gilgamesh.log import Log
from gilgamesh.repl import Repl, argument, command, print_error, print_html
from gilgamesh.rom import ROM
from gilgamesh.state import State, StateChange
from gilgamesh.subroutine import Subroutine

HISTORY_FILE = "~/.local/share/gilgamesh/history.log"


class App(Repl):
    def __init__(self, rom_path: str):
        super().__init__(history_file=HISTORY_FILE)

        self.rom = ROM(rom_path)
        self.log = Log(self.rom)
        # Try to automatically load an existing analysis.
        if not self._do_load():
            self.log.analyze()

        # The subroutine currently under analysis.
        self.subroutine_pc: Optional[int] = None

    @property
    def subroutine(self) -> Optional[Subroutine]:
        if self.subroutine_pc is None:
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
        self.log.analyze()

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
        state_change = StateChange.from_state_expr(state_expr)
        instruction_pc = self._label_to_pc(label_or_pc)
        self.log.assert_instruction_state_change(instruction_pc, state_change)

    @command()
    @argument("state_expr")
    def do_assert_subroutine(self, state_expr: str) -> None:
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
            return print_error("No selected subroutine.")
        state_change = StateChange.from_state_expr(state_expr)
        self.log.assert_subroutine_state_change(self.subroutine, state_change)

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
    @argument("subroutine_or_pc", complete_subroutine)
    def do_deassert_subroutine(self, subroutine_or_pc: str) -> None:
        """Remove previously defined subroutine assertions."""
        pc = self._label_to_pc(subroutine_or_pc)
        self.log.deassert_subroutine_state_change(pc)

    @command()
    def do_disassembly(self) -> None:
        """Show disassembly of selected subroutine."""
        if not self.subroutine:
            return print_error("No selected subroutine.")
        disassembly = Disassembly(self.log, self.subroutine)
        print_html(disassembly.html)

    @command()
    def do_edit(self) -> None:
        """Interactively edit the subroutine using an external editor."""
        if not self.subroutine:
            return print_error("No selected subroutine.")
        disassembly = Disassembly(self.log, self.subroutine)
        disassembly.edit()

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
        s = ["<red>ASSERTED INSTRUCTION STATE CHANGES:</red>\n"]
        for pc, change in self.log.instruction_assertions.items():
            subroutines = [
                self.log.subroutines[i.subroutine] for i in self.log.instructions[pc]
            ]
            try:
                instruction = subroutines[0].instructions[pc]
                operation = "<green>{:4}</green>".format(instruction.name)
                disassembly = f"{operation}{instruction.argument_string}"
            except IndexError:
                disassembly = "<red>UNKNOWN</red>"

            s.append("  <magenta>${:06X}</magenta>  {} -> ".format(pc, disassembly))
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
        s = ["<red>ASSERTED SUBROUTINE STATE CHANGES:</red>\n"]
        for pc, change in self.log.subroutine_assertions.items():
            try:
                sub = "<magenta>{}</magenta>".format(self.log.subroutines[pc].label)
            except KeyError:
                sub = "<red>${:06X}</red>".format(pc)
            s.append(f"  {sub} -> ")
            s.append(self._print_state_change(change))
        print_html("".join(s))

    @command()
    def do_list_subroutines(self) -> None:
        """List subroutines according to various criteria.
        If called with no arguments, display all subroutines.
        Subroutines with unknown return states are shown in red.

        Subroutines can be flagged with various symbols:
          [*] -> Jump table
          [?] -> Stack manipulation
          [!] -> Suspicious instructions"""
        s = []
        for subroutine in self.log.subroutines.values():
            s.append(self._print_subroutine(subroutine))
        print_html("".join(s))

    @command()
    def do_list_subroutines_unknown(self) -> None:
        """List subroutines with unknown return states.

        Subroutines can be flagged with various symbols:
          [*] -> Jump table
          [?] -> Stack manipulation
          [!] -> Suspicious instructions"""
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
        if self.log.load():
            print_html(f'<green>"{self.rom.glm_name}" loaded successfully.</green>\n')
            return True
        else:
            return False

    @command(container=True)
    def do_query(self) -> None:
        """Query the analysis log in various ways."""
        ...

    @command()
    @argument("label_or_pc", complete_label)
    def do_query_state(self, label_or_pc: str) -> None:
        """Show the processor states in which an instruction can be reached."""
        pc = self._label_to_pc(label_or_pc)

        s = []
        states = {State(x.p) for x in self.log.instructions[pc]}
        for state in states:
            s.append(f"<yellow>M</yellow>=<green>{state.m}</green>, ")
            s.append(f"<yellow>X</yellow>=<green>{state.x}</green>\n")
        print_html("".join(s))

    @command()
    @argument("subroutine_or_pc", complete_subroutine)
    def do_query_statechange(self, subroutine_or_pc: str) -> None:
        """Show the change in processor state caused by executing a subroutine."""
        pc = self._label_to_pc(subroutine_or_pc)
        asserted_change = self.log.subroutine_assertions.get(pc)
        if asserted_change:
            return print_html(
                "{} <magenta>(asserted)</magenta>".format(
                    self._print_state_change(asserted_change, newline=False)
                )
            )

        s = []
        for change in self.log.subroutines[pc].state_changes:
            s.append(self._print_state_change(change))
        print_html("".join(s))

    @command()
    @argument("old", complete_label)
    @argument("new")
    def do_rename(self, old: str, new: str) -> None:
        """Rename a label or subroutine."""
        self.log.rename_label(old, new, self.subroutine.pc if self.subroutine else None)

    @command()
    def do_reset(self) -> None:
        """Reset the analysis (start from scratch)."""
        if self.yes_no_prompt("Are you sure you want to reset the entire analysis?"):
            self.log.reset()
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
            self.log.save()
            print_html(f'<green>"{self.rom.glm_name}" saved successfully.</green>\n')

        if not path.exists(self.rom.glm_path):
            save()
        elif self.yes_no_prompt(
            "Are you sure you want to overwrite the saved analysis?"
        ):
            save()

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
        print_html("<green>SNES:</green> ${:06X}".format(pc))
        print_html("<green>PC:</green>   ${:06X}\n".format(self.rom._translate(pc)))

    def _label_to_pc(self, label_or_pc) -> int:
        pc = self.log.get_label_value(
            label_or_pc, self.subroutine.pc if self.subroutine else None
        )
        if pc is not None:
            return pc

        try:
            return int(label_or_pc, 16)
        except ValueError:
            raise GilgameshError("Provided value is neither a label nor an address.")

    @staticmethod
    def _print_state_change(change: StateChange, newline=True) -> str:
        s = []

        if change.unknown:
            s.append("<red>Unknown</red>")
        elif (change.m is None) and (change.x is None):
            s.append("<green>None</green>")
        else:
            if change.m is not None:
                s.append(f"<yellow>M</yellow>=<green>{change.m}</green>")
            if change.x is not None:
                if change.m is not None:
                    s.append(", ")
                s.append(f"<yellow>X</yellow>=<green>{change.x}</green>")

        if newline:
            s.append("\n")
        return "".join(s)

    @staticmethod
    def _print_subroutine(sub: Subroutine) -> str:
        if sub.has_unknown_return_state:
            color = "red"
        elif sub.has_asserted_state_change or sub.instruction_has_asserted_state_change:
            color = "magenta"
        else:
            color = "green"

        comment = ""
        if sub.has_suspicious_instructions:
            comment += " <red>[!]</red>"
        if sub.has_stack_manipulation:
            comment += " <red>[?]</red>"
        if sub.has_jump_table:
            comment += " <red>[*]</red>"

        return "${:06X}  <{}>{}</{}>{}\n".format(
            sub.pc, color, sub.label, color, comment,
        )
