import sqlite3
from bidict import bidict
from enum import Enum
from collections import namedtuple

from gilgamesh.instruction import Instruction
from gilgamesh.opcodes import OpcodeCategory


class VectorType(Enum):
    RESET = 0
    NMI = 1
    IRQ = 2


class LabelType(Enum):
    JUMP = 0
    SUBROUTINE = 1
    VECTOR = 2


class Database:
    def __init__(self, db_path):
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = self._namedtuple_factory
        self._c = self._connection.cursor()
        self._labels = self.labels()

    def instructions(self, start=0x000000, end=0xFFFFFF):
        instructions = self._c.execute('SELECT * FROM instructions WHERE pc >= ? AND pc <= ?', (start, end))
        return (Instruction.from_row(self, i) for i in instructions.fetchall())

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
            SELECT pointee
            FROM instructions AS pointee,
                 instructions AS pointer,
                 references_  AS ref
            WHERE pointee.pc = ref.pointee
              AND pointer.pc = ref.pointer
              AND pointer.opcode IN {}
        """.format(category))

        return (x.pointee for x in referenced_by.fetchall())

    def unknown_branches(self):
        # Select all the branches that point to addresses that
        # are not (yet) recognized as instructions.
        branches = self._c.execute("""
          SELECT branch.*
          FROM instructions AS branch,
               references_  AS ref
          WHERE branch.opcode IN {}
            AND ref.pointer = branch.pc
            AND NOT EXISTS (SELECT 1
                            FROM instructions
                            WHERE pc = ref.pointee)
        """.format(OpcodeCategory.BRANCH))

        return (Instruction.from_row(self, i) for i in branches.fetchall())

    def label(self, address):
        try:
            return self._labels.inv[address]
        except KeyError:
            return None

    def label_address(self, label):
        try:
            return self._labels[label]
        except KeyError:
            return None

    def labels(self, types=None):
        # Search for all the labels:
        if types is None:
            types = {LabelType.JUMP, LabelType.SUBROUTINE, LabelType.VECTOR}
        # Search for just one label (accept a single object):
        elif isinstance(types, LabelType):
            types = {types}

        labels = bidict()
        if LabelType.JUMP in types:
            jump_destinations = self._referenced_by_category(OpcodeCategory.JUMP)
            branch_destinations = self._referenced_by_category(OpcodeCategory.BRANCH)

            for jump_destination in jump_destinations:
                labels['loc_{:06X}'.format(jump_destination)] = jump_destination
            for branch_destination in branch_destinations:
                labels['loc_{:06X}'.format(branch_destination)] = branch_destination

        if LabelType.SUBROUTINE in types:
            subroutines = self._referenced_by_category(OpcodeCategory.CALL)
            for subroutine in subroutines:
                labels['sub_{:06X}'.format(subroutine)] = subroutine

        if LabelType.VECTOR in types:
            for vector in self.vectors():
                if vector.type == VectorType.RESET:
                    labels['reset'] = vector.pc
                elif vector.type == VectorType.NMI:
                    labels['nmi_{:06X}'.format(vector.pc)] = vector.pc
                elif vector.type == VectorType.IRQ:
                    labels['irq_{:06X}'.format(vector.pc)] = vector.pc

        return labels

    @staticmethod
    def _namedtuple_factory(cursor, row):
        # Create named tuples from tuples:
        fields = [column[0] for column in cursor.description]
        Row = namedtuple('Row', fields)
        return Row(*row)
