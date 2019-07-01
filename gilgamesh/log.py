from collections import defaultdict
from typing import DefaultDict, Dict, List, Set

from bidict import ValueDuplicationError, bidict
from sortedcontainers import SortedDict

from .cpu import CPU
from .instruction import Instruction, InstructionID
from .rom import ROM
from .subroutine import Subroutine


class Log:
    def __init__(self, rom: ROM):
        self.rom = rom

        self.entry_points: List[InstructionID] = []
        self.labels: Dict[str, int] = bidict()
        self.instructions: Set[InstructionID] = set()
        self.subroutines: Dict[int, Subroutine] = SortedDict()
        self.subroutines_by_label: Dict[str, Subroutine] = {}
        self.references: DefaultDict[int, Set[int]] = defaultdict(set)

        self.add_subroutine(self.rom.reset_vector, label="reset", entry_point=True)
        self.add_subroutine(self.rom.nmi_vector, label="nmi", entry_point=True)

    @property
    def labels_by_pc(self) -> Dict[int, str]:
        return self.labels.inverse  # noqa

    def analyze(self) -> None:
        for pc, p, subroutine in self.entry_points:
            cpu = CPU(self, pc, p, subroutine)
            cpu.run()
        self._generate_labels()

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions.add(instruction.id)
        subroutine = self.subroutines[instruction.subroutine]
        subroutine.add_instruction(instruction)

    def add_subroutine(
        self, pc: int, p: int = 0b0011_0000, label: str = "", entry_point: bool = False
    ) -> None:
        if not label:
            label = "sub_{:06X}".format(pc)

        subroutine = self.subroutines.get(pc)
        if subroutine is None:
            subroutine = Subroutine(pc, label)
            self.subroutines[pc] = subroutine
            self.subroutines_by_label[label] = subroutine
            self.labels[label] = pc

        if entry_point:
            self.entry_points.append(InstructionID(pc, p, pc))

    def add_reference(self, pc: int, target: int) -> None:
        self.references[target].add(pc)

    def is_visited(self, instruction_id: InstructionID) -> bool:
        return instruction_id in self.instructions

    def _generate_labels(self) -> None:
        for reference in self.references:
            if reference not in self.subroutines:
                try:
                    self.labels[f".loc_{reference:06X}"] = reference
                except ValueDuplicationError:
                    pass
