from typing import List, Optional

from prompt_toolkit import HTML  # type: ignore

from gilgamesh.log import Log
from gilgamesh.repl import Repl, argument, command, print_error, print_html
from gilgamesh.rom import ROM
from gilgamesh.state import State
from gilgamesh.subroutine import Subroutine


class App(Repl):
    def __init__(self, rom_path: str):
        super().__init__()

        self.rom = ROM(rom_path)
        self.log = Log(self.rom)

        # The subroutine currently under analysis.
        self.subroutine: Optional[Subroutine] = None

    @property
    def prompt(self) -> str:
        if self.subroutine is None:
            return super().prompt
        # Show the current subroutine in the prompt if there's one.
        return HTML("<yellow>" + f"[{self.subroutine.label}]> " + "</yellow>")

    def complete_subroutine(self) -> List[str]:
        return sorted(self.log.subroutines_by_label.keys())

    def complete_label(self) -> List[str]:
        subroutines = self.complete_subroutine()
        if not self.subroutine:
            return subroutines
        local_labels = sorted(self.subroutine.local_labels.keys())
        return local_labels + subroutines

    @command()
    def do_analyze(self) -> None:
        """Run the analysis on the ROM."""
        self.log.analyze()

    @command()
    def do_disassembly(self) -> None:
        """Show disassembly of selected subroutine."""
        if not self.subroutine:
            return print_error("No selected subroutine.")

        s = []
        for pc, instruction in self.subroutine.instructions.items():
            label = self.log.get_label(pc, self.subroutine.pc)
            if label:
                s.append(f"<red>{label}</red>:\n")
            operation = "<green>{:4}</green>".format(instruction.name)
            if instruction.argument_alias:
                arg = "<red>{:16}</red>".format(instruction.argument_alias)
            else:
                arg = "{:16}".format(instruction.argument_string)
            comment = "<grey>; ${:06X}</grey>".format(pc)
            s.append(f"  {operation}{arg}{comment}\n")

            if instruction.stopped_execution:
                s.append(
                    "  <grey>{:20}; ${:06X}</grey>\n".format(
                        "; Unknown state.", instruction.next_pc
                    )
                )

        print_html("".join(s))

    @command()
    def do_debug(self) -> None:
        """Debug Gilgamesh itself."""
        breakpoint()  # noqa

    @command(container=True)
    def do_list(self) -> None:
        """List various types of entities."""
        ...

    @command()
    def do_list_subroutines(self) -> None:
        """List subroutines according to various criteria.
        If called with no arguments, display all subroutines."""
        s = []
        for subroutine in self.log.subroutines.values():
            s.append(self._print_subroutine(subroutine))
        print_html("".join(s))

    @command()
    def do_list_subroutines_unknown(self) -> None:
        """List subroutines with unknown or multiple return states."""
        s = []
        for subroutine in self.log.subroutines.values():
            if subroutine.has_unknown_return_state():
                s.append(self._print_subroutine(subroutine))
        print_html("".join(s))

    @command(container=True)
    def do_query(self) -> None:
        """Query the analysis log in various ways."""
        ...

    @command()
    @argument("label_pc", complete_label)
    def do_query_state(self, label_pc: str) -> None:
        """Show the processor states in which an instruction can be reached."""
        pc = self.log.get_label_value(
            label_pc, self.subroutine.pc if self.subroutine else None
        )
        if pc is None:
            pc = int(label_pc, 16)

        s = []
        states = {State(x.p) for x in self.log.instructions[pc]}
        for state in states:
            s.append(f"<yellow>M</yellow>=<green>{state.m}</green>, ")
            s.append(f"<yellow>X</yellow>=<green>{state.x}</green>\n")
        print_html("".join(s))

    @command()
    @argument("old", complete_label)
    @argument("new")
    def do_rename(self, old: str, new: str) -> None:
        """Rename a label or subroutine."""
        self.log.rename_label(old, new, self.subroutine.pc if self.subroutine else None)

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
    @argument("label", complete_subroutine)
    def do_subroutine(self, label: str) -> None:
        """Select which subroutine to inspect."""
        if not label:
            self.subroutine = None
        elif label in self.log.subroutines_by_label:
            self.subroutine = self.log.subroutines_by_label[label]
        else:
            print_error("No such subroutine.")

    @staticmethod
    def _print_subroutine(subroutine: Subroutine) -> str:
        return "${:06X}  <green>{}</green>\n".format(subroutine.pc, subroutine.label)
