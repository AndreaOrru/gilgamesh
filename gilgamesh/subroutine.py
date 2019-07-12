from typing import Dict

from sortedcontainers import SortedDict

from .instruction import Instruction


class Subroutine:
    def __init__(self, log, pc: str, label: str):
        self.log = log
        self.pc = pc
        self.label = label
        self.instructions: Dict[int, Instruction] = SortedDict()

    @property
    def local_labels(self) -> Dict[str, int]:
        return self.log.local_labels[self.pc]

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction
