from unittest import TestCase

from gilgamesh.analysis import Analysis
from gilgamesh.rom import ROM

from .test_rom import assemble


class SimpleTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("lorom.asm"))

    def setUp(self):
        self.analysis = Analysis(self.rom)

    def test_initial_entry_points(self):
        self.assertIn((0x8000, 0b0000_0000, 0x8000), self.analysis.entry_points)
        self.assertEqual(self.analysis.subroutines[0x8000].label, "reset")

        self.assertIn((0x0000, 0b0000_0000, 0x0000), self.analysis.entry_points)
        self.assertEqual(self.analysis.subroutines[0x0000].label, "nmi")


class LoopTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("infinite_loop.asm"))

    def setUp(self):
        self.analysis = Analysis(self.rom)

    def test_instructions(self):
        self.analysis.run()
        self.assertEqual(len(self.analysis.instructions), 1)

        instruction = self.analysis.instructions.popitem()[1]
        self.assertEqual(instruction.pc, 0x8000)
        self.assertEqual(instruction.name, "jmp")
        self.assertEqual(instruction.absolute_argument, 0x8000)
