from collections import namedtuple
from typing import Optional

from cached_property import cached_property  # type: ignore

from gilgamesh.opcodes import AddressMode, Op, argument_size_table, opcode_table
from gilgamesh.signed_types import s8, s16
from gilgamesh.state import State

# The same instruction can be executed in different states or as
# part of different subroutines. We define a InstructionID struct
# as the unique identifier of an instruction executed in a specific
# state and subroutine.
InstructionID = namedtuple("InstructionID", ["pc", "p", "subroutine"])


class Instruction:
    def __init__(
        self, log, pc: int, p: int, subroutine: int, opcode: int, argument: int
    ):
        self.log = log
        self.pc = pc
        self.state = State(p)

        self.subroutine = subroutine
        self.opcode = opcode
        self._argument = argument

        self.stopped_execution = False

    def __repr__(self) -> str:
        return "<{}{}>".format(
            self.name.upper(),
            f" {self.argument_string}" if self.argument_string else "",
        )

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

    @cached_property
    def absolute_argument(self) -> Optional[int]:
        # Addressing modes whose argument is fully specified.
        if self.address_mode in (
            AddressMode.IMMEDIATE_M,
            AddressMode.IMMEDIATE_X,
            AddressMode.IMMEDIATE_8,
            AddressMode.ABSOLUTE_LONG,
        ):
            return self.argument

        # JMP $xxxx -> PB:xxxx
        elif self.address_mode == AddressMode.ABSOLUTE and self.is_control:
            assert self.argument is not None
            return (self.pc & 0xFF0000) | self.argument

        # Bxx .label
        elif self.address_mode == AddressMode.RELATIVE:
            assert (self.size is not None) and (self.argument is not None)
            return self.pc + self.size + s8(self.argument)

        # BRL .label
        elif self.address_mode == AddressMode.RELATIVE_LONG:
            assert (self.size is not None) and (self.argument is not None)
            return self.pc + self.size + s16(self.argument)

        # Other addressing modes depend on context we don't know.
        return None

    @property
    def next_pc(self) -> int:
        return self.pc + self.size

    @property
    def label(self) -> Optional[str]:
        return self.log.get_label(self.pc, self.subroutine)

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

    @cached_property
    def argument_string(self) -> str:
        if self.address_mode == AddressMode.IMPLIED:
            return ""

        elif self.address_mode == AddressMode.IMPLIED_ACCUMULATOR:
            return "a"

        assert self.argument is not None
        assert self.argument_size is not None

        if self.address_mode in (
            AddressMode.IMMEDIATE_M,
            AddressMode.IMMEDIATE_X,
            AddressMode.IMMEDIATE_8,
        ):
            return "#${:0{}X}".format(self.argument, self.argument_size * 2)

        elif self.address_mode in (
            AddressMode.RELATIVE,
            AddressMode.RELATIVE_LONG,
            AddressMode.DIRECT_PAGE,
            AddressMode.ABSOLUTE,
            AddressMode.ABSOLUTE_LONG,
            AddressMode.STACK_ABSOLUTE,
        ):
            return "${:0{}X}".format(self.argument, self.argument_size * 2)

        elif self.address_mode in (
            AddressMode.DIRECT_PAGE_INDEXED_X,
            AddressMode.ABSOLUTE_INDEXED_X,
            AddressMode.ABSOLUTE_INDEXED_LONG,
        ):
            return "${:0{}X},x".format(self.argument, self.argument_size * 2)

        elif self.address_mode in (
            AddressMode.DIRECT_PAGE_INDEXED_Y,
            AddressMode.ABSOLUTE_INDEXED_Y,
        ):
            return "${:0{}X},y".format(self.argument, self.argument_size * 2)

        elif self.address_mode in (
            AddressMode.DIRECT_PAGE_INDIRECT,
            AddressMode.ABSOLUTE_INDIRECT,
            AddressMode.PEI_DIRECT_PAGE_INDIRECT,
        ):
            return "(${:0{}X})".format(self.argument, self.argument_size * 2)

        elif self.address_mode in (
            AddressMode.DIRECT_PAGE_INDIRECT_LONG,
            AddressMode.ABSOLUTE_INDIRECT_LONG,
        ):
            return "[${:0{}X}]".format(self.argument, self.argument_size * 2)

        elif self.address_mode in (
            AddressMode.DIRECT_PAGE_INDEXED_INDIRECT,
            AddressMode.ABSOLUTE_INDEXED_INDIRECT,
        ):
            return "(${:0{}X},x)".format(self.argument, self.argument_size * 2)

        elif self.address_mode == AddressMode.DIRECT_PAGE_INDIRECT_INDEXED:
            return "(${:0{}X}),y".format(self.argument, self.argument_size * 2)

        elif self.address_mode == AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG:
            return "[${:0{}X}],y".format(self.argument, self.argument_size * 2)

        elif self.address_mode == AddressMode.STACK_RELATIVE:
            return "${:02X},s".format(self.argument)

        elif self.address_mode == AddressMode.STACK_RELATIVE_INDIRECT_INDEXED:
            return "(${:02X},s),y".format(self.argument)

        elif self.address_mode == AddressMode.MOVE:
            return "{:02X},{:02X}".format(self.argument & 0xFF, self.argument >> 8)

        assert False

    @property
    def argument_alias(self) -> Optional[str]:
        if self.is_control:
            target = self.absolute_argument
            if target is not None:
                return self.log.get_label(target, self.subroutine)
        return None
