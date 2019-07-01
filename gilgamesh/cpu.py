from copy import copy

from .instruction import Instruction, InstructionID
from .opcodes import Op
from .state import State


class CPU:
    def __init__(self, log, pc: int, p: int, subroutine: int):
        self.log = log
        self.rom = log.rom
        self.pc = pc
        self.state = State(p)
        self.subroutine = subroutine

    @property
    def instruction_id(self) -> InstructionID:
        return InstructionID(self.pc, self.state.p, self.subroutine)

    def copy(self) -> "CPU":
        cpu = copy(self)
        cpu.state = copy(self.state)
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

        if instruction.is_return:
            return False
        elif instruction.is_jump:
            self.jump(instruction)
        elif instruction.is_branch:
            self.branch(instruction)
        elif instruction.is_call:
            self.call(instruction)
        elif instruction.is_sep_rep:
            self.sep_rep(instruction)

        return True

    def branch(self, instruction: Instruction) -> None:
        target = instruction.absolute_argument
        self.log.add_reference(instruction.pc, target)

        cpu = self.copy()
        cpu.pc = target
        cpu.run()

    def call(self, instruction: Instruction) -> None:
        target = instruction.absolute_argument
        self.log.add_reference(instruction.pc, target)
        self.log.add_subroutine(target, self.state.p)

        cpu = self.copy()
        cpu.subroutine = target
        cpu.pc = target
        cpu.run()

    def jump(self, instruction: Instruction) -> None:
        target = instruction.absolute_argument
        self.log.add_reference(instruction.pc, target)
        self.pc = target

    def sep_rep(self, instruction: Instruction) -> None:
        if instruction.operation == Op.SEP:
            self.state.set(instruction.absolute_argument)
        else:
            self.state.reset(instruction.absolute_argument)

    @staticmethod
    def is_ram(address: int) -> bool:
        return (address <= 0x001FFF) or (0x7E0000 <= address <= 0x7FFFFF)
