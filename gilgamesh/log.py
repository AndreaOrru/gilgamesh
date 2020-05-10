import pickle
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set, Tuple

from bidict import bidict  # type: ignore
from sortedcontainers import SortedDict  # type: ignore

from gilgamesh.cpu import CPU
from gilgamesh.instruction import Instruction, InstructionID
from gilgamesh.rom import ROM
from gilgamesh.state import StateChange
from gilgamesh.subroutine import Subroutine


class Log:
    def __init__(self, rom: ROM):
        self.rom = rom
        self.instruction_assertions: Dict[int, StateChange] = {}
        self.subroutine_assertions: Dict[int, StateChange] = {}
        self.preserved_labels: Dict[int, str] = {}
        self.comments: Dict[int, str] = {}
        self.clear()

    def clear(self) -> None:
        # Preserve currently assigned labels.
        self._preserve_labels()

        # Clear all data structures.
        self.entry_points: List[InstructionID] = []
        self.local_labels: DefaultDict[int, Dict[str, int]] = defaultdict(bidict)
        self.instructions: DefaultDict[int, Set[InstructionID]] = defaultdict(set)
        self.subroutines: Dict[int, Subroutine] = SortedDict()
        self.subroutines_by_label: Dict[str, Subroutine] = {}
        self.references: DefaultDict[int, Set[Tuple[int, int]]] = defaultdict(set)

        # Add entry points.
        self.add_subroutine(self.rom.reset_vector, label="reset", entry_point=True)
        self.add_subroutine(self.rom.nmi_vector, label="nmi", entry_point=True)

        self.dirty = False

    def save(self) -> None:
        self._preserve_labels()
        data = {
            "instruction_assertions": self.instruction_assertions,
            "subroutine_assertions": self.subroutine_assertions,
            "preserved_labels": self.preserved_labels,
            "comments": self.comments,
        }
        with open(self.rom.glm_path, "wb") as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    def load(self) -> bool:
        try:
            with open(self.rom.glm_path, "rb") as f:
                data = pickle.load(f)
                self.instruction_assertions = data["instruction_assertions"]
                self.subroutine_assertions = data["subroutine_assertions"]
                self.preserved_labels = data["preserved_labels"]
                self.comments = data["comments"]
            self.analyze()
        except OSError:
            return False
        else:
            return True

    def analyze(self) -> None:
        # Clear the current results.
        if self.instructions:
            self.clear()

        # Start emulation from all entry points.
        for pc, p, subroutine in self.entry_points:
            cpu = CPU(self, pc, p, subroutine)
            cpu.run()

        # Generate labels for newly discovered code.
        self._generate_labels()

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc].add(instruction.id)
        subroutine = self.subroutines[instruction.subroutine]
        subroutine.add_instruction(instruction)

        if instruction.pc in self.instruction_assertions:
            subroutine.instruction_has_asserted_state_change = True

    def add_subroutine(
        self, pc: int, p: int = 0b0011_0000, label: str = "", entry_point: bool = False
    ) -> None:
        # Assign a label to the subroutine (or retrieve the existing one).
        preserved_label = self.preserved_labels.get(pc)
        if preserved_label:
            label = preserved_label
        elif not label:
            label = "sub_{:06X}".format(pc)

        # Create and register subroutine (unless it exists already).
        subroutine = self.subroutines.get(pc)
        if subroutine is None:
            subroutine = Subroutine(self, pc, label)
            self.subroutines[pc] = subroutine
            self.subroutines_by_label[label] = subroutine

        # Apply existing state change assertions.
        state_change = self.subroutine_assertions.get(pc)
        if state_change:
            subroutine.assert_state_change(state_change)

        # Register the subroutine as an entry point if specified.
        if entry_point:
            self.entry_points.append(InstructionID(pc, p, pc))

    def add_subroutine_state(
        self, subroutine_pc: int, state_change: StateChange
    ) -> None:
        if subroutine_pc not in self.subroutine_assertions:
            # Keep track of the processor state changes
            # caused by the execution of a subroutine.
            subroutine = self.subroutines[subroutine_pc]
            subroutine.state_changes.add(state_change)

    def assert_instruction_state_change(
        self, instruction_pc: int, state_change: StateChange
    ) -> None:
        self.instruction_assertions[instruction_pc] = state_change
        self.dirty = True

    def deassert_instruction_state_change(self, instruction_pc: int) -> None:
        self.instruction_assertions.pop(instruction_pc, None)
        self.dirty = True

    def assert_subroutine_state_change(
        self, subroutine: Subroutine, state_change: StateChange
    ) -> None:
        self.subroutine_assertions[subroutine.pc] = state_change
        self.dirty = True

    def deassert_subroutine_state_change(self, subroutine_pc: int) -> None:
        self.subroutine_assertions.pop(subroutine_pc, None)
        self.dirty = True

    def add_reference(self, instruction: Instruction, target: int) -> None:
        self.references[target].add((instruction.pc, instruction.subroutine))

    def get_label(self, pc: int, subroutine_pc: int) -> Optional[str]:
        subroutine = self.subroutines.get(pc)
        if subroutine:
            return subroutine.label

        local_label = self.local_labels[subroutine_pc].inverse.get(pc)  # type: ignore
        if local_label:
            return f".{local_label}"

        return None

    def get_label_value(
        self, label: str, subroutine_pc: Optional[int] = None
    ) -> Optional[int]:
        # If there's a match with a subroutine.
        subroutine = self.subroutines_by_label.get(label)
        if subroutine is not None:
            return subroutine.pc

        # If there's a match with a local label inside the given subroutine.
        if subroutine_pc is not None:
            return self.local_labels[subroutine_pc].get(label)

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
        elements = self.instructions.get(instruction_id.pc, set())
        return instruction_id in elements

    def _generate_labels(self) -> None:
        for target, sources in self.references.items():
            # Subroutines are already tracked.
            if target in self.subroutines:
                continue

            # Generate local labels, or reuse existing ones.
            for pc, subroutine_pc in sources:
                preserved_label = self.preserved_labels.get(target)
                local_label = (
                    preserved_label if preserved_label else f"loc_{target:06X}"
                )
                self.local_labels[subroutine_pc][local_label] = target

    def _preserve_labels(self) -> None:
        if hasattr(self, "instructions"):
            for subroutine_labels in self.local_labels.values():
                self.preserved_labels.update(subroutine_labels.inverse)  # type: ignore
            for subroutine in self.subroutines.values():
                self.preserved_labels[subroutine.pc] = subroutine.label
