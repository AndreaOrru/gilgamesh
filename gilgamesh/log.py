import gc
from collections import defaultdict, namedtuple
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple

from bidict import bidict  # type: ignore
from sortedcontainers import SortedDict  # type: ignore

from gilgamesh.errors import GilgameshError
from gilgamesh.snes.cpu import CPU
from gilgamesh.snes.instruction import Instruction, InstructionID
from gilgamesh.snes.rom import ROM
from gilgamesh.snes.state import State, StateChange
from gilgamesh.subroutine import Subroutine
from gilgamesh.utils.invalidable import bulk_invalidate

EntryPoint = namedtuple("EntryPoint", ("name", "p"))


class Log:
    def __init__(self, rom: ROM):
        self.rom = rom
        self.reset()

    def reset(self) -> None:
        self.instruction_assertions: Dict[int, StateChange] = {}
        self.subroutine_assertions: Dict[int, Dict[int, StateChange]] = {}
        self.preserved_labels: Dict[int, str] = {}
        self.comments: Dict[int, str] = {}

        self.entry_points: Dict[int, EntryPoint] = {
            self.rom.reset_vector: EntryPoint("reset", 0b0011_0000),
            self.rom.nmi_vector: EntryPoint("nmi", 0b0011_0000),
        }

        self._clear(preserve_labels=False)

    def _clear(self, preserve_labels=True) -> None:
        # Preserve currently assigned labels.
        if preserve_labels:
            self._preserve_labels()

        # Invalidate Subroutine and Instruction objects.
        if hasattr(self, "subroutines"):
            bulk_invalidate(self.subroutines.values())

        # Clear all data structures.
        self.local_labels: DefaultDict[int, Dict[str, int]] = defaultdict(bidict)
        self.instructions: DefaultDict[int, Set[InstructionID]] = defaultdict(set)
        self.subroutines: Dict[int, Subroutine] = SortedDict()
        self.subroutines_by_label: Dict[str, Subroutine] = {}
        self.references: DefaultDict[int, Set[Tuple[int, int]]] = defaultdict(set)
        gc.collect()

        # Add entry points.
        for pc, entry in self.entry_points.items():
            self.add_subroutine(pc, label=entry.name, stack_trace=[])

        self.dirty = False

    def analyze(self, preserve_labels=True) -> None:
        # Clear the current results.
        if self.instructions:
            self._clear(preserve_labels)

        # Start emulation from all entry points.
        for subroutine_pc, (name, p) in self.entry_points.items():
            cpu = CPU(self, subroutine_pc, p, subroutine_pc)
            cpu.run()

        # Generate labels for newly discovered code.
        self._generate_labels()
        gc.collect()

    def save(self) -> Dict[str, Any]:
        self._preserve_labels()
        return {
            "entry_points": self.entry_points,
            "instruction_assertions": self.instruction_assertions,
            "subroutine_assertions": self.subroutine_assertions,
            "preserved_labels": self.preserved_labels,
            "comments": self.comments,
        }

    def load(self, data: Dict[str, Any]) -> None:
        self.entry_points = data["entry_points"]
        self.instruction_assertions = data["instruction_assertions"]
        self.subroutine_assertions = data["subroutine_assertions"]
        self.preserved_labels = data["preserved_labels"]
        self.comments = data["comments"]

        self.analyze(preserve_labels=False)

    def add_entry_point(self, pc: int, name: str, state: State):
        if (pc in self.entry_points) or (pc in self.instructions):
            raise GilgameshError("This address is already covered by the analysis.")
        self.entry_points[pc] = EntryPoint(name, state.p)
        self.dirty = True

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc].add(instruction.id)
        subroutine = self.subroutines[instruction.subroutine]
        subroutine.add_instruction(instruction)

        if instruction.pc in self.instruction_assertions:
            subroutine.instruction_has_asserted_state_change = True

    def add_subroutine(
        self, pc: int, label: str = "", stack_trace: List[int] = None
    ) -> None:
        if self.rom.is_ram(pc):
            return
        if stack_trace is None:
            stack_trace = []

        # Assign a label to the subroutine (or retrieve the existing one).
        preserved_label = self.preserved_labels.get(pc)
        if preserved_label:
            label = preserved_label
        elif not label:
            label = "sub_{:06X}".format(pc)

        # Create and register subroutine (unless it exists already).
        subroutine = self.subroutines.get(pc)
        if subroutine is None:
            subroutine = Subroutine(self, pc, label, stack_trace)
            self.subroutines[pc] = subroutine
            self.subroutines_by_label[label] = subroutine

        # Apply existing state change assertions.
        state_changes = self.subroutine_assertions.get(pc, {})
        for state_change in state_changes.items():
            subroutine.assert_state_change(*state_change)

    def add_subroutine_state(
        self, instruction_pc: int, subroutine_pc: int, state_change: StateChange
    ) -> None:
        # Try to retrieve a state change assertion, if it exists.
        try:
            state_change = self.subroutine_assertions[subroutine_pc][instruction_pc]
        except KeyError:
            pass

        # Keep track of the processor state changes
        # caused by the execution of a subroutine.
        subroutine = self.subroutines[subroutine_pc]
        subroutine.state_changes[instruction_pc] = state_change

    def assert_instruction_state_change(
        self, instruction_pc: int, state_change: StateChange
    ) -> None:
        self.instruction_assertions[instruction_pc] = state_change
        self.dirty = True

    def deassert_instruction_state_change(self, instruction_pc: int) -> None:
        self.instruction_assertions.pop(instruction_pc, None)
        self.dirty = True

    def assert_subroutine_state_change(
        self, instruction_pc: int, subroutine: Subroutine, state_change: StateChange
    ) -> None:
        if subroutine.pc not in self.subroutine_assertions:
            self.subroutine_assertions[subroutine.pc] = {}
        self.subroutine_assertions[subroutine.pc][instruction_pc] = state_change
        self.dirty = True

    def deassert_subroutine_state_change(
        self, instruction_pc: int, subroutine_pc: int
    ) -> None:
        sub_assertions = self.subroutine_assertions.get(subroutine_pc, None)
        if sub_assertions:
            sub_assertions.pop(instruction_pc, None)
            if not sub_assertions:
                del self.subroutine_assertions[subroutine_pc]
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
            return self.local_labels[subroutine_pc].get(label[1:])

        return None

    def rename_label(
        self, old: str, new: str, subroutine_pc: Optional[int] = None, dry=False
    ) -> None:
        if old.startswith("."):
            if subroutine_pc is None:
                raise GilgameshError("No selected subroutine.")
            if not new.startswith("."):
                raise GilgameshError(
                    "Tried to transform a local label into a global one."
                )
            self._rename_local_label(old[1:], new[1:], subroutine_pc, dry)
        else:
            if new.startswith("."):
                raise GilgameshError(
                    "Tried to transform a subroutine into a local label."
                )
            self._rename_subroutine(old, new, dry)

    def _rename_local_label(
        self, old: str, new: str, subroutine_pc: int, dry=False
    ) -> None:
        local_labels = self.local_labels[subroutine_pc]
        pc = local_labels.get(old, None)
        if pc is None:
            raise GilgameshError(f'Unknown local label: "{old}".')
        elif not dry:
            del local_labels[old]

        if not new.isidentifier():
            raise GilgameshError("The provided label is not a valid identifier.")
        if new in local_labels:
            raise GilgameshError("The provided label is already in use.")

        if not dry:
            local_labels[new] = pc

    def _rename_subroutine(self, old: str, new: str, dry=False) -> None:
        subroutine = self.subroutines_by_label.get(old, None)
        if subroutine is None:
            raise GilgameshError(f'Unknown subroutine label: "{old}".')
        elif not dry:
            del self.subroutines_by_label[old]

        if not new.isidentifier():
            raise GilgameshError("The provided label is not a valid identifier.")
        if new in self.subroutines_by_label:
            raise GilgameshError("The provided label is already in use.")

        if not dry:
            subroutine.label = new
            self.subroutines_by_label[new] = subroutine

    def is_visited(self, instruction_id: InstructionID) -> bool:
        elements = self.instructions.get(instruction_id.pc, set())
        return instruction_id in elements

    @property
    def num_suspect_subroutines(self) -> int:
        return sum(
            1 if s.has_suspect_instructions else 0 for s in self.subroutines.values()
        )

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
