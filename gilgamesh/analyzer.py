"""Static analyzer."""

from collections import defaultdict
from collections import OrderedDict
from enum import Enum

from bidict import bidict

from gilgamesh.block import Block
from gilgamesh.database import VectorType
from gilgamesh.instruction import Instruction
from gilgamesh.opcodes import OpcodeCategory
from gilgamesh.utils import pairwise


class LabelType(Enum):
    """Types of labels."""
    JUMP = 0
    SUBROUTINE = 1
    VECTOR = 2


class Analyzer:
    """Static analyzer for the ROM's code and data flow."""

    def __init__(self, db):
        self._db = db
        self.analyze()

    def analyze(self):
        """Reanalyze the ROM and regenerate the labels."""
        self._labels = self.labels()

    def write_database(self):
        """Save the database changes to disk."""
        self._db.save()

    def store_instruction(self, i):
        """Store a new instruction into the database.

        Args:
            i: The instruction to be stored.
        """
        self._db.store_instruction(i.pc, i.opcode.number, i.flags, i.operand)

    def instruction(self, pc):
        """Search for an instruction in the database.

        Args:
            pc: The address of the instruction.

        Returns:
            The corresponding Instruction object, or None
        """
        instruction = self._db.instruction(pc)
        return None if (instruction is None) else Instruction.from_row(self, instruction)

    def instructions(self, start=0x000000, end=0xFFFFFF):
        """Search for a instructions inside an address interval.

        Args:
            start: The start of the interval.
            end: The end of the interval (included).

        Returns:
            An iterator over all the Instruction objects in the range.
        """
        instructions = self._db.instructions(start, end)
        return (Instruction.from_row(self, i) for i in instructions)

    def label(self, address):
        """Search for a label for the given address.

        Args:
            address: The address to search for.

        Returns:
            The associated label, or None if no one could be found.
        """
        try:
            return self._labels.inv[address]
        except KeyError:
            return None

    def label_address(self, label):
        """Search for the address associated with a label.

        Args:
            label: The label to search for.

        Returns:
            The associated address.

        Raises:
            KeyError if no associated address could be found.
        """
        return self._labels[label]

    def labels(self, types=None):
        """Generate all the labels in the program.

        Args:
            types: A set of LabelTypes, or None for all of them.

        Returns:
            A bidirectional dictionary from labels to addresses and viceversa.
        """
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
        """Generate a Control Flow Graph of the program.

        Returns:
            blocks: An ordered dictionary of all the Blocks.
            edges: A dictionary of all the directed edges between blocks.
            inv_edges: A dictionary of all the inverted directed edges.
        """
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
        """Generate all the functions in the program.

        Returns:
            A list of all the functions.
        """
        blocks, edges, _ = self.flow_graph()
        subroutines = self.labels({LabelType.SUBROUTINE, LabelType.VECTOR})

        functions = []
        for subroutine in subroutines.values():
            functions.append([blocks[b] for b in sorted(self._bfs(edges, subroutine))])

        return functions

    @staticmethod
    def _bfs(edges, start):
        """Run BFS on a Control Flow Graph.

        Args:
            edges: The edges of the graph.
            start: The block from which to start the search.

        Returns:
            A set of the visited blocks.
        """
        visited = set()
        queue = [start]
        while queue:
            block = queue.pop(0)
            if block not in visited:
                visited.add(block)
                queue.extend(edges[block] - visited)
        return visited

    def incomplete_branches(self):
        """Search for all the incomplete branches in the program.

        "Incomplete branches" are defined as branches for which at least one
        of the two possible control flows have not been executed at runtime.

        Returns:
            A generator expression of all the incomplete branches.
        """
        # Get all the branches instructions:
        branches = (Instruction.from_row(self, i) for i in self._db.branches())
        # Select those that point to, or ar followed by, addresses that are not instructions:
        incomplete_branches = (i for i in branches if (self.instruction(i.pc + i.size) is None) or
                                                      (self.instruction(i.unique_reference) is None))
        return incomplete_branches
