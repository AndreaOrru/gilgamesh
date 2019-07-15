from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set, Tuple

from bidict import bidict
from sortedcontainers import SortedDict

from .cpu import CPU
from .instruction import Instruction, InstructionID
from .rom import ROM
from .state import StateChange
from .subroutine import Subroutine


class Log:
    def __init__(self, rom: ROM):
        self.rom = rom

        self.entry_points: List[InstructionID] = []
        self.local_labels: DefaultDict[int, Dict[str, int]] = defaultdict(bidict)
        self.instructions: Set[InstructionID] = set()
        self.subroutines: Dict[int, Subroutine] = SortedDict()
        self.subroutines_by_label: Dict[str, Subroutine] = {}
        self.references: DefaultDict[int, Set[Tuple[int, int]]] = defaultdict(set)

        self.add_subroutine(self.rom.reset_vector, label="reset", entry_point=True)
        self.add_subroutine(self.rom.nmi_vector, label="nmi", entry_point=True)

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
            subroutine = Subroutine(self, pc, label)
            self.subroutines[pc] = subroutine
            self.subroutines_by_label[label] = subroutine

        if entry_point:
            self.entry_points.append(InstructionID(pc, p, pc))

    def add_subroutine_state(
        self, subroutine_pc: int, state_change: StateChange
    ) -> None:
        subroutine = self.subroutines[subroutine_pc]
        subroutine.state_changes.add(state_change)

    def get_subroutine_states(self, subroutine_pc: int) -> Set[StateChange]:
        return self.subroutines[subroutine_pc].state_changes

    def add_reference(self, instruction: Instruction, target: int) -> None:
        self.references[target].add((instruction.pc, instruction.subroutine))

    def get_label(self, pc: int, subroutine_pc: int) -> Optional[str]:
        subroutine = self.subroutines.get(pc)
        if subroutine:
            return subroutine.label
        local_label = self.local_labels[subroutine_pc].inverse.get(pc)  # noqa: T484
        if local_label:
            return f".{local_label}"
        return None

    def rename_label(
        self, old: str, new: str, subroutine_pc: Optional[int] = None
    ) -> None:
        subroutine = self.subroutines_by_label.pop(old, None)
        if subroutine is not None:
            subroutine.label = new
            self.subroutines_by_label[new] = subroutine

        elif subroutine_pc is not None:
            local_labels = self.local_labels[subroutine_pc]
            local_labels[new] = local_labels.pop(old)

    def is_visited(self, instruction_id: InstructionID) -> bool:
        return instruction_id in self.instructions

    def _generate_labels(self) -> None:
        for target, sources in self.references.items():
            if target in self.subroutines:
                continue

            for pc, subroutine_pc in sources:
                local_label = f"loc_{target:06X}"
                self.local_labels[subroutine_pc][local_label] = target
