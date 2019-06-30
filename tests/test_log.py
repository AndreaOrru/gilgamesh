from unittest import TestCase

from gilgamesh.log import Log
from gilgamesh.rom import ROM

from .test_rom import assemble


class SimpleTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("lorom.asm"))

    def setUp(self):
        self.log = Log(self.rom)

    def test_initial_entry_points(self):
        self.assertIn((0x8000, 0b0011_0000, 0x8000), self.log.entry_points)
        self.assertEqual(self.log.subroutines[0x8000].label, "reset")

        self.assertIn((0x0000, 0b0011_0000, 0x0000), self.log.entry_points)
        self.assertEqual(self.log.subroutines[0x0000].label, "nmi")


class LoopTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("infinite_loop.asm"))

    def setUp(self):
        self.log = Log(self.rom)

    def test_instructions(self):
        self.log.analyze()
        self.assertEqual(len(self.log.instructions), 1)

        subroutine = self.log.subroutines[0x8000]
        instruction = subroutine.instructions.popitem()[1]
        self.assertEqual(instruction.pc, 0x8000)
        self.assertEqual(instruction.name, "jmp")
        self.assertEqual(instruction.absolute_argument, 0x8000)
