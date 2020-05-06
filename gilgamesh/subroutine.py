from typing import Dict, Set

from sortedcontainers import SortedDict  # type: ignore

from gilgamesh.instruction import Instruction
from gilgamesh.state import StateChange


class Subroutine:
    def __init__(self, log, pc: int, label: str):
        self.log = log
        self.pc = pc
        self.label = label

        # Instructions belonging to the subroutine.
        self.instructions: Dict[int, Instruction] = SortedDict()
        # Calling the subroutine results in the following state changes.
        self.state_changes: Set[StateChange] = set()

    @property
    def local_labels(self) -> Dict[str, int]:
        return self.log.local_labels[self.pc]

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction
