from copy import copy
from typing import List, Optional, Tuple

from gilgamesh.snes.instruction import Instruction, InstructionID, StackManipulation
from gilgamesh.snes.opcodes import AddressMode, Op
from gilgamesh.snes.registers import Registers
from gilgamesh.snes.state import State, StateChange, UnknownReason
from gilgamesh.stack import Stack
from gilgamesh.subroutine import Subroutine


class CPU:
    def __init__(self, log, pc: int, p: int, subroutine: int):
        self.log = log
        self.rom = log.rom

        # Processor state.
        self.pc = pc
        self.state = State(p)
        self.registers = Registers(self.state)
        self.stack = Stack()

        # Change in CPU state caused by the execution of the current subroutine.
        self.state_change = StateChange()
        # What we know about the CPU state based on the
        # sequence of instructions we have executed.
        self.state_inference = StateChange()

        # The subroutine currently being executed.
        self.subroutine_pc = subroutine
        # The stack of calls that brought us to the current subroutine.
        self.stack_trace: List[int] = []

    @property
    def instruction_id(self) -> InstructionID:
        # Get the ID of the instruction currently being executed
        # in the context of the current subroutine.
        return InstructionID(self.pc, self.state.p, self.subroutine_pc)

    @property
    def subroutine(self) -> Subroutine:
        return self.log.subroutines[self.subroutine_pc]

    def copy(self, new_subroutine=False) -> "CPU":
        # Copy the current state of the CPU.
        cpu = copy(self)
        cpu.state = copy(self.state)
        cpu.registers = self.registers.copy(cpu.state)
        cpu.stack = self.stack.copy()  # TODO: check if necessary.
        cpu.stack_trace = copy(self.stack_trace)
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
        if self.rom.is_ram(self.pc):
            return False
        # Don't visit the exact same instruction twice.
        if self.log.is_visited(self.instruction_id):
            return False

        # Disassemble and log the instruction.
        opcode = self.rom.read_byte(self.pc)
        argument = self.rom.read_address(self.pc + 1)
        instruction = Instruction(
            self.log,
            *self.instruction_id,
            opcode,
            argument,
            self.registers.snapshot(),
            copy(self.state_change)
        )
        self.log.add_instruction(instruction)

        # Emulate the instruction.
        keep_going = self.execute(instruction)
        # Apply asserted state changes if any, and log it inside the instruction object.
        instruction.state_change_after = self._maybe_apply_asserted_state_change(
            instruction
        )

        return keep_going

    def execute(self, instruction: Instruction) -> bool:
        self.pc += instruction.size

        # See if we can learn something about the *required*
        # state of the CPU based on the current instruction.
        self._derive_state_inference(instruction)

        if instruction.is_return:
            return self.ret(instruction)
        elif instruction.is_interrupt:
            self._unknown_subroutine_state(
                instruction, unknown_reason=UnknownReason.SUSPECT_INSTRUCTION
            )
            return False
        elif instruction.is_call or instruction.is_jump:
            return self.call_or_jump(instruction)
        elif instruction.is_branch:
            self.branch(instruction)
        elif instruction.is_sep_rep:
            self.sep_rep(instruction)
        elif instruction.does_change_stack:
            self.change_stack(instruction)
        elif instruction.does_change_a:
            self.change_a(instruction)
        elif instruction.is_pop:
            return self.pop(instruction)
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

    def call_or_jump(self, i: Instruction) -> bool:
        if i.absolute_argument:
            targets: List[Tuple[Optional[int], int]] = [(None, i.absolute_argument)]
        else:
            targets = self.log.jump_assertions.get(i.pc, [(None, None)])

        if i.is_call:
            return self._call(i, targets)
        else:
            self._jump(i, targets)
            return False

    def _call(self, i: Instruction, targets: List[Tuple[Optional[int], int]]) -> bool:
        # Keep track of the state before the call.
        saved_state, saved_state_change = copy(self.state), copy(self.state_change)
        possible_states = set()

        for _, target in targets:
            if target is None:
                # If we can't reliably derive the address of the subroutine
                # being called, we're left in an unknown state.
                return self._unknown_subroutine_state(
                    i, unknown_reason=UnknownReason.INDIRECT_JUMP
                )

            # Run a parallel instance of the CPU to execute
            # the subroutine that is being called.
            cpu = self.copy(new_subroutine=True)
            call_size = 2 if i.operation in (Op.JSR, Op.RTS) else 3
            cpu.stack.push(i, i.pc, call_size)
            cpu.stack_trace.append(self.subroutine_pc)
            cpu.subroutine_pc = target
            cpu.pc = target

            # Emulate the called subroutine.
            self.log.add_reference(i, target)
            self.log.add_subroutine(target, stack_trace=cpu.stack_trace)
            cpu.run()

            # If we univocally know what the return state of the
            # called subroutine is, we can propagate it to the
            # current CPU state. Otherwise, to be on the safe
            # side, we need to stop the execution.
            known, unknown_reason = self._propagate_subroutine_state(i.pc, target)
            if known or self._unknown_subroutine_state(
                i, unknown_reason=unknown_reason
            ):
                possible_states.add((self.state, self.state_change))

            # Restore the state before this target was executed.
            self.state, self.saved_state_change = (
                copy(saved_state),
                copy(saved_state_change),
            )

        for state, state_change in possible_states:
            cpu = self.copy()
            cpu.state, cpu.state_change = state, state_change
            cpu.run()
        return False

    def _jump(self, i: Instruction, targets: List[Tuple[Optional[int], int]]) -> None:
        for _, target in targets:
            if target is None:
                self._unknown_subroutine_state(
                    i, unknown_reason=UnknownReason.INDIRECT_JUMP
                )
                return

            self.log.add_reference(i, target)
            cpu = self.copy()
            cpu.pc = target
            cpu.run()

    def ret(self, i: Instruction) -> bool:
        if i.operation != Op.RTI:
            ret_size = 2 if i.operation == Op.RTS else 3
            stack_entries = self.stack.pop(ret_size)

            # This return is used as an anomalous jump table.
            if i.is_jump_table:
                for s in stack_entries:
                    if s.instruction:
                        s.instruction.stack_manipulation = StackManipulation.HARMLESS

                # If the stack is constructed in such a way that
                # we would return to the next instruction, it is
                # effectively a subroutine call.
                if self.stack.match(i.pc, ret_size):
                    for s in self.stack.pop(ret_size):
                        if s.instruction:
                            s.instruction.stack_manipulation = (
                                StackManipulation.HARMLESS
                            )
                    return self._call(i, self.log.jump_assertions[i.pc])
                # Otherwise, it's a simple jump.
                else:
                    self._jump(i, self.log.jump_assertions[i.pc])
                    return False

            # Check whether this return is operating on a manipulated stack.
            else:
                call_op = (
                    (Op.JSR, Op.RTS) if i.operation == Op.RTS else (Op.JSL, Op.RTL)
                )
                # Non-call instructions which operated on the region of the
                # stack containing the return address from the subroutine.
                stack_manipulators = [
                    s.instruction
                    for s in stack_entries
                    if not s.instruction or s.instruction.operation not in call_op
                ]
                if stack_manipulators:
                    self._unknown_subroutine_state(
                        i,
                        unknown_reason=UnknownReason.STACK_MANIPULATION,
                        stack_manipulator=stack_manipulators[-1],
                    )
                    return False

        # Standard return.
        self.log.add_subroutine_state(self.subroutine.pc, i.pc, self.state_change)
        return False

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

    def change_a(self, i: Instruction) -> None:
        if i.address_mode == AddressMode.IMMEDIATE_M:
            assert i.argument is not None
            a = self.registers.a.get()

            if i.operation == Op.LDA:
                self.registers.a.set(i.argument)
            elif a is not None:
                if i.operation == Op.ADC:
                    # TODO: handle carry flag.
                    self.registers.a.set(a + i.argument)
                elif i.operation == Op.SBC:
                    # TODO: handle negative flag.
                    self.registers.a.set(a - i.argument)
        elif i.operation == Op.TSC:
            self.registers.a.set_whole(self.stack.pointer)
        elif i.operation == Op.PLA:
            self.stack.pop(self.state.a_size)
        else:
            self.registers.a.set(None)

    def change_stack(self, i: Instruction) -> None:
        if i.operation == Op.TCS:
            a = self.registers.a.get_whole()
            self.stack.set_pointer(i, a)
            if a is not None:
                return
        # We keep the disassembly going if the stack manipulation
        # doesn't otherwise influence the state of the processor.
        i.stack_manipulation = StackManipulation.HARMLESS

    def push(self, instruction: Instruction) -> None:
        if instruction.operation == Op.PHP:
            self.stack.push(instruction, (copy(self.state), copy(self.state_change)))
        elif instruction.operation == Op.PHA:
            self.stack.push(instruction, self.registers.a.get(), self.state.a_size)
        elif instruction.operation in (Op.PHX, Op.PHY):
            self.stack.push(instruction, size=self.state.x_size)
        elif instruction.operation in (Op.PHB, Op.PHK):
            self.stack.push(instruction)
        elif instruction.operation in (Op.PHD, Op.PEA, Op.PER):
            self.stack.push(instruction, size=2)
        else:
            assert False

    def pop(self, i: Instruction) -> bool:
        if i.operation == Op.PLP:
            entry = self.stack.pop_one()
            if entry.instruction and entry.instruction.operation == Op.PHP:
                self.state, self.state_change = entry.data
            # We can't trust the disassembly if we don't know
            # which state the PLP instruction is restoring.
            else:
                return self._unknown_subroutine_state(
                    i,
                    unknown_reason=UnknownReason.STACK_MANIPULATION,
                    stack_manipulator=entry.instruction,
                )

        elif i.operation in (Op.PLX, Op.PLY):
            self.stack.pop(self.state.x_size)
        elif i.operation == Op.PLB:
            self.stack.pop_one()
        elif i.operation == Op.PLD:
            self.stack.pop(2)
        else:
            assert False
        return True

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

    def _propagate_subroutine_state(
        self, call_pc: int, subroutine_pc: int
    ) -> Tuple[bool, UnknownReason]:
        known = True
        unknown_reason = UnknownReason.KNOWN

        # If the user defined a state assertion for the current instruction.
        if call_pc in self.log.instruction_assertions:
            return (known, unknown_reason)  # Execution can proceed.

        # If the subroutine can return in more than one distinct state, or its
        # state is unknown, we can't reliably propagate the state to the caller.
        subroutine = self.log.subroutines[subroutine_pc]
        return_states = subroutine.simplify_return_states(self.state)

        # Multiple known return states.
        if len([s for s in return_states if not s.unknown]) > 1:
            known = False
            unknown_reason = UnknownReason.MULTIPLE_RETURN_STATES
            self.log.add_subroutine_state(
                self.subroutine_pc, call_pc, StateChange(unknown_reason=unknown_reason)
            )
        # Unknown state with some reason.
        elif any(s.unknown for s in return_states):
            known = False
            unknown_state = [s for s in return_states if s.unknown][0]
            unknown_reason = unknown_state.unknown_reason
            self.log.add_subroutine_state(self.subroutine_pc, call_pc, unknown_state)

        # Unique return state, apply it.
        if known:
            assert len(return_states) == 1
            self._apply_state_change(return_states.pop())

        return (known, unknown_reason)

    def _unknown_subroutine_state(
        self,
        instruction: Instruction,
        unknown_reason: Optional[UnknownReason] = None,
        stack_manipulator: Optional[Instruction] = None,
    ) -> bool:
        # Check if the user defined a state assertion for the current instruction.
        if instruction.pc in self.log.instruction_assertions:
            return True  # Execution can proceed.

        # No custom assertion, we need to stop here.
        unknown_reason = unknown_reason or UnknownReason.UNKNOWN
        self.state_change = StateChange(unknown_reason=unknown_reason)
        self.log.add_subroutine_state(
            self.subroutine_pc, instruction.pc, copy(self.state_change)
        )

        # If the unknown state is due to stack manipulation:
        if unknown_reason == UnknownReason.STACK_MANIPULATION:
            # If we know which instruction performed the
            # manipulation, we flag it.
            if stack_manipulator:
                self.subroutine.has_stack_manipulation = True
                stack_manipulator.stack_manipulation = (
                    StackManipulation.CAUSES_UNKNOWN_STATE
                )

        return False

    def _apply_state_change(self, state_change: StateChange) -> None:
        if state_change.m is not None:
            self.state_change.m = self.state.m = state_change.m
        if state_change.x is not None:
            self.state_change.x = self.state.x = state_change.x

    def _maybe_apply_asserted_state_change(self, i: Instruction) -> StateChange:
        """Apply asserted state changes if any. Return the asserted
        state change if there is one, or a copy of the current state
        change otherwise."""
        asserted_state = self.log.instruction_assertions.get(i.pc)
        if asserted_state:
            self._apply_state_change(asserted_state)
            return asserted_state
        else:
            return copy(self.state_change)
