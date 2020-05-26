from typing import Dict, List, Optional, Set, Tuple

from cached_property import cached_property  # type: ignore
from sortedcontainers import SortedDict  # type: ignore

from gilgamesh.snes.instruction import Instruction
from gilgamesh.snes.opcodes import Op
from gilgamesh.snes.state import State, StateChange, UnknownReason
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
        self.stack_traces: Set[Tuple[int, ...]] = set()

        # Whether an instruction inside the subroutine performs stack manipulation.
        self.has_stack_manipulation = False
        # Whether a subroutine calls itself down the line.
        self.is_recursive = False

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
    def is_jump_table_target(self) -> bool:
        return self.pc in self.log.jump_table_targets

    @property
    def has_asserted_state_change(self) -> bool:
        return any(s.asserted for s in self.state_changes.values())

    @property
    def has_unknown_return_state(self) -> bool:
        return any(s.unknown for s in self.state_changes.values())

    @property
    def is_responsible_for_unknown_state(self) -> bool:
        return self.has_unknown_return_state and (
            self.has_suspect_instructions
            or self.has_stack_manipulation
            or self.indirect_jumps
            or self.is_recursive
        )

    @cached_property
    def instruction_has_asserted_state_change(self) -> bool:
        return any(i.has_asserted_state_change for i in self.instructions.values())

    @cached_property
    def indirect_jumps(self) -> List[int]:
        return [i.pc for i in self.instructions.values() if i.is_indirect_jump]

    @cached_property
    def has_suspect_instructions(self) -> bool:
        return any(i.operation == Op.BRK for i in self.instructions.values())

    @cached_property
    def does_save_state_in_incipit(self) -> bool:
        for i in self.instructions.values():
            if i.operation == Op.PHP:
                return True
            elif i.is_sep_rep or i.is_control:
                return False
        return False

    @property
    def has_incomplete_jump_table(self) -> bool:
        return any(i not in self.log.complete_jump_tables for i in self.indirect_jumps)

    @property
    def has_multiple_known_state_changes(self) -> bool:
        return len([s for s in self.state_changes.values() if not s.unknown]) > 1

    @property
    def unified_state_change(self) -> Optional[StateChange]:
        if sum(1 for s in self.state_changes.values() if s.unknown) > 1:
            return None
        unified = StateChange()
        for s in self.state_changes.values():
            if s.unknown:
                continue
            if s.m is not None:
                if (unified.m is not None) and (s.m != unified.m):
                    return None
                unified.m = s.m
            if s.x is not None:
                if (unified.x is not None) and (s.x != unified.x):
                    return None
                unified.x = s.x
        return unified

    def invalidate(self) -> None:
        bulk_invalidate(self.instructions.values())
        super().invalidate()

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions[instruction.pc] = instruction

    def assert_state_change(
        self, instruction_pc: int, state_change: StateChange
    ) -> None:
        self.state_changes[instruction_pc] = state_change

    def simplify_return_states(self, state: State) -> List[StateChange]:
        if len(self.state_changes) == 0:
            self.is_recursive = True
            return [StateChange(unknown_reason=UnknownReason.RECURSION)]

        # Simplify the state changes based on the caller state.
        changes = set()
        for change in self.state_changes.values():
            changes.add(change.simplify(state))
        return list(changes)
