class Block:
    """A basic block of instructions. that are always executed exactly once, in order.

    Attributes:
        instructions: A list of the instructions in the block.
    """

    def __init__(self, analyzer, instructions=None):
        self._analyzer = analyzer

        if instructions is None:
            self.instructions = []
        else:
            self.instructions = instructions

    def __iter__(self):
        return iter(self.instructions)

    def add_instruction(self, instruction):
        """Add an instruction at the end of the block.

        Args:
            instruction: The instruction to be added.
        """
        self.instructions.append(instruction)

    @property
    def first(self):
        """The first instruction in the block."""
        return self.instructions[0]

    @property
    def last(self):
        """The last instruction in the block."""
        return self.instructions[-1]

    @property
    def start(self):
        """The starting address of the block."""
        return self.first.pc

    @property
    def end(self):
        """The ending address of the block (not included)."""
        return self.last.pc + self.last.size

    @property
    def dominated_blocks(self):
        """The set of blocks that are might be executed right after the current one."""
        if self.last.is_return:
            return set()
        elif self.last.is_jump or self.last.mnemonic in ('bra', 'brl'):
            return {self.last.unique_reference}
        elif self.last.is_branch:
            return {self.last.unique_reference, self.end}
        else:
            return {self.end}
