# flake8: noqa

import re
from enum import IntEnum

from gilgamesh.opcodes import AddressMode as Mode, OpcodeCategory, opcode_table


class ReferenceType(IntEnum):
    DIRECT = 0
    INDIRECT = 1


class Instruction:
    _format_operand_table = {
        Mode.IMPLIED:                           lambda x, s: '',
        Mode.IMMEDIATE_M:                       lambda x, s: '#${:0{}X}'.format(x, 2*s),
        Mode.IMMEDIATE_I:                       lambda x, s: '#${:0{}X}'.format(x, 2*s),
        Mode.IMMEDIATE_8:                       lambda x, s: '#${:02X}'.format(x),
        Mode.RELATIVE:                          lambda x, s: '${:02X}'.format(x),
        Mode.RELATIVE_LONG:                     lambda x, s: '${:02X}'.format(x),
        Mode.DIRECT_PAGE:                       lambda x, s: '${:02X}'.format(x),
        Mode.DIRECT_PAGE_INDEXED_X:             lambda x, s: '${:02X},x'.format(x),
        Mode.DIRECT_PAGE_INDEXED_Y:             lambda x, s: '${:02X},y'.format(x),
        Mode.DIRECT_PAGE_INDIRECT:              lambda x, s: '(${:02X})'.format(x),
        Mode.DIRECT_PAGE_INDEXED_INDIRECT:      lambda x, s: '(${:02X},x)'.format(x),
        Mode.DIRECT_PAGE_INDIRECT_INDEXED:      lambda x, s: '(${:02X}),y'.format(x),
        Mode.DIRECT_PAGE_INDIRECT_LONG:         lambda x, s: '[${:02X}]'.format(x),
        Mode.DIRECT_PAGE_INDIRECT_INDEXED_LONG: lambda x, s: '[${:02X}]'.format(x),
        Mode.ABSOLUTE:                          lambda x, s: '${:04X}'.format(x),
        Mode.ABSOLUTE_INDEXED_X:                lambda x, s: '${:04X},x'.format(x),
        Mode.ABSOLUTE_INDEXED_Y:                lambda x, s: '${:04X},y'.format(x),
        Mode.ABSOLUTE_LONG:                     lambda x, s: '${:06X}'.format(x),
        Mode.ABSOLUTE_INDEXED_LONG:             lambda x, s: '${:06X},x'.format(x),
        Mode.STACK_RELATIVE:                    lambda x, s: '${:02X},s'.format(x),
        Mode.STACK_RELATIVE_INDIRECT_INDEXED:   lambda x, s: '(${:02X},s),y'.format(x),
        Mode.ABSOLUTE_INDIRECT:                 lambda x, s: '(${:04X})'.format(x),
        Mode.ABSOLUTE_INDIRECT_LONG:            lambda x, s: '[${:06X}]'.format(x),
        Mode.ABSOLUTE_INDEXED_INDIRECT:         lambda x, s: '(${:04X},x)'.format(x),
        Mode.IMPLIED_ACCUMULATOR:               lambda x, s: '',
        Mode.MOVE:                              lambda x, s: '${:02X},${:02X}'.format(x & 0xFF, x >> 8),
        Mode.PEA:                               lambda x, s: '${:04X}'.format(x),
        Mode.PEI_DIRECT_PAGE_INDIRECT:          lambda x, s: '(${:02X})'.format(x),
    }

    def __init__(self, database, pc, opcode, size, operand=None):
        self.database = database
        self.pc = pc
        self.opcode = opcode_table[opcode]
        self.size = size
        self.operand = operand

    def __str__(self):
        mnemonic = self.mnemonic
        operand = self._format_operand()
        return '{} {}'.format(mnemonic, operand) if operand else mnemonic

    @classmethod
    def from_row(cls, database, row):
        return cls(database, *row)

    @property
    def mnemonic(self):
        return self.opcode.mnemonic

    @property
    def address_mode(self):
        return self.opcode.address_mode

    @property
    def label(self):
        return self.database.label(self.pc)

    def is_call(self):
        return self.opcode.number in OpcodeCategory.CALL

    def is_jump(self):
        return self.opcode.number in OpcodeCategory.JUMP

    def is_branch(self):
        return self.opcode.number in OpcodeCategory.BRANCH

    def is_control_flow(self):
        return self.is_call() or self.is_jump() or self.is_branch()

    def unique_reference(self):
        indirect = list(self.database.references(self.pc, ReferenceType.INDIRECT))
        direct = list(self.database.references(self.pc, ReferenceType.DIRECT))

        if len(indirect) == 0 and len(direct) == 1:
            return direct[0]
        else:
            return None

    def _format_operand(self):
        operand = self._format_operand_table[self.address_mode](self.operand, self.size - 1)

        if self.is_control_flow():
            reference = self.unique_reference()
            if reference:
                label = self.database.label(reference)
                if label:
                    operand = re.sub('\$[A-F0-9]+', label, operand)

        return operand
