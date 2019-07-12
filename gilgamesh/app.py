from typing import Iterable, Optional

from prompt_toolkit import HTML

from .log import Log
from .repl import Repl, argument, command, print_html
from .rom import ROM
from .subroutine import Subroutine


class App(Repl):
    def __init__(self, rom_path: str):
        super().__init__()

        self.rom = ROM(rom_path)
        self.log = Log(self.rom)

        self.subroutine: Optional[Subroutine] = None

    @property
    def prompt(self) -> str:
        if self.subroutine is None:
            return super().prompt
        return HTML("<yellow>" + f"[{self.subroutine.label}]> " + "</yellow>")

    def complete_subroutine(self) -> Iterable[str]:
        return self.log.subroutines_by_label.keys()

    @command
    def do_analyze(self) -> None:
        """Run the analysis on the ROM."""
        self.log.analyze()

    @command
    def do_disassembly(self) -> None:
        """Show disassembly of selected subroutine."""
        if not self.subroutine:
            return self.error("No selected subroutine.")

        s = ""
        for pc, instruction in self.subroutine.instructions.items():
            label = self.log.labels_by_pc.get(pc)
            if label:
                s += f"<red>{label}</red>:\n"
            operation = "<green>{:4}</green>".format(instruction.name)
            if instruction.argument_alias:
                arg = "<red>{:16}</red>".format(instruction.argument_alias)
            else:
                arg = "{:16}".format(instruction.argument_string)
            comment = "<grey>; ${:06X}</grey>".format(pc)
            s += f"  {operation}{arg}{comment}\n"
        print_html(s)

    @command
    def do_list(self) -> None:
        """List various types of entities."""
        ...

    @command
    def do_list_subroutines(self) -> None:
        """List all subroutines."""
        s = ""
        for subroutine in self.log.subroutines.values():
            s += "${:06X}  <green>{}</green>\n".format(subroutine.pc, subroutine.label)
        print_html(s)

    @command
    def do_rom(self) -> None:
        """Show general information on the ROM."""
        s = ""
        s += "<green>Title:</green>    {}\n".format(self.rom.title)
        s += "<green>Type:</green>     {}\n".format(self.rom.type.name)
        s += "<green>Size:</green>     {} KiB\n".format(self.rom.size // 1024)
        s += "<green>Vectors:</green>\n"
        s += "  <green>RESET:</green>  ${:06X}\n".format(self.rom.reset_vector)
        s += "  <green>NMI:</green>    ${:06X}\n".format(self.rom.nmi_vector)
        print_html(s)

    @command
    @argument("label", complete_subroutine)
    def do_subroutine(self, label: str) -> None:
        """Select which subroutine to inspect."""
        if not label:
            self.subroutine = None
        elif label in self.log.subroutines_by_label:
            self.subroutine = self.log.subroutines_by_label[label]
        else:
            self.error("No such subroutine.")
