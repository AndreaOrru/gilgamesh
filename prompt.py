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
            self.command = line[0]
            self.parameters = line[1:]

            if self.command == '':
                continue
            elif self.command in ('d', 'disassembly'):
                self._disassembly()
            elif self.command in ('dr', 'direct_references'):
                self._references(ReferenceType.DIRECT)
            elif self.command in ('ir', 'indirect_references'):
                self._references(ReferenceType.INDIRECT)
            elif self.command in ('r', 'references'):
                self._references()
            elif self.command in ('drb', 'directly_referenced_by'):
                self._referenced_by(ReferenceType.DIRECT)
            elif self.command in ('irb', 'indirectly_referenced_by'):
                self._referenced_by(ReferenceType.INDIRECT)
            elif self.command in ('rb', 'referenced_by'):
                self._referenced_by()
            elif self.command in ('l', 'labels'):
                self._labels()
            elif self.command in ('s', 'subroutines'):
                self._labels(LabelType.SUBROUTINE)
            elif self.command in ('v', 'vectors'):
                self._labels(LabelType.VECTOR)
            elif self.command in ('e', 'q', 'exit', 'quit'):
                return
            else:
                print('ERROR: unknown command "{}"'.format(self.command))

    def _disassembly(self):
        for instruction in self.database.instructions(*map(unhex, self.parameters)):
            if instruction.label:
                print('\n{}:'.format(instruction.label))
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
