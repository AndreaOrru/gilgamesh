import sqlite3
from enum import IntEnum

from instruction import Instruction
from opcodes import OpcodeCategory


class ReferenceType(IntEnum):
    DIRECT = 0
    INDIRECT = 1


class Database:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.c = self.connection.cursor()

    def instructions(self, start=None, end=None):
        if (start is not None) and (end is not None):
            instructions = self.c.execute('SELECT * FROM instructions WHERE pc >= ? AND pc <= ?', (start, end))
        else:
            instructions = self.c.execute('SELECT * FROM instructions')
        return map(Instruction.from_row, instructions.fetchall())

    def references(self, address, typ=None):
        if typ is None:
            references = self.c.execute('SELECT * FROM references_ WHERE pointer=?', (address,))
        else:
            references = self.c.execute('SELECT * FROM references_ WHERE pointer=? AND type=?', (address, typ))
        return map(lambda x: x['pointee'], references.fetchall())

    def referenced_by(self, address, typ=None):
        if typ is None:
            referenced_by = self.c.execute('SELECT * FROM references_ WHERE pointee=?', (address,))
        else:
            referenced_by = self.c.execute('SELECT * FROM references_ WHERE pointee=? AND type=?', (address, typ))
        return map(lambda x: x['pointer'], referenced_by.fetchall())

    def subroutines(self):
        subroutines = self.c.execute("""
            SELECT *
            FROM instructions,
                 references_
            WHERE instructions.pc = references_.pointer
              AND instructions.opcode IN {}
        """.format(OpcodeCategory.CALL))
        return map(lambda x: x['pointee'], subroutines.fetchall())
