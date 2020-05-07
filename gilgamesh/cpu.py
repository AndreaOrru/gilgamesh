from copy import copy
from typing import List, Tuple

from typing_extensions import Literal

from gilgamesh.instruction import Instruction, InstructionID
from gilgamesh.opcodes import AddressMode, Op
from gilgamesh.state import State, StateChange


class CPU:
    def __init__(self, log, pc: int, p: int, subroutine: int):
        self.log = log
        self.rom = log.rom

        # Processor state.
        self.pc = pc
        self.state = State(p)

        # Change in CPU state caused by the execution of the current subroutine.
        self.state_change = StateChange()
        # What we know about the CPU state based on the
        # sequence of instructions we have executed.
        self.state_inference = StateChange()

        # Stack formed as a result of sequences of PHP/PLP instructions.
        self.state_stack: List[Tuple[State, StateChange]] = []
        # The subroutine currently being executed.
        self.subroutine = subroutine

    @property
    def instruction_id(self) -> InstructionID:
        # Get the ID of the instruction currently being executed
        # in the context of the current subroutine.
        return InstructionID(self.pc, self.state.p, self.subroutine)

    def copy(self, new_subroutine=False) -> "CPU":
        # Copy the current state of the CPU.
        cpu = copy(self)
        cpu.state = copy(self.state)
        cpu.state_inference = copy(self.state_inference)
        # Don't carry over the state change information to new subroutines.
        cpu.state_change = StateChange() if new_subroutine else copy(self.state_change)
        return cpu

    def run(self) -> None:
        keep_going = self.step()
        while keep_going:
            keep_going = self.step()

    def step(self) -> bool:
        # We can't analyze code that lives in RAM.
        if self.is_ram(self.pc):
            return False
        # Don't visit the exact same instruction twice.
        if self.log.is_visited(self.instruction_id):
            return False

        opcode = self.rom.read_byte(self.pc)
        argument = self.rom.read_address(self.pc + 1)

        instruction = Instruction(self.log, *self.instruction_id, opcode, argument)
        self.log.add_instruction(instruction)

        return self.execute(instruction)

    def execute(self, instruction: Instruction) -> bool:
        self.pc += instruction.size

        # See if we can learn something about the *required*
        # state of the CPU based on the current instruction.
        self._derive_state_inference(instruction)

        if instruction.is_return:
            self.log.add_subroutine_state(self.subroutine, self.state_change)
            return False  # Terminate the execution of this subroutine.
        elif instruction.is_interrupt:
            return self._unknown_subroutine_state(instruction)
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

        return True  # Keep executing in the context of this subroutine.

    def branch(self, instruction: Instruction) -> None:
        # Run a parallel instance of the CPU to follow
        # the case in which we don't take the branch.
        cpu = self.copy()
        cpu.run()

        target = instruction.absolute_argument
        assert target is not None

        # Log the fact that the current instruction references the
        # instruction pointed by the branch. Then take the branch.
        self.log.add_reference(instruction, target)
        self.pc = target

    def call(self, instruction: Instruction) -> bool:
        target = instruction.absolute_argument
        if target is None:
            # If we can't reliably derive the address of the subroutine
            # being called, we're left in an unknown state.
            return self._unknown_subroutine_state(instruction)

        self.log.add_reference(instruction, target)
        self.log.add_subroutine(target)

        # Run a parallel instance of the CPU to execute
        # the subroutine that is being called.
        cpu = self.copy(new_subroutine=True)
        cpu.subroutine = target
        cpu.pc = target
        cpu.run()

        # If we univocally know what the return state of the
        # called subroutine is, we can propagate it to the
        # current CPU state. Otherwise, to be on the safe
        # side, we need to stop the execution.
        known = self._propagate_subroutine_state(target)
        if not known:
            return self._unknown_subroutine_state(instruction)
        return True

    def jump(self, instruction: Instruction) -> bool:
        target = instruction.absolute_argument
        if target is None:
            return self._unknown_subroutine_state(instruction)
        self.log.add_reference(instruction, target)
        self.pc = target
        return True

    def sep_rep(self, instruction: Instruction) -> None:
        arg = instruction.absolute_argument
        assert arg is not None

        if instruction.operation == Op.SEP:
            self.state.set(arg)
            self.state_change.set(arg)
        else:
            self.state.reset(arg)
            self.state_change.reset(arg)

        # Simplify the state change by applying our knowledge
        # of the current state. I.e. if we know that the
        # processor is operating in 8-bits accumulator mode
        # and we switch to that same mode, effectively no
        # state change is being performed.
        self.state_change.apply_inference(self.state_inference)

    def push_state(self) -> None:
        self.state_stack.append((copy(self.state), copy(self.state_change)))

    def pop_state(self) -> None:
        self.state, self.state_change = self.state_stack.pop()

    @staticmethod
    def is_ram(address: int) -> bool:
        return (address <= 0x001FFF) or (0x7E0000 <= address <= 0x7FFFFF)

    def _derive_state_inference(self, instruction: Instruction) -> None:
        # If we're executing an instruction with a certain operand size,
        # and no state change has been performed in the current subroutine,
        # then we can infer that the state of the processor as we enter
        # the subroutine *must* be the same in all cases.
        if (
            instruction.address_mode == AddressMode.IMMEDIATE_M
            and self.state_change.m is None
        ):
            self.state_inference.m = self.state.m
        elif (
            instruction.address_mode == AddressMode.IMMEDIATE_X
            and self.state_change.x is None
        ):
            self.state_inference.x = self.state.x

    def _propagate_subroutine_state(self, subroutine_pc: int) -> bool:
        # If the subroutine can return in more than one distinct state, or its
        # state is unknown, we can't reliably propagate the state to the caller.
        subroutine = self.log.subroutines[subroutine_pc]
        if subroutine.has_unknown_return_state():
            return False

        change = subroutine.state_change
        if change.m is not None:
            self.state_change.m = self.state.m = change.m
        if change.x is not None:
            self.state_change.x = self.state.x = change.x

        return True

    def _unknown_subroutine_state(self, instruction: Instruction) -> Literal[False]:
        self.log.add_subroutine_state(self.subroutine, StateChange(unknown=True))
        instruction.stopped_execution = True
        return False
