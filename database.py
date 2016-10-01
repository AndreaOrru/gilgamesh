import sqlite3
from itertools import chain

from instruction import Instruction


class Database:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.c = self.connection.cursor()

    def instructions(self, start=None, end=None):
        if (start and end):
            instructions = self.c.execute('SELECT * FROM instructions WHERE pc >= ? AND pc <= ?', (start, end))
        else:
            instructions = self.c.execute('SELECT * FROM instructions')
        return map(Instruction.from_row, instructions.fetchall())

    def direct_references(self, address):
        references = self.c.execute('SELECT * FROM direct_references WHERE pointer=?', (address,))
        return map(lambda x: x['pointee'], references.fetchall())

    def indirect_references(self, address):
        references = self.c.execute('SELECT * FROM indirect_references WHERE pointer=?', (address,))
        return map(lambda x: x['pointee'], references.fetchall())

    def references(self, address):
        direct = self.direct_references(address)
        indirect = self.indirect_references(address)
        return sorted(chain(direct, indirect))

    def directly_referenced_by(self, address):
        referenced_by = self.c.execute('SELECT * FROM direct_references WHERE pointee=?', (address,))
        return map(lambda x: x['pointer'], referenced_by.fetchall())

    def indirectly_referenced_by(self, address):
        referenced_by = self.c.execute('SELECT * FROM indirect_references WHERE pointee=?', (address,))
        return map(lambda x: x['pointer'], referenced_by.fetchall())

    def referenced_by(self, address):
        directly = self.directly_referenced_by(address)
        indirectly = self.indirectly_referenced_by(address)
        return sorted(chain(directly, indirectly))
