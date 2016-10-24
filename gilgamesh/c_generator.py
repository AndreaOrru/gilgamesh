# flake8: noqa

import re

from gilgamesh.code_generator import CodeGenerator
from gilgamesh.opcodes import AddressMode
from gilgamesh.registers import registers


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
        lambda x,s: 'B + 0x{:04x}'.format(x),            # ABSOLUTE
        lambda x,s: 'B + 0x{:04x} + X'.format(x),        # ABSOLUTE_INDEXED_X
        lambda x,s: 'B + 0x{:04x} + Y'.format(x),        # ABSOLUTE_INDEXED_Y
        lambda x,s: '0x{:06x}'.format(x),                # ABSOLUTE_LONG
        lambda x,s: '0x{:06x} + X'.format(x),            # ABSOLUTE_INDEXED_LONG
        lambda x,s: 'S + 0x{:02x}'.format(x),            # STACK_RELATIVE
        lambda x,s: 'mem_w(S + 0x{:02x}) + Y'.format(x), # STACK_RELATIVE_INDIRECT_INDEXED
        lambda x,s: 'mem_w(B + 0x{:04x})'.format(x),     # ABSOLUTE_INDIRECT
        lambda x,s: 'mem_l(0x{:06x})'.format(x),         # ABSOLUTE_INDIRECT_LONG
        lambda x,s: 'mem_w(B + 0x{:04x} + X)'.format(x), # ABSOLUTE_INDEXED_INDIRECT
        lambda x,s: '',                                  # IMPLIED_ACCUMULATOR
        lambda x,s: '0x{:02X}, 0x{:02X}'.format(x & 0xFF, x >> 8),  # MOVE
        lambda x,s: '0x{:04X}'.format(x),                # PEA
        lambda x,s: 'mem_w(0x{:02X})'.format(x),         # PEI_DIRECT_PAGE_INDIRECT
    ]

    def compile(self):
        functions = self._analyzer.functions()
        self._dma_transfers = {d.pc: d for d in self._analyzer._db.dma_transfers()}

        buffer = self._compile_prologue()

        for function in functions:
            buffer += self._compile_prototype(function)

        for function in functions:
            buffer += self._compile_function(function)

        return buffer

    def _compile_prototype(self, function):
        return 'void {}();\n'.format(function[0].first.label)

    def _compile_function(self, function):
        s = ''

        s += '\nvoid {}()\n'.format(function[0].first.label)
        s += '{\n'
        for block in function:
            if function[0] is not block:
                s += '\n'

            for instruction in block:
                s += self._compile_instruction(instruction)
        s += '}\n'

        return s

    def _compile_instruction(self, i):
        s = ''
        comment = ''

        if i.label:
            s += '{}:\n'.format(i.label)

        dma = self._dma_transfers.get(i.pc)
        if dma is not None:
            comment = '  // DMA: ${:06X} -> {} ({} bytes)'.format(
                dma.source, dma.destination.name, dma.bytes)

        s += '    {}{}\n'.format(self._format_instruction(i), comment)

        return s

    def _format_instruction(self, i):
        s = i.mnemonic.upper()

        if i.mnemonic in ('sep', 'rep', 'sei', 'xce', 'cli'):
            s = '// ' + s
        elif i.is_jump or i.mnemonic == 'bra':
            return 'goto {};'.format(self._format_operand(i))
        elif i.is_call:
            return '{}();'.format(self._format_operand(i))
        elif i.is_return:
            return 'return;'
        elif i.mnemonic in ('inc', 'dec'):
            return s + '_{}'.format('b(A.l);' if i.m_flag else 'w(A.w);')
        elif i.mnemonic in ('inx', 'iny', 'dex', 'dey'):
            reg = s[-1]
            return s[:-1] + 'C_{1}({0}.{2});'.format(reg, *(('b', 'l') if i.x_flag else ('w', 'w')))

        if i.address_mode in (AddressMode.IMMEDIATE_M,
                              AddressMode.IMMEDIATE_X,
                              AddressMode.IMMEDIATE_8):
            s += '_imm'

        if i.mnemonic in self.M_BOUND:
            s += '_b' if i.m_flag else '_w'
        elif i.mnemonic in self.X_BOUND:
            s += '_b' if i.x_flag else '_w'

        s += '({});'.format(self._format_operand(i))

        return s

    def _format_operand(self, i):
        if i.mnemonic == 'php':
            return '{}, {}'.format(int(i.m_flag), int(i.x_flag))
        elif i.mnemonic == 'phk':
            return '0x{:02x}'.format(i.pc >> 16)

        s = self._format_operand_table[i.address_mode](i.operand, i.size - 1)

        reference = i.unique_reference
        if reference:
            label = registers.get(reference)
            if label is None:
                label = self._analyzer.label(reference)
            if label:
                # FIXME: Hackish...
                s = re.sub('0x[a-f0-9]+', label, s)
                s = s.replace('B + ', '')

        return s

    def _compile_prologue(self):
        return """#include "w65816.hpp"

Register A, X, Y, S, D;
uint32_t B = 0;
Flags P;
uint8_t mem[0x20000];\n\n"""
