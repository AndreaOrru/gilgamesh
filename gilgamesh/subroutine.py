from typing import Dict, Set, Tuple

from cached_property import cached_property  # type: ignore
from sortedcontainers import SortedDict  # type: ignore

from gilgamesh.snes.instruction import Instruction
from gilgamesh.snes.opcodes import Op
from gilgamesh.snes.state import State, StateChange
from gilgamesh.stack import StackTraceEntry
from gilgamesh.utils.invalidable import Invalidable, bulk_invalidate


class Subroutine(Invalidable):
    def __init__(self, log, pc: int, label: str):
        super().__init__()
        self.log = log
        self.pc = pc
        self.label = label

        # Instructions belonging to the subroutine.
        self.instructions: Dict[int, Instruction] = SortedDict()
        # Calling the subroutine results in the following state changes.
        self.state_changes: Dict[int, StateChange] = {}
        # The stack of calls that brought us to the current subroutine.
        self.stack_traces: Set[Tuple[StackTraceEntry, ...]] = set()

        # Whether an instruction inside the subroutine performs stack manipulation.
        self.has_stack_manipulation = False

    @property
    def local_labels(self) -> Dict[str, int]:
        return self.log.local_labels[self.pc]

    @property
    def state_change(self) -> StateChange:
        assert len(self.state_changes) == 1
        return next(iter(self.state_changes.values()))

    @property
    def is_entry_point(self) -> bool:
        return self.pc in self.log.entry_points

    @property
    def has_asserted_state_change(self) -> bool:
        return any(s.asserted for s in self.state_changes.values())

    @property
    def has_unknown_return_state(self) -> bool:
        return any(s.unknown for s in self.state_changes.values())

    @cached_property
    def instruction_has_asserted_state_change(self) -> bool:
        return any(i.has_asserted_state_change for i in self.instructions.values())

    @cached_property
    def has_suspect_instructions(self) -> bool:
        return any(i.operation == Op.BRK for i in self.instructions.values())

    @cached_property
    def has_jump_table(self) -> bool:
        return any(
            (i.is_jump or i.is_call) and (i.absolute_argument is None)
            for i in self.instructions.values()
        )

    def invalidate(self) -> None:
        bulk_invalidate(self.instructions.values())
        super().invalidate()

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction

    def assert_state_change(
        self, instruction_pc: int, state_change: StateChange
    ) -> None:
        self.state_changes[instruction_pc] = state_change

    def simplify_return_states(self, state: State) -> Tuple[Set[StateChange], bool]:
        assert len(self.state_changes) > 0

        # Simplify the state changes based on the caller state.
        unknown = False
        changes = set()

        for change in self.state_changes.values():
            changes.add(change.simplify(state))
            if change.unknown:
                unknown = True

        return changes, unknown
