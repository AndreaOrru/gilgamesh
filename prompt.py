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

            if (self.command == ''):
                continue
            elif (self.command in ('i', 'instructions')):
                self._instructions()
            elif (self.command in ('dr', 'direct_references')):
                self._direct_references()
            elif (self.command in ('ir', 'indirect_references')):
                self._indirect_references()
            elif (self.command in ('r', 'references')):
                self._references()
            elif (self.command in ('drb', 'directly_referenced_by')):
                self._directly_referenced_by()
            elif (self.command in ('irb', 'indirectly_referenced_by')):
                self._indirectly_referenced_by()
            elif (self.command in ('rb', 'referenced_by')):
                self._referenced_by()
            elif (self.command in ('q', 'exit', 'quit')):
                return
            else:
                print('ERROR: unknown command "{}"'.format(self.command))

            print()

    def unhex(self, x):
        return int(x, 16)

    def _direct_references(self):
        address = self.parameters[0]
        for reference in self.database.direct_references(self.unhex(address)):
            print('${:06X}'.format(reference))

    def _indirect_references(self):
        address = self.parameters[0]
        for reference in self.database.indirect_references(self.unhex(address)):
            print('${:06X}'.format(reference))

    def _references(self):
        address = self.parameters[0]
        for reference in self.database.references(self.unhex(address)):
            print('${:06X}'.format(reference))

    def _directly_referenced_by(self):
        address = self.parameters[0]
        for referenced_by in self.database.directly_referenced_by(self.unhex(address)):
            print('${:06X}'.format(referenced_by))

    def _indirectly_referenced_by(self):
        address = self.parameters[0]
        for referenced_by in self.database.indirectly_referenced_by(self.unhex(address)):
            print('${:06X}'.format(referenced_by))

    def _referenced_by(self):
        address = self.parameters[0]
        for referenced_by in self.database.referenced_by(self.unhex(address)):
            print('${:06X}'.format(referenced_by))

    def _instructions(self):
        for instruction in self.database.instructions(*map(self.unhex, self.parameters)):
            print('{:<20}// ${:06X}'.format(str(instruction), instruction.pc))
