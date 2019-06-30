from cmd import Cmd

from .colors import NORMAL, YELLOW, print
from .log import Log
from .rom import ROM


class App(Cmd):
    prompt = f"{YELLOW}>>>{NORMAL} "

    def __init__(self, rom_path: str):
        super().__init__()
        self.rom = ROM(rom_path)
        self.log = Log(self.rom)

    def do_rom(self, _):
        """Show general information on the ROM."""
        print("<green>Title:</green>    {}", self.rom.title)
        print("<green>Type:</green>     {}", self.rom.type.name)
        print("<green>Size:</green>     {} KiB", self.rom.size // 1024)
        print("<green>Vectors:</green>")
        print("  <green>RESET:</green>  ${:06X}", self.rom.reset_vector)
        print("  <green>NMI:</green>    ${:06X}", self.rom.nmi_vector)

    def do_analyze(self, _):
        """Run the analysis on the ROM."""
        self.log.analyze()

    def do_subroutines(self, _):
        """List all known subroutines."""
        for subroutine in self.log.subroutines.values():
            print("${:06X}  <green>{}</green>", subroutine.pc, subroutine.label)

    def do_debug(self, _) -> None:
        """Debug Gilgamesh itself."""
        breakpoint()  # noqa

    def do_EOF(self, _) -> bool:
        """Quit the application."""
        return True

    def do_quit(self, _) -> bool:
        """Quit the application."""
        return True
