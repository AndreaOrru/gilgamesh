from ctypes import c_int8, c_int16

from gilgamesh.instruction import Instruction
from gilgamesh.opcodes import AddressMode as Mode


class CPU:
    """Minimal abstraction of a R65816 processor.

    Holds the state of the processor at a given time.
    Provides basic symbolic execution to expand the known flow graph.

    Attributes:
        pc: The value of the Program Counter register.
        flags: The value of the P flags register.
    """

    def __init__(self, analyzer, rom, pc, flags):
        self._analyzer = analyzer
        self._rom = rom
        self.pc = pc
        self.flags = flags

    def execute(self):
        """Execute a CPU instruction and log it into the database.

        Note that it might actually execute more instructions
        in case a branch has to be explored.
        """
        # Fetch the opcode from the ROM:
        opcode = self._rom.read_byte(self.pc)

        # Parse the instruction and its operand:
        i = Instruction(self._analyzer, self.pc, opcode, self.flags)
        i.operand = self._rom.read_value(i.pc + 1, i.size - 1)
        # Advance the CPU's Program Counter:
        self.pc += i.size  # FIXME: what happens at bank borders?

        # Actually emulate the instruction:
        ref = self._dispatch_instruction(i)
        self._analyzer.store_instruction(i)
        if ref is not None:
            self._analyzer._db.store_reference(i.pc, ref)

        return i

    def _dispatch_instruction(self, i):
        """Dispatch the execution of the instruction to the right emulation method.

        Args:
            i: The instruction.

        Return:
            The address that the instruction references, or None.
        """
        ref = None
        if i.is_branch:
            ref = self._branch(i)
        elif i.is_jump:
            ref = self._jump(i)
        elif i.is_call:
            ref = self._call(i)
        elif i.is_return:
            self._return()
        elif i.mnemonic == 'rep':
            self._rep(i)
        elif i.mnemonic == 'sep':
            self._sep(i)
        return ref

    def run(self):
        """Run the emulation till a known instruction is found.

        Logs the executed instructions into the database."""
        yield self.execute()
        while (self.pc is not None) and self._analyzer.instruction(self.pc) is None:
            yield self.execute()

    def _rep(self, i):
        """Emulate the REP instruction.

        Args:
            i: The instruction.
        """
        self.flags &= ~i.operand

    def _sep(self, i):
        """Emulate the SEP instruction.

        Args:
            i: The instruction.
        """
        self.flags |= i.operand

    def _branch_always(self, i):
        """Emulate the BRA and BRL instructions.

        Args:
            i: The instruction.

        Returns:
            The target of the branch.
        """
        if i.address_mode == Mode.RELATIVE:
            self.pc += c_int8(i.operand).value
        elif i.address_mode == Mode.RELATIVE_LONG:
            self.pc += c_int16(i.operand).value
        return self.pc

    def _branch(self, i):
        """Emulate all branch instructions.

        Note that a conditional branch will cause another
        CPU instance to be created and run.

        Args:
            i: The instruction.

        Returns:
            The target of the branch.
        """
        if i.mnemonic in ('bra', 'brl'):
            return self._branch_always(i)
        else:
            branch_pc = self.pc + c_int8(i.operand).value
            branch_cpu = CPU(self._analyzer, self._rom, branch_pc, self.flags)
            branch_cpu.run()
            return branch_pc

    def _jump(self, i):
        """Emulate the JMP instruction.

        Args:
            i: The instruction.

        Returns:
            The target of the branch.
        """
        self.pc = self._decode_address_operand(i)
        return self.pc

    def _call(self, i):
        """Emulate the JSR instruction.

        Args:
            i: The instruction.

        Returns:
            The target of the call.
        """
        call_pc = self._decode_address_operand(i)
        call_cpu = CPU(self._analyzer, self._rom, call_pc, self.flags)
        call_cpu.run()
        self.flags = call_cpu.flags
        return call_pc

    def _return(self):
        """Emulate the RTS/RTL/RTI instructions."""
        self.pc = None

    @staticmethod
    def _decode_address_operand(i):
        """Decode the address operand of a control flow instruction.

        Args:
            i: The instruction to decode.

        Returns:
            The address expressed in the operand, or None if not inferable.
        """
        # TODO: handle indirect jumps when possible.
        if i.opcode.address_mode == Mode.ABSOLUTE:
            return ((i.pc + i.size) & 0xFF0000) | i.operand
        elif i.opcode.address_mode == Mode.ABSOLUTE_LONG:
            return i.operand
        else:
            return None
