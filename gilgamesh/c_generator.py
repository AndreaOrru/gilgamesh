# flake8: noqa

import re

from gilgamesh.code_generator import CodeGenerator
from gilgamesh.opcodes import AddressMode


class CGenerator(CodeGenerator):
    M_BOUND = {'adc', 'and', 'asl', 'bit', 'cmp', 'dec', 'eor', 'inc', 'lda', 'lsr', 'ora',
               'pha', 'pla', 'rol', 'ror', 'sbc', 'sta', 'stz', 'trb', 'tsb', 'txa', 'tya'}
    X_BOUND = {'cpx', 'cpy', 'dex', 'dey', 'inx', 'iny', 'ldx', 'ldy', 'phx', 'phy', 'plx',
               'ply', 'stx', 'sty', 'tax', 'tay', 'tsx', 'txy', 'tyx'}

    _format_operand_table = [
        lambda x,s: '',                                  # IMPLIED
        lambda x,s: '0x{:0{}x}'.format(x, 2*s),          # IMMEDIATE_M
        lambda x,s: '0x{:0{}x}'.format(x, 2*s),          # IMMEDIATE_X
        lambda x,s: '0x{:02x}'.format(x),                # IMMEDIATE_8
        lambda x,s: '0x{:02x}'.format(x),                # RELATIVE
        lambda x,s: '0x{:02x}'.format(x),                # RELATIVE_LONG
        lambda x,s: 'D + 0x{:02x}'.format(x),            # DIRECT_PAGE
        lambda x,s: 'D + 0x{:02x} + X'.format(x),        # DIRECT_PAGE_INDEXED_X
        lambda x,s: 'D + 0x{:02x} + Y'.format(x),        # DIRECT_PAGE_INDEXED_Y
        lambda x,s: 'mem_w(D + 0x{:02x})'.format(x),     # DIRECT_PAGE_INDIRECT
        lambda x,s: 'mem_w(D + 0x{:02x} + X)'.format(x), # DIRECT_PAGE_INDEXED_INDIRECT
        lambda x,s: 'mem_w(D + 0x{:02x}) + Y'.format(x), # DIRECT_PAGE_INDIRECT_INDEXED
        lambda x,s: 'mem_l(0x{:02x})'.format(x),         # DIRECT_PAGE_INDIRECT_LONG
        lambda x,s: 'mem_l(0x{:02x})'.format(x),         # DIRECT_PAGE_INDIRECT_INDEXED_LONG
        lambda x,s: '0x{:04x}'.format(x),                # ABSOLUTE
        lambda x,s: '0x{:04x} + X'.format(x),            # ABSOLUTE_INDEXED_X
        lambda x,s: '0x{:04x} + Y'.format(x),            # ABSOLUTE_INDEXED_Y
        lambda x,s: '0x{:06x}'.format(x),                # ABSOLUTE_LONG
        lambda x,s: '0x{:06x} + X'.format(x),            # ABSOLUTE_INDEXED_LONG
        lambda x,s: 'S + 0x{:02x}'.format(x),            # STACK_RELATIVE
        lambda x,s: 'mem_w(S + 0x{:02x}) + Y'.format(x), # STACK_RELATIVE_INDIRECT_INDEXED
        lambda x,s: 'mem_w(0x{:04x})'.format(x),         # ABSOLUTE_INDIRECT
        lambda x,s: 'mem_l(0x{:06x})'.format(x),         # ABSOLUTE_INDIRECT_LONG
        lambda x,s: 'mem_w(0x{:04x} + X)'.format(x),     # ABSOLUTE_INDEXED_INDIRECT
        lambda x,s: '',                                  # IMPLIED_ACCUMULATOR
        lambda x,s: '0x{:02X}, 0x{:02X}'.format(x & 0xFF, x >> 8),  # MOVE
        lambda x,s: '0x{:04X}'.format(x),                # PEA
        lambda x,s: 'mem_w(0x{:02X})'.format(x),         # PEI_DIRECT_PAGE_INDIRECT
    ]

    def compile(self):
        buffer = ''
        for function in self._analyzer.functions():
            buffer += self._compile_function(function)
        return buffer

    def _compile_function(self, function):
        s = ''

        s += 'void {}()\n'.format(function[0].first.label)
        s += '{\n'
        for block in function:
            for instruction in block:
                s += self._compile_instruction(instruction)
        s += '}\n\n'

        return s

    def _compile_instruction(self, i):
        s = ''

        if i.label:
            s += '{}:\n'.format(i.label)
        s += '    {}{}({});\n'.format(i.mnemonic.upper(),
                                     self._format_postfix(i),
                                     self._format_operand(i))
        return s

    def _format_postfix(self, i):
        s = ''

        if i.address_mode in (AddressMode.IMMEDIATE_M,
                              AddressMode.IMMEDIATE_X,
                              AddressMode.IMMEDIATE_8):
            s += '_imm'

        if i.mnemonic in self.M_BOUND:
            s += '_b' if i.m_flag else '_w'
        elif i.mnemonic in self.X_BOUND:
            s += '_b' if i.x_flag else '_w'

        return s

    def _format_operand(self, i):
        s = self._format_operand_table[i.address_mode](i.operand, i.size - 1)

        if i.is_control_flow:
            reference = i.unique_reference
            if reference:
                label = self._analyzer.label(reference)
                if label:
                    s = re.sub('0x[A-F0-9]+', label, s)

        return s
