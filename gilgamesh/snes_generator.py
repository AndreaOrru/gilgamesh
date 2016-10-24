from collections import namedtuple
from itertools import groupby

from gilgamesh.code_generator import CodeGenerator
from gilgamesh.utils import grouper
from gilgamesh.utils import pairwise


Group = namedtuple('Group', ['value', 'length'])


class SNESGenerator(CodeGenerator):
    """Code generator for the bass SNES assembler."""

    def compile(self):
        buffer = self._compile_prologue()
        blocks = self._analyzer.flow_graph()[0].values()

        # Go through the blocks in consecutive pairs:
        for b1, b2 in pairwise(blocks):
            # Print the block's instructions:
            for i in b1:
                buffer += self._compile_instruction(i)
            buffer += '\n'

            # If there is data between this block and the next, print it:
            if b1.end != b2.start:
                buffer += self._compile_data(b1.end, b2.start)

        # Compile the last instruction and any extra data:
        for i in b2:
            buffer += self._compile_instruction(i)
        buffer += self._compile_data(b2.end, end=None)

        return buffer

    def _compile_data(self, start, end):
        """Generate assembly directives for blocks of data.

        Args:
            start: The address of the first byte of the block.
            end: The address of the last byte (not included).

        Returns:
            The compiled data as a string.
        """
        if start >= self._rom.end_address:
            return ''

        data = self._rom.read_bytes(start, end=end)
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
        """Generate assembly directives for an instruction.

        Args:
            instruction: An object of type of Instruction.

        Returns:
            The compiled instruction as a string.
        """
        s = ''
        if instruction.label:
            # FIXME: Not reliable.
            if instruction.label[:4] != 'loc_':
                s += '\n'
            s += '{}:\n'.format(instruction.label)
        s += '    {:<20}// ${:06X}\n'.format(instruction.format(), instruction.pc)

        return s

    @staticmethod
    def _iter_len(iterator):
        """Calculate the length of a (finite) iterator.

        Args:
            iterator: An iterator object.

        Returns:
            The length of the iterator.
        """
        return sum(1 for x in iterator)

    @staticmethod
    def _compile_prologue():
        """Generate necessary directives to set up the assembler.

        Returns:
           A string with the directives.
        ."""
        # FIXME: This will only work for LoROM.
        return """arch snes.cpu
include "w65816.inc"

macro seek(variable offset) {
  origin ((offset & $7F0000) >> 1) | (offset & $7FFF)
  base offset
}

seek($008000)\n\n"""
