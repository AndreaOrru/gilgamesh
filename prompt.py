from contextlib import redirect_stdout

from database import LabelType
from instruction import ReferenceType


def unhex(x):
    return int(x, 16)


class Prompt:
    def __init__(self, database):
        self.database = database
        self.command = ''
        self.parameters = []

    def run(self):
        while True:
            print('>>> ', end="")

            line = input().split(' ')
            command = line[0]

            if line[-2: -1] == ['>']:
                redirect_file = line[-1]
                self.parameters = line[:-2]

                with open(redirect_file, 'w') as f:
                    with redirect_stdout(f):
                        self._dispatch_command(command)
            else:
                self.parameters = line[1:]
                self._dispatch_command(command)

    def _dispatch_command(self, command):
        if command == '':
            return
        elif command in ('d', 'disassembly'):
            self._disassembly()
        elif command in ('dr', 'direct_references'):
            self._references(ReferenceType.DIRECT)
        elif command in ('ir', 'indirect_references'):
            self._references(ReferenceType.INDIRECT)
        elif command in ('r', 'references'):
            self._references()
        elif command in ('drb', 'directly_referenced_by'):
            self._referenced_by(ReferenceType.DIRECT)
        elif command in ('irb', 'indirectly_referenced_by'):
            self._referenced_by(ReferenceType.INDIRECT)
        elif command in ('rb', 'referenced_by'):
            self._referenced_by()
        elif command in ('l', 'labels'):
            self._labels()
        elif command in ('s', 'subroutines'):
            self._labels(LabelType.SUBROUTINE)
        elif command in ('v', 'vectors'):
            self._labels(LabelType.VECTOR)
        elif command in ('e', 'q', 'exit', 'quit'):
            exit()
        else:
            print('ERROR: unknown command "{}"'.format(command))

    def _disassembly(self):
        print('arch snes.cpu')
        print("""
macro seek(variable offset) {
  origin ((offset & $7F0000) >> 1) | (offset & $7FFF)
  base offset
}\n""")
        for instruction in self.database.instructions(*map(unhex, self.parameters)):
            if instruction.label:
                print('\nseek(0x{:06X})'.format(instruction.pc))
                print('{}:'.format(instruction.label))
            print('  {:<20}// ${:06X}'.format(str(instruction), instruction.pc))

    def _vectors(self):
        for vector in self.database.vectors():
            print('${:06X} ({})'.format(vector.pc, vector.type.name))

    def _references(self, typ=None):
        address = self.parameters[0]
        for reference in self.database.references(unhex(address), typ):
            print('${:06X}'.format(reference))

    def _referenced_by(self, typ=None):
        address = self.parameters[0]
        for referenced_by in self.database.referenced_by(unhex(address), typ):
            print('${:06X}'.format(referenced_by))

    def _labels(self, types=None):
        for name, pc in sorted(self.database.labels(types).items()):
            print('{:<20}// ${:06X}'.format(name, pc))
