from copy import copy
from typing import List, Tuple

from typing_extensions import Literal

from .instruction import Instruction, InstructionID
from .opcodes import AddressMode, Op
from .state import State, StateChange


class CPU:
    def __init__(self, log, pc: int, p: int, subroutine: int):
        self.log = log
        self.rom = log.rom
        self.pc = pc
        self.state = State(p)
        self.state_assertion = StateChange()
        self.state_change = StateChange()
        self.state_stack: List[Tuple[State, StateChange]] = []
        self.subroutine = subroutine

    @property
    def instruction_id(self) -> InstructionID:
        return InstructionID(self.pc, self.state.p, self.subroutine)

    def copy(self, new_subroutine=False) -> "CPU":
        cpu = copy(self)
        cpu.state = copy(self.state)
        cpu.state_assertion = copy(self.state_assertion)
        cpu.state_change = StateChange() if new_subroutine else copy(self.state_change)
        return cpu

    def run(self) -> None:
        keep_going = self.step()
        while keep_going:
            keep_going = self.step()

    def step(self) -> bool:
        if self.is_ram(self.pc):
            return False
        if self.log.is_visited(self.instruction_id):
            return False

        opcode = self.rom.read_byte(self.pc)
        argument = self.rom.read_address(self.pc + 1)

        instruction = Instruction(self.log, *self.instruction_id, opcode, argument)
        self.log.add_instruction(instruction)

        return self.execute(instruction)

    def execute(self, instruction: Instruction) -> bool:
        self.pc += instruction.size

        self._derive_state_assertion(instruction)

        if instruction.is_return:
            self.log.add_subroutine_state(self.subroutine, self.state_change)
            return False
        elif instruction.is_interrupt:
            return self._unknown_subroutine_state()
        elif instruction.is_call:
            return self.call(instruction)
        elif instruction.is_jump:
            return self.jump(instruction)
        elif instruction.is_branch:
            self.branch(instruction)
        elif instruction.is_sep_rep:
            self.sep_rep(instruction)
        elif instruction.operation == Op.PHP:
            self.push_state()
        elif instruction.operation == Op.PLP:
            self.pop_state()

        return True

    def branch(self, instruction: Instruction) -> None:
        cpu = self.copy()
        cpu.run()

        target = instruction.absolute_argument
        self.log.add_reference(instruction, target)
        self.pc = target

    def call(self, instruction: Instruction) -> bool:
        target = instruction.absolute_argument
        if target is None:
            return self._unknown_subroutine_state()

        self.log.add_reference(instruction, target)
        self.log.add_subroutine(target)

        cpu = self.copy(new_subroutine=True)
        cpu.subroutine = target
        cpu.pc = target
        cpu.run()

        known = self._propagate_subroutine_state(target)
        if not known:
            return self._unknown_subroutine_state()
        return known

    def jump(self, instruction: Instruction) -> bool:
        target = instruction.absolute_argument
        if target is None:
            return self._unknown_subroutine_state()
        self.log.add_reference(instruction, target)
        self.pc = target
        return True

    def sep_rep(self, instruction: Instruction) -> None:
        arg = instruction.absolute_argument
        if instruction.operation == Op.SEP:
            self.state.set(arg)
            self.state_change.set(arg)
        else:
            self.state.reset(arg)
            self.state_change.reset(arg)
        self.state_change.apply_assertion(self.state_assertion)

    def push_state(self) -> None:
        self.state_stack.append((copy(self.state), copy(self.state_change)))

    def pop_state(self) -> None:
        self.state, self.state_change = self.state_stack.pop()

    @staticmethod
    def is_ram(address: int) -> bool:
        return (address <= 0x001FFF) or (0x7E0000 <= address <= 0x7FFFFF)

    def _derive_state_assertion(self, instruction: Instruction) -> None:
        saved_assertion = self.log.state_assertions.get(instruction.pc)
        if saved_assertion:
            if saved_assertion.m is not None:
                self.state_assertion.m = saved_assertion.m
            if saved_assertion.x is not None:
                self.state_assertion.x = saved_assertion.x
            return

        if (
            instruction.address_mode == AddressMode.IMMEDIATE_M
            and self.state_change.m is None
        ):
            self.state_assertion.m = self.state.m
        elif (
            instruction.address_mode == AddressMode.IMMEDIATE_X
            and self.state_change.x is None
        ):
            self.state_assertion.x = self.state.x

    def _propagate_subroutine_state(self, subroutine: int) -> bool:
        state_changes = self.log.get_subroutine_states(subroutine)
        if len(state_changes) != 1:
            return False

        change = next(iter(state_changes))
        if change.unknown:
            return False

        if change.m is not None:
            self.state_change.m = self.state.m = change.m
        if change.x is not None:
            self.state_change.x = self.state.x = change.x

        return True

    def _unknown_subroutine_state(self) -> Literal[False]:
        self.log.add_subroutine_state(self.subroutine, StateChange(unknown=True))
        return False
