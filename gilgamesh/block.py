from gilgamesh.opcodes import OpcodeCategory


class Block:
    def __init__(self, analyzer, instructions=None):
        self._analyzer = analyzer

        if instructions is None:
            self.instructions = []
        else:
            self.instructions = instructions

    def __iter__(self):
        return iter(self.instructions)

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

    @property
    def first(self):
        return self.instructions[0]

    @property
    def last(self):
        return self.instructions[-1]

    @property
    def start(self):
        return self.first.pc

    @property
    def end(self):
        return self.last.pc + self.last.size

    @property
    def dominated_blocks(self):
        if self.last.is_return:
            return []
        elif self.last.is_jump or self.last.mnemonic in ('bra', 'brl'):
            return [self.last.unique_reference]
        elif self.last.is_call or self.last.is_branch:
            return [self.last.unique_reference, self.end]
        else:
            return [self.end]
