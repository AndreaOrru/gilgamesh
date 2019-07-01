from cmd import Cmd
from typing import List, Optional

from .colors import NORMAL, YELLOW, print_html
from .log import Log
from .rom import ROM
from .subroutine import Subroutine


class App(Cmd):
    def __init__(self, rom_path: str):
        super().__init__()

        self.rom = ROM(rom_path)
        self.log = Log(self.rom)

        self.subroutine: Optional[Subroutine] = None

    @property
    def prompt(self) -> str:  # noqa
        prompt = "" if (self.subroutine is None) else f"[{self.subroutine.label}]"
        return f"{YELLOW}{prompt}>{NORMAL} "

    def do_rom(self, _) -> None:
        """Show general information on the ROM."""
        s = ""
        s += "<green>Title:</green>    {}\n".format(self.rom.title)
        s += "<green>Type:</green>     {}\n".format(self.rom.type.name)
        s += "<green>Size:</green>     {} KiB\n".format(self.rom.size // 1024)
        s += "<green>Vectors:</green>\n"
        s += "  <green>RESET:</green>  ${:06X}\n".format(self.rom.reset_vector)
        s += "  <green>NMI:</green>    ${:06X}\n".format(self.rom.nmi_vector)
        print_html(s)

    def do_analyze(self, _) -> None:
        """Run the analysis on the ROM."""
        self.log.analyze()

    def complete_subroutine(self, text: str, *args) -> List[str]:
        text = text.lower()
        return [x for x in self.log.subroutines_by_label if x.lower().startswith(text)]

    def do_subroutine(self, label: str) -> None:
        """Select which subroutine to inspect."""
        if not label:
            self.subroutine = None
        elif label in self.log.subroutines_by_label:
            self.subroutine = self.log.subroutines_by_label[label]
        else:
            print('*** No subroutine named "{}"', label)

    def complete_list(self, *args) -> List[str]:
        return ["subroutines"]

    def do_list(self, arg: str) -> None:
        if arg == "subroutines":
            self._do_list_subroutines()
        else:
            print("*** Unknown syntax: list {}", arg)

    def _do_list_subroutines(self) -> None:
        s = ""
        for subroutine in self.log.subroutines.values():
            s += "${:06X}  <green>{}</green>\n".format(subroutine.pc, subroutine.label)
        print_html(s)

    def do_disassembly(self, _) -> None:
        if not self.subroutine:
            return print("*** No selected subroutine")

        s = ""
        for pc, instruction in self.subroutine.instructions.items():
            label = self.log.labels_by_pc.get(pc)
            if label:
                s += f"<red>{label}</red>:\n"
            operation = "<green>{:4}</green>".format(instruction.name)
            if instruction.argument_alias:
                argument = "<red>{:16}</red>".format(instruction.argument_alias)
            else:
                argument = "{:16}".format(instruction.argument_string)
            comment = "<grey>; ${:06X}</grey>".format(pc)
            s += f"  {operation}{argument}{comment}\n"
        print_html(s)

    def do_debug(self, _) -> None:
        """Debug Gilgamesh itself."""
        breakpoint()  # noqa

    def do_EOF(self, _) -> bool:
        """Quit the application."""
        return True

    def do_quit(self, _) -> bool:
        """Quit the application."""
        return True
