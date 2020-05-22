from typing import Optional, Set

from gilgamesh.disassembly.container import DisassemblyContainer
from gilgamesh.log import Log
from gilgamesh.subroutine import Subroutine


class SubroutineDisassembly(DisassemblyContainer):
    def __init__(
        self, subroutine: Subroutine, preview_excluded_labels: Optional[Set[str]] = None
    ):
        super().__init__(subroutine.log, [subroutine], preview_excluded_labels)


class ROMDisassembly(DisassemblyContainer):
    def __init__(self, log: Log):
        super().__init__(log, log.subroutines.values())


__all__ = ["SubroutineDisassembly", "ROMDisassembly"]
