from typing import Dict

from .instruction import Instruction


class Subroutine:
    def __init__(self, pc: str, label: str):
        self.pc = pc
        self.label = label
        self.instructions: Dict[int, Instruction] = {}

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction
