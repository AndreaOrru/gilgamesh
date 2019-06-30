from typing import Dict, List, Set

from sortedcontainers import SortedDict

from .cpu import CPU
from .instruction import Instruction, InstructionID
from .rom import ROM
from .subroutine import Subroutine


class Log:
    def __init__(self, rom: ROM):
        self.rom = rom

        self.instructions: Set[InstructionID] = set()
        self.entry_points: List[InstructionID] = []
        self.subroutines: Dict[int, Subroutine] = SortedDict()
        self.labels: Dict[str, Subroutine] = {}

        self.add_subroutine(self.rom.reset_vector, label="reset")
        self.add_subroutine(self.rom.nmi_vector, label="nmi")

    def analyze(self) -> None:
        for pc, p, subroutine in self.entry_points:
            cpu = CPU(self, pc, p, subroutine)
            cpu.run()

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions.add(instruction.id)
        subroutine = self.subroutines[instruction.subroutine]
        subroutine.add_instruction(instruction)

    def add_subroutine(self, pc: int, p: int = 0b0011_0000, label: str = "") -> None:
        if not label:
            label = "sub_{:06X}".format(pc)

        subroutine = self.subroutines.get(pc)
        if subroutine is None:
            subroutine = Subroutine(pc, label)
            self.subroutines[pc] = subroutine
            self.labels[label] = subroutine
        self.entry_points.append(InstructionID(pc, p, pc))

    def is_visited(self, instruction_id: InstructionID) -> bool:
        return instruction_id in self.instructions
