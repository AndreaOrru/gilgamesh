from typing import Dict, Set, Tuple

from sortedcontainers import SortedDict  # type: ignore

from gilgamesh.instruction import Instruction
from gilgamesh.opcodes import Op
from gilgamesh.state import State, StateChange
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
        self.state_changes: Set[StateChange] = set()

        self.has_jump_table = False
        self.has_suspicious_instructions = False
        self.has_asserted_state_change = False
        self.instruction_has_asserted_state_change = False

    @property
    def local_labels(self) -> Dict[str, int]:
        return self.log.local_labels[self.pc]

    @property
    def state_change(self) -> StateChange:
        assert len(self.state_changes) == 1
        return next(iter(self.state_changes))

    @property
    def has_unknown_return_state(self) -> bool:
        return any(s for s in self.state_changes if s.unknown)

    def invalidate(self) -> None:
        bulk_invalidate(self.instructions.values())
        super().invalidate()

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction

        if instruction.operation == Op.BRK:
            self.has_suspicious_instructions = True
        elif (instruction.absolute_argument is None) and (
            instruction.is_jump or instruction.is_call
        ):
            self.has_jump_table = True

    def assert_state_change(self, state_change: StateChange) -> None:
        self.state_changes = {state_change}
        self.has_asserted_state_change = True

    def simplify_return_states(self, state: State) -> Tuple[Set[StateChange], bool]:
        assert len(self.state_changes) > 0

        # Simplify the state changes based on the caller state.
        unknown = False
        changes = set()

        for change in self.state_changes:
            changes.add(change.simplify(state))
            if change.unknown:
                unknown = True

        return changes, unknown
