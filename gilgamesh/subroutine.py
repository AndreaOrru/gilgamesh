from typing import Dict

from sortedcontainers import SortedDict

from .instruction import Instruction


class Subroutine:
    def __init__(self, pc: str, label: str):
        self.pc = pc
        self.label = label
        self.instructions: Dict[int, Instruction] = SortedDict()

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction
