from gilgamesh.disassembly.container import DisassemblyContainer
from gilgamesh.log import Log
from gilgamesh.subroutine import Subroutine


class SubroutineDisassembly(DisassemblyContainer):
    def __init__(self, subroutine: Subroutine):
        super().__init__(subroutine.log, [subroutine])


class ROMDisassembly(DisassemblyContainer):
    def __init__(self, log: Log):
        super().__init__(log, log.subroutines.values())


__all__ = ["SubroutineDisassembly", "ROMDisassembly"]
