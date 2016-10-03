import sqlite3
from enum import Enum, IntEnum
from collections import namedtuple
from itertools import chain

from instruction import Instruction
from opcodes import OpcodeCategory


class ReferenceType(IntEnum):
    DIRECT = 0
    INDIRECT = 1


class VectorType(Enum):
    RESET = 0
    NMI = 1
    IRQ = 2


def namedtuple_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    Row = namedtuple('Row', fields)
    return Row(*row)


class Database:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = namedtuple_factory
        self.c = self.connection.cursor()

    def instructions(self, start=0x000000, end=0xFFFFFF):
        instructions = self.c.execute('SELECT * FROM instructions WHERE pc >= ? AND pc <= ?', (start, end))
        return map(Instruction.from_row, instructions.fetchall())

    def vectors(self):
        def vector_factory(vector):
            return type(vector)(vector.pc, VectorType(vector.type).name)
        vectors = self.c.execute('SELECT * FROM vectors')
        return map(vector_factory, vectors.fetchall())

    def references(self, address, typ=None):
        if typ is None:
            references = self.c.execute('SELECT pointee FROM references_ WHERE pointer=?', (address,))
        else:
            references = self.c.execute('SELECT pointee FROM references_ WHERE pointer=? AND type=?', (address, typ))
        return map(lambda x: x.pointee, references.fetchall())

    def referenced_by(self, address, typ=None):
        if typ is None:
            referenced_by = self.c.execute('SELECT pointer FROM references_ WHERE pointee=?', (address,))
        else:
            referenced_by = self.c.execute('SELECT pointer FROM references_ WHERE pointee=? AND type=?', (address, typ))
        return map(lambda x: x.pointer, referenced_by.fetchall())

    def labels(self):
        labels = self.c.execute('SELECT * FROM labels')
        return labels.fetchall()

    def subroutines(self):
        subroutines = self.c.execute("""
            SELECT pointee
            FROM instructions,
                 references_
            WHERE instructions.pc = references_.pointer
              AND instructions.opcode IN {}
        """.format(OpcodeCategory.CALL))

        return sorted(chain(
            map(lambda x: x.pointee, subroutines.fetchall()),
            map(lambda x: x.pc, self.vectors())
        ))
