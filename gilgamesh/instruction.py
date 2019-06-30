from collections import namedtuple
from typing import Optional

from .opcodes import AddressMode, Op, argument_size_table, opcode_table
from .state import State
from .types import s8, s16

InstructionID = namedtuple("InstructionID", ["pc", "p", "subroutine"])


class Instruction:
    def __init__(self, pc: int, p: int, subroutine: int, opcode: int, argument: int):
        self.pc = pc
        self.state = State(p)
        self.subroutine = subroutine
        self.opcode = opcode
        self._argument = argument

    @property
    def id(self) -> InstructionID:
        return InstructionID(self.pc, self.state.p, self.subroutine)

    @property
    def name(self) -> str:
        return self.operation.name.lower()

    @property
    def operation(self) -> Op:
        return opcode_table[self.opcode][0]

    @property
    def address_mode(self) -> AddressMode:
        return opcode_table[self.opcode][1]

    @property
    def size(self) -> int:
        return self.argument_size + 1

    @property
    def argument_size(self) -> int:
        size = argument_size_table[self.address_mode]
        if size is not None:
            return size

        if self.address_mode == AddressMode.IMMEDIATE_M:
            return self.state.a_size
        elif self.address_mode == AddressMode.IMMEDIATE_X:
            return self.state.x_size
        assert False

    @property
    def argument(self) -> Optional[int]:
        if self.argument_size == 1:
            return self._argument & 0xFF
        elif self.argument_size == 2:
            return self._argument & 0xFFFF
        elif self.argument_size == 3:
            return self._argument & 0xFFFFFF
        return None

    @property
    def absolute_argument(self) -> Optional[int]:
        if self.address_mode in (
            AddressMode.IMMEDIATE_M,
            AddressMode.IMMEDIATE_X,
            AddressMode.IMMEDIATE_8,
            AddressMode.ABSOLUTE_LONG,
        ):
            return self.argument

        elif self.address_mode == AddressMode.ABSOLUTE and self.is_control:
            assert self.argument is not None
            return (self.pc & 0xFF0000) | self.argument

        elif self.address_mode == AddressMode.RELATIVE:
            assert self.size is not None
            return self.pc + self.size + s8(self.argument)

        elif self.address_mode == AddressMode.RELATIVE_LONG:
            assert self.size is not None
            return self.pc + self.size + s16(self.argument)

        return None

    @property
    def is_branch(self) -> bool:
        return self.operation in (
            Op.BCC,
            Op.BCS,
            Op.BEQ,
            Op.BMI,
            Op.BNE,
            Op.BPL,
            Op.BVC,
            Op.BVS,
        )

    @property
    def is_call(self) -> bool:
        return self.operation in (Op.JSL, Op.JSR)

    @property
    def is_jump(self) -> bool:
        return self.operation in (Op.BRA, Op.BRL, Op.JMP, Op.JML)

    @property
    def is_return(self) -> bool:
        return self.operation in (Op.RTI, Op.RTL, Op.RTS)

    @property
    def is_interrupt(self) -> bool:
        return self.operation in (Op.BRK, Op.RTI)

    @property
    def is_control(self) -> bool:
        return (
            self.is_branch
            or self.is_call
            or self.is_jump
            or self.is_return
            or self.is_interrupt
        )

    @property
    def is_sep_rep(self) -> bool:
        return self.operation in (Op.SEP, Op.REP)
