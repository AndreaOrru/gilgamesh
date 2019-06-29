from cmd import Cmd

from .rom import ROM


class App(Cmd):
    prompt = ">>> "

    def __init__(self, rom_path: str):
        super().__init__()
        self.rom = ROM(rom_path)

    def do_EOF(self, _) -> bool:
        """Quit the application."""
        return True

    def do_quit(self, _) -> bool:
        """Quit the application."""
        return True
