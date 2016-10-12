from collections import namedtuple
from itertools import groupby

from gilgamesh.code_generator import CodeGenerator
from gilgamesh.utils import grouper, pairwise


Group = namedtuple('Group', ['value', 'length'])


class SNESGenerator(CodeGenerator):
    def compile(self):
        buffer = ''
        buffer += self._generate_prologue()

        # Go through the instructions in consecutive pairs:
        for i1, i2 in pairwise(self._analyzer.instructions()):
            # Print the instruction:
            buffer += self._compile_instruction(i1)

            # If there is data between this instruction and the next, print it:
            if (i1.pc + i1.size) != i2.pc:
                buffer += self._compile_data(i1.pc + i1.size, i2.pc)

        # Compile the last instruction and any extra data:
        buffer += self._compile_instruction(i2)
        buffer += self._compile_data(i2.pc + i2.size, end=None)

        return buffer

    def _compile_data(self, begin, end):
        if begin >= self._rom.end_address:
            return ''

        data = self._rom.read_bytes(begin, end=end)
        groups = []

        # Iterate through the data in consecutive value groups:
        for value, group in groupby(data):
            length = self._iter_len(group)
            # Keep track sequences of 32 consecutively equal values:
            if length > 32:
                groups.append(Group(value, length))
            # Append anything else in the last element of the list (itself a list of values):
            else:
                try:
                    groups[-1] += [value] * length
                except (IndexError, TypeError):
                    # If the list is empty or the last element is a Group:
                    groups.append([value] * length)

        # Generate the compilation output:
        s = '\n'
        for group in groups:
            # If the element is a Group, use the "fill" directive:
            if isinstance(group, Group):
                s += '\nfill {}, ${:02X}\n\n'.format(group.length, group.value)
            else:
                # Otherwise just print sequences of 16 bytes:
                for values in grouper(group, 0x10):
                    s += 'db '
                    s += ', '.join(map(lambda v: '${:02X}'.format(v), values))
                    s += '\n'

        return s

    @staticmethod
    def _compile_instruction(instruction):
        s = ''
        if instruction.label:
            s += '\n{}:\n'.format(instruction.label)
        s += '    {:<20}// ${:06X}\n'.format(instruction.format(), instruction.pc)

        return s

    @staticmethod
    def _iter_len(iterator):
        return sum(1 for x in iterator)

    @staticmethod
    def _generate_prologue():
        # FIXME: This will only work for LoROM.
        return """arch snes.cpu

macro seek(variable offset) {
  origin ((offset & $7F0000) >> 1) | (offset & $7FFF)
  base offset
}

seek($008000)\n"""
