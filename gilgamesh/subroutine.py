from typing import Dict, Optional, Set

from sortedcontainers import SortedDict  # type: ignore

from gilgamesh.instruction import Instruction
from gilgamesh.state import State, StateChange


class Subroutine:
    def __init__(self, log, pc: int, label: str):
        self.log = log
        self.pc = pc
        self.label = label

        # Instructions belonging to the subroutine.
        self.instructions: Dict[int, Instruction] = SortedDict()
        # Calling the subroutine results in the following state changes.
        self.state_changes: Set[StateChange] = set()

        self.asserted_state_change = False

    @property
    def local_labels(self) -> Dict[str, int]:
        return self.log.local_labels[self.pc]

    @property
    def state_change(self) -> StateChange:
        assert len(self.state_changes) == 1
        return next(iter(self.state_changes))

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction

    def assert_state_change(self, state_change: StateChange) -> None:
        self.state_changes = {state_change}
        self.asserted_state_change = True

    def check_unknown_return_state(self, state: Optional[State] = None) -> bool:
        # Try to simplify the state changes based on the caller state.
        if state:
            simplified_changes = set()
            while self.state_changes:
                change = self.state_changes.pop()
                change.simplify(state)
                simplified_changes.add(change)
            self.state_changes = simplified_changes

        if len(self.state_changes) != 1 or self.state_change.unknown:
            return True

        return False
