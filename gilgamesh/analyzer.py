from bidict import bidict
from collections import defaultdict, OrderedDict
from enum import Enum

from gilgamesh.block import Block
from gilgamesh.database import VectorType
from gilgamesh.instruction import Instruction
from gilgamesh.opcodes import OpcodeCategory
from gilgamesh.utils import pairwise


class LabelType(Enum):
    JUMP = 0
    SUBROUTINE = 1
    VECTOR = 2


class Analyzer:
    def __init__(self, db):
        self._db = db
        self.analyze()

    def analyze(self):
        self._labels = self.labels()

    def write_database(self):
        self._db.save()

    def store_instruction(self, i):
        self._db.store_instruction(i.pc, i.opcode.number, i.flags, i.operand)

    def instruction(self, pc):
        instruction = self._db.instruction(pc)
        return None if (instruction is None) else Instruction.from_row(self, instruction)

    def instructions(self, start=0x000000, end=0xFFFFFF):
        instructions = self._db.instructions(start, end)
        return (Instruction.from_row(self, i) for i in instructions)

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
            jump_destinations = self._db._referenced_by_category(OpcodeCategory.JUMP)
            branch_destinations = self._db._referenced_by_category(OpcodeCategory.BRANCH)

            for jump_destination in jump_destinations:
                labels['loc_{:06X}'.format(jump_destination)] = jump_destination
            for branch_destination in branch_destinations:
                labels['loc_{:06X}'.format(branch_destination)] = branch_destination

        if LabelType.SUBROUTINE in types:
            subroutines = self._db._referenced_by_category(OpcodeCategory.CALL)
            for subroutine in subroutines:
                labels['sub_{:06X}'.format(subroutine)] = subroutine

        if LabelType.VECTOR in types:
            for vector in self._db.vectors():
                if vector.type == VectorType.RESET:
                    labels['reset'] = vector.pc
                elif vector.type == VectorType.NMI:
                    labels['nmi_{:06X}'.format(vector.pc)] = vector.pc
                elif vector.type == VectorType.IRQ:
                    labels['irq_{:06X}'.format(vector.pc)] = vector.pc

        return labels

    def flow_graph(self):
        blocks = [Block(self)]
        edges = defaultdict(set)
        inv_edges = defaultdict(set)

        for i1, i2 in pairwise(self.instructions()):
            current_block = blocks[-1]
            current_block.add_instruction(i1)
            if ((i1.pc + i1.size) != i2.pc) or i1.is_control_flow or (i2.label is not None):
                for b in current_block.dominated_blocks:
                    edges[current_block.start].add(b)
                    inv_edges[b].add(current_block.start)
                blocks.append(Block(self))
        blocks[-1].add_instruction(i2)

        blocks = OrderedDict((b.start, b) for b in blocks)
        return blocks, edges, inv_edges

    def functions(self):
        blocks, edges, inv_edges = self.flow_graph()
        subroutines = self.labels({LabelType.SUBROUTINE, LabelType.VECTOR})

        functions = []
        for subroutine in subroutines.values():
            functions.append(self._bfs(edges, subroutine))

        return functions

    def _bfs(self, edges, start):
        visited = set()
        queue = [start]
        while queue:
            block = queue.pop(0)
            if block not in visited:
                visited.add(block)
                queue.extend(edges[block] - visited)
        return visited

    def incomplete_branches(self):
        # Get all the branches instructions:
        branches = (Instruction.from_row(self, i) for i in self._db.branches())
        # Select those that point to, or ar followed by, addresses that are not instructions:
        incomplete_branches = (i for i in branches if (self.instruction(i.pc + i.size) is None) or
                                                      (self.instruction(i.unique_reference) is None))
        return incomplete_branches
