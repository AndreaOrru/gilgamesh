# flake8: noqa

import re
from enum import IntEnum

from gilgamesh.opcodes import AddressMode
from gilgamesh.opcodes import OpcodeCategory
from gilgamesh.opcodes import opcode_table
from gilgamesh.opcodes import size_table


class ReferenceType(IntEnum):
    DIRECT = 0
    INDIRECT = 1


class Instruction:
    _format_operand_table = [
        lambda x,s: '',                         # IMPLIED
        lambda x,s: '#${:0{}X}'.format(x, 2*s), # IMMEDIATE_M
        lambda x,s: '#${:0{}X}'.format(x, 2*s), # IMMEDIATE_X
        lambda x,s: '#${:02X}'.format(x),       # IMMEDIATE_8
        lambda x,s: '${:02X}'.format(x),        # RELATIVE
        lambda x,s: '${:02X}'.format(x),        # RELATIVE_LONG
        lambda x,s: '${:02X}'.format(x),        # DIRECT_PAGE
        lambda x,s: '${:02X},x'.format(x),      # DIRECT_PAGE_INDEXED_X
        lambda x,s: '${:02X},y'.format(x),      # DIRECT_PAGE_INDEXED_Y
        lambda x,s: '(${:02X})'.format(x),      # DIRECT_PAGE_INDIRECT
        lambda x,s: '(${:02X},x)'.format(x),    # DIRECT_PAGE_INDEXED_INDIRECT
        lambda x,s: '(${:02X}),y'.format(x),    # DIRECT_PAGE_INDIRECT_INDEXED
        lambda x,s: '[${:02X}]'.format(x),      # DIRECT_PAGE_INDIRECT_LONG
        lambda x,s: '[${:02X}]'.format(x),      # DIRECT_PAGE_INDIRECT_INDEXED_LONG
        lambda x,s: '${:04X}'.format(x),        # ABSOLUTE
        lambda x,s: '${:04X},x'.format(x),      # ABSOLUTE_INDEXED_X
        lambda x,s: '${:04X},y'.format(x),      # ABSOLUTE_INDEXED_Y
        lambda x,s: '${:06X}'.format(x),        # ABSOLUTE_LONG
        lambda x,s: '${:06X},x'.format(x),      # ABSOLUTE_INDEXED_LONG
        lambda x,s: '${:02X},s'.format(x),      # STACK_RELATIVE
        lambda x,s: '(${:02X},s),y'.format(x),  # STACK_RELATIVE_INDIRECT_INDEXED
        lambda x,s: '(${:04X})'.format(x),      # ABSOLUTE_INDIRECT
        lambda x,s: '[${:06X}]'.format(x),      # ABSOLUTE_INDIRECT_LONG
        lambda x,s: '(${:04X},x)'.format(x),    # ABSOLUTE_INDEXED_INDIRECT
        lambda x,s: '',                         # IMPLIED_ACCUMULATOR
        lambda x,s: '${:02X},${:02X}'.format(x & 0xFF, x >> 8),  # MOVE
        lambda x,s: '${:04X}'.format(x),        # PEA
        lambda x,s: '(${:02X})'.format(x),      # PEI_DIRECT_PAGE_INDIRECT
    ]

    def __init__(self, analyzer, pc, opcode, flags, operand=None):
        self._analyzer = analyzer
        self.pc = pc
        self.opcode = opcode_table[opcode]
        self.flags = flags
        self.operand = operand

    @classmethod
    def from_row(cls, analyzer, row):
        return cls(analyzer, *row)

    def __lt__(self, other):
        return self.pc < other.pc

    def __str__(self):
        return self.format(False)

    def format(self, pretty=True):
        mnemonic = self.mnemonic
        operand = self._format_operand(pretty)
        return '{} {}'.format(mnemonic, operand) if operand else mnemonic

    @property
    def x_flag(self):
        return bool(self.flags & (2 << 3))

    @property
    def m_flag(self):
        return bool(self.flags & (2 << 4))

    @property
    def size(self):
        size = size_table[self.opcode.address_mode]
        if size is None:
            if self.opcode.address_mode == AddressMode.IMMEDIATE_M:
                return 2 if self.m_flag else 3
            elif self.opcode.address_mode == AddressMode.IMMEDIATE_X:
                return 2 if self.x_flag else 3
        else:
            return size

    @property
    def mnemonic(self):
        return self.opcode.mnemonic

    @property
    def address_mode(self):
        return self.opcode.address_mode

    @property
    def label(self):
        return self._analyzer.label(self.pc)

    @property
    def is_call(self):
        return self.opcode.number in OpcodeCategory.CALL

    @property
    def is_jump(self):
        return self.opcode.number in OpcodeCategory.JUMP

    @property
    def is_branch(self):
        return self.opcode.number in OpcodeCategory.BRANCH

    @property
    def is_return(self):
        return self.opcode.number in OpcodeCategory.RETURN

    @property
    def is_control_flow(self):
        return self.is_call or self.is_jump or self.is_branch or self.is_return

    @property
    def unique_reference(self):
        # TODO: export references inside analyzer:
        indirect = list(self._analyzer._db.references(self.pc, ReferenceType.INDIRECT))
        direct = list(self._analyzer._db.references(self.pc, ReferenceType.DIRECT))

        # Return the one single direct reference if there is one, None otherwise:
        if len(indirect) == 0 and len(direct) == 1:
            return direct[0]
        else:
            return None

    def _format_operand(self, pretty=True):
        operand = self._format_operand_table[self.address_mode](self.operand, self.size - 1)

        # Convert the address the instruction points to to a label, if there is one:
        if pretty and self.is_control_flow:
            reference = self.unique_reference
            if reference:
                label = self._analyzer.label(reference)
                if label:
                    operand = re.sub('\$[A-F0-9]+', label, operand)

        return operand
