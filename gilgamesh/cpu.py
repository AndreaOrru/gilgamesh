from ctypes import c_int8, c_int16

from gilgamesh.instruction import Instruction
from gilgamesh.opcodes import AddressMode as Mode


class CPU:
    def __init__(self, analyzer, rom, pc, flags):
        self._analyzer = analyzer
        self._rom = rom
        self.pc = pc
        self.flags = flags

    def execute(self, trace=False):
        # Fetch the opcode from the ROM:
        opcode = self._rom.read_byte(self.pc)

        # Parse the instruction and its operand:
        i = Instruction(self._analyzer, self.pc, opcode, self.flags)
        i.operand = self._rom.read_value(i.pc + 1, i.size - 1)
        # Advance the CPU's Program Counter:
        self.pc += i.size

        # Actually emulate the instruction:
        ref = self._dispatch_instruction(i)
        if trace:
            self._analyzer.store_instruction(i)
            if ref is not None:
                self._analyzer._db.store_reference(i.pc, ref)

        return i

    def _dispatch_instruction(self, i):
        ref = None
        if i.is_branch:
            ref = self._branch(i)
        elif i.is_jump:
            ref = self._jump(i)
        elif i.is_call:
            ref = self._call(i)
        elif i.is_return:
            self._return(i)
        elif i.mnemonic == 'rep':
            self._rep(i)
        elif i.mnemonic == 'sep':
            self._sep(i)
        return ref

    def run(self, trace=False):
        yield self.execute(trace)
        while (self.pc is not None) and self._analyzer.instruction(self.pc) is None:
            yield self.execute(trace)

    def _rep(self, i):
        self.flags &= ~i.operand

    def _sep(self, i):
        self.flags |= i.operand

    def _branch_always(self, i):
        if i.address_mode == Mode.RELATIVE:
            self.pc += c_int8(i.operand).value
        elif i.address_mode == Mode.RELATIVE_LONG:
            self.pc += c_int16(i.operand).value
        return self.pc

    def _branch(self, i):
        if i.mnemonic in ('bra', 'brl'):
            return self._branch_always(i)
        else:
            branch_pc = self.pc + c_int8(i.operand).value
            branch_cpu = CPU(self._analyzer, self._rom, branch_pc, self.flags)
            branch_cpu.run()
            return branch_pc

    def _jump(self, i):
        self.pc = self._decode_address_operand(self.pc, i.operand, i.address_mode)
        return self.pc

    def _call(self, i):
        call_pc = self._decode_address_operand(self.pc, i.operand, i.address_mode)
        call_cpu = CPU(self._analyzer, self._rom, call_pc, self.flags)
        call_cpu.run()
        self.flags = call_cpu.flags
        return call_pc

    def _return(self, i):
        self.pc = None

    @staticmethod
    def _decode_address_operand(pc, operand, mode):
        # TODO: handle indirect jumps when possible.
        if mode == Mode.ABSOLUTE:
            return (pc & 0xFF0000) | operand
        elif mode == Mode.ABSOLUTE_LONG:
            return operand
        else:
            return None
