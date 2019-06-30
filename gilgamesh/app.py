from cmd import Cmd
from typing import List, Optional

from .colors import NORMAL, YELLOW, print_html
from .log import Log
from .rom import ROM


class App(Cmd):
    def __init__(self, rom_path: str):
        super().__init__()

        self.rom = ROM(rom_path)
        self.log = Log(self.rom)

        self.subroutine: Optional[str] = None

    @property
    def prompt(self) -> str:  # noqa
        prompt = "" if (self.subroutine is None) else f"[{self.subroutine}]"
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
        return [x for x in self.log.labels.keys() if x.startswith(text)]

    def do_subroutine(self, arg: str) -> None:
        """Select which subroutine to inspect."""
        if not arg:
            self.subroutine = None
        elif arg in self.log.labels:
            self.subroutine = arg
        else:
            print('*** No subroutine named "{}"', arg)

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
        s = f"<red>{self.subroutine}</red>:\n"
        subroutine = self.log.labels[self.subroutine]
        for pc, instruction in subroutine.instructions.items():
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
