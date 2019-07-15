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
        self.log.analyze()

    def test_instructions(self):
        self.assertEqual(len(self.log.instructions), 1)

        subroutine = self.log.subroutines[0x8000]
        instruction = subroutine.instructions.popitem()[1]
        self.assertEqual(instruction.pc, 0x8000)
        self.assertEqual(instruction.name, "jmp")
        self.assertEqual(instruction.absolute_argument, 0x8000)


class StateChangeTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("state_change.asm"))

    def setUp(self):
        self.log = Log(self.rom)
        self.log.analyze()

    def test_instructions(self):
        self.assertEqual(len(self.log.instructions), 7)

    def test_sub_state_change(self):
        sub = self.log.subroutines[0x800E]
        self.assertEqual(len(sub.state_changes), 1)

        change = next(iter(sub.state_changes))
        self.assertEqual(change.m, 0)
        self.assertEqual(change.x, 0)

    def test_lda_ldx_size(self):
        reset = self.log.subroutines_by_label["reset"]
        lda = reset.instructions[0x8005]
        ldx = reset.instructions[0x8008]

        self.assertEqual(lda.name, "lda")
        self.assertEqual(lda.argument_size, 2)

        self.assertEqual(ldx.name, "ldx")
        self.assertEqual(ldx.argument_size, 2)


class ElidableStateChangeTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("elidable_state_change.asm"))

    def setUp(self):
        self.log = Log(self.rom)
        self.log.analyze()

    def test_instructions(self):
        self.assertEqual(len(self.log.instructions), 10)

    def test_sub_state_change(self):
        sub = self.log.subroutines[0x800A]
        self.assertEqual(len(sub.state_changes), 1)

        change = next(iter(sub.state_changes))
        self.assertEqual(change.m, None)
        self.assertEqual(change.x, None)


class JumpInsideSubroutineTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("jump_inside_subroutine.asm"))

    def setUp(self):
        self.log = Log(self.rom)
        self.log.analyze()

    def test_sub_state_change(self):
        sub = self.log.subroutines[0x8016]
        self.assertEqual(len(sub.state_changes), 1)

        change = next(iter(sub.state_changes))
        self.assertEqual(change.m, 0)
