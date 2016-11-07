# pylint: disable=unnecessary-lambda
"""Command interpreter."""

import readline
import sys
from contextlib import redirect_stdout

from gilgamesh.analyzer import LabelType
from gilgamesh.c_generator import CGenerator
from gilgamesh.cpu import CPU
from gilgamesh.instruction import ReferenceType
from gilgamesh.snes_generator import SNESGenerator


class Prompt:
    """Command interpreter."""

    def __init__(self, analyzer, rom):
        self._analyzer = analyzer
        self._rom = rom

    def run(self):
        """Run the command interpreter."""
        readline.parse_and_bind('')

        while True:
            line = input('>>> ').strip()

            # Redirect output to a file:
            try:
                separator_index = line.index('>')
                command = line[:separator_index]
                redirect_file = line[separator_index + 1:].strip()
            # Output to stdout:
            except ValueError:
                command = line
                redirect_file = None
            command = [x.strip() for x in command.split()]

            if redirect_file:
                with open(redirect_file, 'w') as f:
                    with redirect_stdout(f):
                        self._dispatch_command(command[0], command[1:])
            else:
                self._dispatch_command(command[0], command[1:])

    def _dispatch_command(self, operation, parameters):
        """Dispatch the execution of the command to the right method.

        Args:
            operation: String containing the name of the command.
            parameters: List containing the parameters for the command.
        """
        function = {
            '':    lambda: None,
            'd':   lambda: self._print_disassembly(),
            'dc':  lambda: self._print_decompilation(),
            'i':   lambda: self._print_instructions(*parameters),
            'dr':  lambda: self._print_references(ReferenceType.DIRECT, *parameters),
            'ir':  lambda: self._print_references(ReferenceType.INDIRECT, *parameters),
            'r':   lambda: self._print_references(*parameters),
            'drb': lambda: self._print_referenced_by(ReferenceType.DIRECT, *parameters),
            'irb': lambda: self._print_referenced_by(ReferenceType.INDIRECT, *parameters),
            'rb':  lambda: self._print_referenced_by(*parameters),
            'l':   lambda: self._print_labels(*parameters),
            's':   lambda: self._print_labels(LabelType.SUBROUTINE),
            'v':   lambda: self._print_labels(LabelType.VECTOR),
            'dma': lambda: self._print_dma_transfers(),
            'ib':  lambda: self._print_incomplete_branches(),
            'b':   lambda: self._print_bytes(*parameters),
            'bc':  lambda: self._print_bytes(*parameters, c_array=True),
            'e':   lambda: self._emulate_incomplete_branches(*parameters),
            'f':   lambda: self._print_functions(),
            'fg':  lambda: self._print_flow_graph(),
            'a':   lambda: self._analyzer.analyze(),
            'h':   lambda: self.help(),
            'w':   lambda: self._analyzer.write_database(),
            'wq':  lambda: [self._analyzer.write_database(), sys.exit()],
            'q':   lambda: sys.exit(),
        }.get(operation)

        if function:
            function()
        else:
            sys.stderr.write('ERROR: unknown operation "{}"\n'.format(operation))
            sys.stderr.write('Type "h" for help.\n')

    @staticmethod
    def help():
        print("""List of commands:
  i    Instructions
  d    Disassembly
  dc   Decompilation

  r    References
  dr   Direct references
  ir   Indirect references

  rb   Referenced by
  drb  Directly referenced by
  irb  Indirectly referenced by

  l    Labels
  s    Subroutines
  v    Vectors

  dma  DMA transfers
  b    Bytes
  bc   Bytes as C array

  a    Analyze
  e    Emulate
  ib   Incomplete branches
  f    Functions
  fg   Flow graph

  w    Write
  wq   Write and quit
  q    Quit""")

    def _emulate_incomplete_branches(self):
        # TODO: Move to analyzer.
        for branch in self._analyzer.incomplete_branches():
            cpu = CPU(self._analyzer, self._rom, branch.pc, branch.flags)
            for instruction in cpu.run():
                print('${:06X}    {}'.format(instruction.pc, str(instruction)))
            print()
        # Reanalyze the ROM:
        self._analyzer.analyze()

    def _print_flow_graph(self):
        blocks, edges, inv_edges = self._analyzer.flow_graph()

        for block in blocks.values():
            in_edges = sorted(inv_edges.get(block.start) or [])
            print('in edges: ' + ', '.join('${:06X}'.format(e) for e in in_edges))

            for instruction in block:
                print('${:06X}    {}'.format(instruction.pc, str(instruction)))

            out_edges = sorted(edges.get(block.start) or [])
            print('out edges: ' + ', '.join('${:06X}'.format(e) for e in out_edges))
            print()

    def _print_functions(self):
        for function in self._analyzer.functions():
            for block in function:
                print('${:06X}'.format(block.start))
            print()

    def _print_disassembly(self):
        snes_generator = SNESGenerator(self._analyzer, self._rom)
        print(snes_generator.compile())

    def _print_decompilation(self):
        c_generator = CGenerator(self._analyzer, self._rom)
        print(c_generator.compile())

    def _print_instructions(self, *parameters):
        if len(parameters) == 1:
            parameters = [parameters[0]] * 2

        for instruction in self._analyzer.instructions(*map(self._unhex, parameters)):
            print('${:06X}    {}'.format(instruction.pc, str(instruction)))

    def _print_vectors(self):
        # TODO: have Vector be a class.
        for vector in self._analyzer._db.vectors():
            print('${:06X} ({})'.format(vector.pc, vector.type.name))

    def _print_dma_transfers(self):
        # TODO: have DMATransfer be a class.
        for d in self._analyzer._db.dma_transfers():
            print('${:06X}    ${:06X} -> {} (${:X} bytes)'.format(
                d.pc, d.source, d.destination.name, d.bytes
            ))

    def _print_references(self, address, typ=None):
        for reference in self._analyzer._db.references(self._unhex(address), typ):
            print('${:06X}'.format(reference))

    def _print_referenced_by(self, address, typ=None):
        for referenced_by in self._analyzer._db.referenced_by(self._unhex(address), typ):
            print('${:06X}'.format(referenced_by))

    def _print_incomplete_branches(self):
        for branch in sorted(self._analyzer.incomplete_branches()):
            print('${:06X}    {} -> ${:06X}'.format(branch.pc, str(branch), branch.unique_reference))

    def _print_bytes(self, address, end='+1', c_array=False):
        """Print a hex dump of a region of memory.

        Args:
            address: The initial address of the region.

        Returns:

        """
        address = self._unhex(address)
        if end[0] != '+':
            count = self._unhex(end) - address
        else:
            count = self._unhex(end)

        if c_array:
            return self._print_bytes_c(address, count)

        for i in range(count):
            byte = self._rom.read_byte(address + i)
            if (i % 0x10) == 0:
                print('{}${:06X}    '.format('\n' if i != 0 else '', address + i), end='')
            print('{:02X}'.format(byte), end=' ')
        print()

    def _print_bytes_c(self, start, count):
        print('uint8_t array[] = {', end='')

        for i in range(count):
            byte = self._rom.read_byte(start + i)
            if (i % 0x10) == 0:
                print('\n    ', end='')
            print('0x{:02X}'.format(byte), end=', ')

        print('\n};')


    def _print_labels(self, types=None):
        for name, address in sorted(self._analyzer.labels(types).items()):
            print('${:06X}    {}'.format(address, name))

    @staticmethod
    def _unhex(x):
        return int(x, 16)
