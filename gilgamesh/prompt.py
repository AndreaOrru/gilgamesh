import sys
from contextlib import redirect_stdout

from gilgamesh.database import LabelType
from gilgamesh.instruction import ReferenceType
from gilgamesh.snes_generator import SNESGenerator


class Prompt:
    def __init__(self, db, rom):
        self._db = db
        self._rom = rom

    def run(self):
        while True:
            print('>>> ', end='')
            line = input().strip()

            # Redirect output to a file:
            try:
                separator_index = line.index('>')
                command = line[:separator_index]
                redirect_file = line[separator_index + 1:].strip()
            # Output to stdout:
            except ValueError:
                command = line
                redirect_file = None
            command = list(map(lambda x: x.strip(), command.split()))

            if redirect_file:
                with open(redirect_file, 'w') as f:
                    with redirect_stdout(f):
                        self._dispatch_command(command[0], command[1:])
            else:
                self._dispatch_command(command[0], command[1:])

    def _dispatch_command(self, operation, parameters):
        if operation == '':
            return
        elif operation in ('d', 'disassembly'):
            self._print_disassembly()
        elif operation in ('i', 'instructions'):
            self._print_instructions(*parameters)
        elif operation in ('dr', 'direct_references'):
            self._print_references(ReferenceType.DIRECT, *parameters)
        elif operation in ('ir', 'indirect_references'):
            self._print_references(ReferenceType.INDIRECT, *parameters)
        elif operation in ('r', 'references'):
            self._print_references(*parameters)
        elif operation in ('drb', 'directly_referenced_by'):
            self._print_referenced_by(ReferenceType.DIRECT, *parameters)
        elif operation in ('irb', 'indirectly_referenced_by'):
            self._print_referenced_by(ReferenceType.INDIRECT, *parameters)
        elif operation in ('rb', 'referenced_by'):
            self._print_referenced_by(*parameters)
        elif operation in ('l', 'labels'):
            self._print_labels(*parameters)
        elif operation in ('s', 'subroutines'):
            self._print_labels(LabelType.SUBROUTINE)
        elif operation in ('v', 'vectors'):
            self._print_labels(LabelType.VECTOR)
        elif operation in ('ub', 'unknown_branches'):
            self._print_unknown_branches()
        elif operation in ('b', 'bytes'):
            self._print_bytes(*parameters)
        elif operation in ('e', 'q', 'exit', 'quit'):
            sys.exit()
        else:
            # TODO: raise an exception and catch in self.run.
            sys.stderr.write('ERROR: unknown operation "{}"\n'.format(operation))

    def _print_disassembly(self):
        snes_generator = SNESGenerator(self._db)
        print(snes_generator.compile())

    def _print_instructions(self, *parameters):
        for instruction in self._db.instructions(*map(self._unhex, parameters)):
            print('${:06X}    {}'.format(instruction.pc, str(instruction)))

    def _print_vectors(self):
        # TODO: have Vector be a class.
        for vector in self._db.vectors():
            print('${:06X} ({})'.format(vector.pc, vector.type.name))

    def _print_references(self, address, typ=None):
        for reference in self._db.references(self._unhex(address), typ):
            print('${:06X}'.format(reference))

    def _print_referenced_by(self, address, typ=None):
        for referenced_by in self._db.referenced_by(self._unhex(address), typ):
            print('${:06X}'.format(referenced_by))

    def _print_unknown_branches(self):
        for branch in self._db.unknown_branches():
            print('${:06X}    {} -> ${:06X}'.format(branch.pc, str(branch), branch.unique_reference))

    def _print_bytes(self, address, size='+1'):
        address = self._unhex(address)
        if size[0] != '+':
            size = self._unhex(size) - address
        else:
            size = self._unhex(size)

        for i in range(size):
            byte = self._rom.read_byte(address + i)
            if (i % 0x10) == 0:
                print('{}${:06X}    '.format('\n' if i != 0 else '', address + i), end='')
            print('{:02X}'.format(byte), end=' ')
        print()

    def _print_labels(self, types=None):
        for name, pc in sorted(self._db.labels(types).items()):
            print('${:06X}    {}'.format(pc, name))

    @staticmethod
    def _unhex(x):
        return int(x, 16)
