import sqlite3
from collections import namedtuple
from enum import Enum

from gilgamesh.instruction import ReferenceType
from gilgamesh.opcodes import OpcodeCategory


class VectorType(Enum):
    RESET = 0
    NMI = 1
    IRQ = 2


class Database:
    def __init__(self, db_path):
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = self._namedtuple_factory
        self._c = self._connection.cursor()

    def save(self):
        self._connection.commit()

    def store_instruction(self, pc, opcode, flags, operand):
        self._c.execute('INSERT OR IGNORE INTO instructions VALUES(?, ?, ?, ?)', (
            pc, opcode, flags, operand
        ))

    def store_reference(self, pointer, pointee, typ=ReferenceType.DIRECT):
        self._c.execute('INSERT OR IGNORE INTO references_ VALUES(?, ?, ?)', (
            pointer, pointee, typ
        ))

    def instruction(self, pc):
        instruction = self._c.execute('SELECT * FROM instructions WHERE pc = ?', (pc,))
        return instruction.fetchone()

    def instructions(self, start=0x000000, end=0xFFFFFF):
        instructions = self._c.execute('SELECT * FROM instructions WHERE pc >= ? AND pc <= ?', (start, end))
        return instructions.fetchall()

    def vectors(self):
        def vector_factory(vector):
            return type(vector)(vector.pc, VectorType(vector.type))
        vectors = self._c.execute('SELECT * FROM vectors')
        return map(vector_factory, vectors.fetchall())

    def references(self, address, typ=None):
        if typ is None:
            references = self._c.execute('SELECT pointee FROM references_ WHERE pointer=?', (address,))
        else:
            references = self._c.execute('SELECT pointee FROM references_ WHERE pointer=? AND type=?', (address, typ))
        return (x.pointee for x in references.fetchall())

    def referenced_by(self, address, typ=None):
        if typ is None:
            referenced_by = self._c.execute('SELECT pointer FROM references_ WHERE pointee=?', (address,))
        else:
            referenced_by = self._c.execute('SELECT pointer FROM references_ WHERE pointee=? AND type=?', (address, typ))
        return (x.pointer for x in referenced_by.fetchall())

    def _referenced_by_category(self, category):
        referenced_by = self._c.execute("""
            SELECT ref.pointee
            FROM instructions AS pointee,
                 instructions AS pointer,
                 references_  AS ref
            WHERE pointee.pc = ref.pointee
              AND pointer.pc = ref.pointer
              AND pointer.opcode IN {}
        """.format(category))

        return (x.pointee for x in referenced_by.fetchall())

    def branches(self):
        # Select all branches in the program:
        branches = self._c.execute("""
          SELECT branch.*
          FROM instructions AS branch,
               references_  AS ref
          WHERE branch.opcode IN {}
            AND ref.pointer = branch.pc
        """.format(OpcodeCategory.BRANCH))

        return branches.fetchall()

    @staticmethod
    def _namedtuple_factory(cursor, row):
        # Create named tuples from tuples:
        fields = [column[0] for column in cursor.description]
        Row = namedtuple('Row', fields)
        return Row(*row)
