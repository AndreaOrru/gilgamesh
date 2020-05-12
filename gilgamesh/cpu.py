from copy import copy

from gilgamesh.instruction import Instruction, InstructionID
from gilgamesh.opcodes import AddressMode, Op
from gilgamesh.stack import Stack
from gilgamesh.state import State, StateChange


class CPU:
    def __init__(self, log, pc: int, p: int, subroutine: int):
        self.log = log
        self.rom = log.rom

        # Processor state.
        self.pc = pc
        self.state = State(p)
        self.stack = Stack()

        # Change in CPU state caused by the execution of the current subroutine.
        self.state_change = StateChange()
        # What we know about the CPU state based on the
        # sequence of instructions we have executed.
        self.state_inference = StateChange()

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
        cpu.stack = self.stack.copy()  # TODO: check if necessary.
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

        # Disassemble and log the instruction.
        opcode = self.rom.read_byte(self.pc)
        argument = self.rom.read_address(self.pc + 1)
        instruction = Instruction(self.log, *self.instruction_id, opcode, argument)
        self.log.add_instruction(instruction)

        # Emulate the instruction.
        keep_going = self.execute(instruction)

        # Apply asserted state changes, if any.
        asserted_state = self.log.instruction_assertions.get(instruction.pc)
        if asserted_state:
            self._apply_state_change(asserted_state)
        return keep_going

    def execute(self, instruction: Instruction) -> bool:
        self.pc += instruction.size

        # See if we can learn something about the *required*
        # state of the CPU based on the current instruction.
        self._derive_state_inference(instruction)

        if instruction.is_return:
            self.ret(instruction)
            return False  # Terminate the execution of this subroutine.
        elif instruction.is_interrupt:
            self._unknown_subroutine_state(instruction)
            return False
        elif instruction.is_call:
            return self.call(instruction)
        elif instruction.is_jump:
            return self.jump(instruction)
        elif instruction.is_branch:
            self.branch(instruction)
        elif instruction.is_sep_rep:
            self.sep_rep(instruction)
        elif instruction.is_pop:
            self.pop(instruction)
        elif instruction.is_push:
            self.push(instruction)

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
        call_size = 2 if instruction.operation == Op.JSR else 3
        cpu.stack.push(instruction, size=call_size)
        cpu.subroutine = target
        cpu.pc = target
        cpu.run()

        # If we univocally know what the return state of the
        # called subroutine is, we can propagate it to the
        # current CPU state. Otherwise, to be on the safe
        # side, we need to stop the execution.
        known = self._propagate_subroutine_state(instruction.pc, target)
        if not known:
            return self._unknown_subroutine_state(instruction)
        return True

    def jump(self, instruction: Instruction) -> bool:
        target = instruction.absolute_argument
        if target is None:
            self._unknown_subroutine_state(instruction)
            return False

        self.log.add_reference(instruction, target)
        self.pc = target
        return True

    def ret(self, instruction: Instruction) -> None:
        # Check whether this return is operating on a manipulated stack.
        if instruction.operation != Op.RTI:
            ret_size = 2 if instruction.operation == Op.RTS else 3
            if not all(s.instruction.is_call for s in self.stack.pop(ret_size)):
                self._unknown_subroutine_state(instruction)
                return

        # Standard return.
        self.log.add_subroutine_state(self.subroutine, self.state_change)

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

    def push(self, instruction: Instruction) -> None:
        if instruction.operation == Op.PHP:
            self.stack.push(instruction, (copy(self.state), copy(self.state_change)))
        elif instruction.operation == Op.PHA:
            self.stack.push(instruction, size=self.state.a_size)
        elif instruction.operation in (Op.PHX, Op.PHY):
            self.stack.push(instruction, size=self.state.x_size)
        elif instruction.operation == Op.PHB:
            self.stack.push(instruction)
        elif instruction.operation in (Op.PHD, Op.PEA):
            self.stack.push(instruction, size=2)
        else:
            assert False

    def pop(self, instruction: Instruction) -> None:
        if instruction.operation == Op.PLP:
            stack_entry = self.stack.pop_one()
            assert stack_entry.instruction.operation == Op.PHP
            self.state, self.state_change = stack_entry.data
        elif instruction.operation == Op.PLA:
            self.stack.pop(self.state.a_size)
        elif instruction.operation in (Op.PLX, Op.PLY):
            self.stack.pop(self.state.x_size)
        elif instruction.operation == Op.PLB:
            self.stack.pop_one()
        elif instruction.operation == Op.PLD:
            self.stack.pop(2)
        else:
            assert False

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

    def _propagate_subroutine_state(self, call_pc: int, subroutine_pc: int) -> bool:
        # If the user defined a state assertion for the current instruction.
        if call_pc in self.log.instruction_assertions:
            return True  # Execution can proceed.

        # If the subroutine can return in more than one distinct state, or its
        # state is unknown, we can't reliably propagate the state to the caller.
        subroutine = self.log.subroutines[subroutine_pc]
        return_states, unknown = subroutine.simplify_return_states(self.state)
        if len(return_states) > 1 or unknown:
            return False

        # Unique return state, apply it.
        self._apply_state_change(return_states.pop())
        return True

    def _unknown_subroutine_state(self, instruction: Instruction) -> bool:
        # Check if the user defined a state assertion for the current instruction.
        if instruction.pc in self.log.instruction_assertions:
            return True  # Execution can proceed.

        # No custom assertion, we need to stop here.
        self.log.add_subroutine_state(self.subroutine, StateChange(unknown=True))
        instruction.stopped_execution = True
        return False

    def _apply_state_change(self, state_change: StateChange) -> None:
        if state_change.m is not None:
            self.state_change.m = self.state.m = state_change.m
        if state_change.x is not None:
            self.state_change.x = self.state.x = state_change.x
