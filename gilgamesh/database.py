import sqlite3
from collections import namedtuple
from enum import Enum

from gilgamesh.instruction import ReferenceType
from gilgamesh.opcodes import OpcodeCategory


class VectorType(Enum):
    """Types of vectors."""
    RESET = 0
    NMI = 1
    IRQ = 2


class Database:
    """Abstraction on top of database queries/operations."""

    def __init__(self, db_path):
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = self._namedtuple_factory
        self._c = self._connection.cursor()

    def save(self):
        """Save the database to disk."""
        self._connection.commit()

    def store_instruction(self, pc, opcode, flags, operand=None):
        """Store a new instruction into the database.

        Args:
            pc: Program Counter.
            opcode: Opcode number.
            flags: Value of the P flags register.
            operand: Optional operand of the instruction.
        """
        self._c.execute('INSERT OR IGNORE INTO instructions VALUES(?, ?, ?, ?)', (
            pc, opcode, flags, operand
        ))

    def store_reference(self, pointer, pointee, typ=ReferenceType.DIRECT):
        """Store a new reference into the database.

        Args:
            pointer: Address of the pointer.
            pointee: Address of the pointee.
            typ: The type of reference (DIRECT or INDIRECT).
        """
        self._c.execute('INSERT OR IGNORE INTO references_ VALUES(?, ?, ?)', (
            pointer, pointee, typ
        ))

    def instruction(self, pc):
        """Search for an instruction in the database.

        Args:
            pc: The address of the instruction.

        Returns:
            The corresponding row in the database, or None.
        """
        instruction = self._c.execute('SELECT * FROM instructions WHERE pc = ?', (pc,))
        return instruction.fetchone()

    def instructions(self, start=0x000000, end=0xFFFFFF):
        """Search for a instructions inside an address interval.

        Args:
            start: The start of the interval.
            end: The end of the interval (included).

        Returns:
            An iterator over all the instruction rows in the given range.
        """
        instructions = self._c.execute('SELECT * FROM instructions WHERE pc >= ? AND pc <= ?', (start, end))
        return instructions.fetchall()

    def vectors(self):
        # TODO: Vector should be a class.
        def vector_factory(vector):
            return type(vector)(vector.pc, VectorType(vector.type))
        vectors = self._c.execute('SELECT * FROM vectors')
        return map(vector_factory, vectors.fetchall())

    def references(self, address, typ=None):
        """Search for all the memory addresses that are referenced by the given address.

        Args:
            address: The address of the pointer.
            typ: ReferenceType.DIRECT or INDIRECT. None includes both.

        Returns:
            An iterator over all the referenced addresses.
        """
        if typ is None:
            references = self._c.execute('SELECT pointee FROM references_ WHERE pointer=?', (address,))
        else:
            references = self._c.execute('SELECT pointee FROM references_ WHERE pointer=? AND type=?', (address, typ))
        return (x.pointee for x in references.fetchall())

    def referenced_by(self, address, typ=None):
        """Search for all the memory addresses that reference the given address.

        Args:
            address: The address of the pointee.
            typ: ReferenceType.DIRECT or INDIRECT. None includes both.

        Returns:
            An iterator over all the addresses that point to the given address.
        """
        if typ is None:
            referenced_by = self._c.execute('SELECT pointer FROM references_ WHERE pointee=?', (address,))
        else:
            referenced_by = self._c.execute('SELECT pointer FROM references_ WHERE pointee=? AND type=?', (address, typ))
        return (x.pointer for x in referenced_by.fetchall())

    def _referenced_by_category(self, category):
        """Search instructions of a certain category that reference the given address.

        Args:
            category: An OpcodeCategory to which the instructions have to belong.

        Returns:
            An iterator over the filtered addresses that point to the given address.
        """
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
        """Search for all the branches in the program.

        Returns:
            An iterator over all the addresses of the branches.
        """
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
        """Convert SQLite rows to named tuples.

        Args:
            cursor: The current SQLite cursor.
            row: The row to convert.

        Returns:
            The row converted to a named tuple.
        """
        fields = [column[0] for column in cursor.description]
        Row = namedtuple('Row', fields)
        return Row(*row)
