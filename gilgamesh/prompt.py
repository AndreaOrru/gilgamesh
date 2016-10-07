import sys
from contextlib import redirect_stdout

from gilgamesh.database import LabelType
from gilgamesh.instruction import ReferenceType


class Prompt:
    def __init__(self, db):
        self._db = db

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
            self._print_disassembly(*parameters)
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
        elif operation in ('e', 'q', 'exit', 'quit'):
            sys.exit()
        else:
            # TODO: raise an exception and catch in self.run.
            sys.stderr.write('ERROR: unknown operation "{}"\n'.format(operation))

    def _print_disassembly(self, *parameters):
        self._print_disassembly_prologue()
        for instruction in self._db.instructions(*map(self._unhex, parameters)):
            if instruction.label:
                print('\nseek(0x{:06X})'.format(instruction.pc))
                print('{}:'.format(instruction.label))
            print('  {:<20}// ${:06X}'.format(str(instruction), instruction.pc))

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
            print(branch)

    def _print_labels(self, types=None):
        for name, pc in sorted(self._db.labels(types).items()):
            print('{:<20}// ${:06X}'.format(name, pc))

    @staticmethod
    def _print_disassembly_prologue():
        print("""arch snes.cpu
macro seek(variable offset) {
  origin ((offset & $7F0000) >> 1) | (offset & $7FFF)
  base offset
}\n""")

    @staticmethod
    def _unhex(x):
        return int(x, 16)
