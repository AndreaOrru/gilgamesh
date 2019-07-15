from typing import Dict, Set

from sortedcontainers import SortedDict

from .instruction import Instruction
from .state import StateChange


class Subroutine:
    def __init__(self, log, pc: str, label: str):
        self.log = log
        self.pc = pc
        self.label = label
        self.instructions: Dict[int, Instruction] = SortedDict()
        self.state_changes: Set[StateChange] = set()

    @property
    def local_labels(self) -> Dict[str, int]:
        return self.log.local_labels[self.pc]

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction
