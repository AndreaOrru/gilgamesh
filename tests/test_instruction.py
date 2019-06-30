from unittest import TestCase

from gilgamesh.instruction import Instruction, InstructionID
from gilgamesh.opcodes import AddressMode, Op


class InstructionTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        instruction_id = InstructionID(pc=0x000000, p=0b0000_0000, subroutine=0x000000)
        cls.brl = Instruction(*instruction_id, opcode=0x82, argument=0xFFFD)
        cls.lda = Instruction(*instruction_id, opcode=0xA9, argument=0x1234)

    def test_name(self):
        self.assertEqual(self.brl.name, "brl")
        self.assertEqual(self.lda.name, "lda")

    def test_operation(self):
        self.assertEqual(self.brl.operation, Op.BRL)
        self.assertEqual(self.lda.operation, Op.LDA)

    def test_address_mode(self):
        self.assertEqual(self.brl.address_mode, AddressMode.RELATIVE_LONG)
        self.assertEqual(self.lda.address_mode, AddressMode.IMMEDIATE_M)

    def test_size(self):
        self.assertEqual(self.brl.size, 3)
        self.assertEqual(self.lda.size, 3)

    def test_argument_size(self):
        self.assertEqual(self.brl.argument_size, 2)
        self.assertEqual(self.lda.argument_size, 2)

    def test_argument(self):
        self.assertEqual(self.brl.argument, 0xFFFD)
        self.assertEqual(self.lda.argument, 0x1234)

    def test_absolute_argument(self):
        self.assertEqual(self.brl.absolute_argument, 0x000000)
        self.assertEqual(self.lda.argument, 0x1234)

    def test_type(self):
        self.assertFalse(self.brl.is_branch)
        self.assertTrue(self.brl.is_jump)
        self.assertTrue(self.brl.is_control)

        self.assertFalse(self.lda.is_control)
        self.assertFalse(self.lda.is_sep_rep)