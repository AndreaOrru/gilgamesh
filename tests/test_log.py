from abc import ABC
from unittest import TestCase

from gilgamesh.log import Log
from gilgamesh.rom import ROM
from gilgamesh.state import StateChange

from .test_rom import assemble


class LogTest(ABC):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble(cls.asm))

    def setUp(self):
        self.log = Log(self.rom)
        self.log.analyze()


class LoROMTest(LogTest, TestCase):
    asm = "lorom.asm"

    def test_initial_entry_points(self):
        self.assertIn((0x8000, 0b0011_0000, 0x8000), self.log.entry_points)
        self.assertEqual(self.log.subroutines[0x8000].label, "reset")

        self.assertIn((0x0000, 0b0011_0000, 0x0000), self.log.entry_points)
        self.assertEqual(self.log.subroutines[0x0000].label, "nmi")


class InfiniteLoopTest(LogTest, TestCase):
    asm = "infinite_loop.asm"

    def test_instructions(self):
        self.assertEqual(len(self.log.instructions), 1)

        subroutine = self.log.subroutines[0x8000]
        instruction = subroutine.instructions.popitem()[1]
        self.assertEqual(instruction.pc, 0x8000)
        self.assertEqual(instruction.name, "jmp")
        self.assertEqual(instruction.absolute_argument, 0x8000)


class StateChangeTest(LogTest, TestCase):
    asm = "state_change.asm"

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


class ElidableStateChangeTest(LogTest, TestCase):
    asm = "elidable_state_change.asm"

    def test_instructions(self):
        self.assertEqual(len(self.log.instructions), 10)

    def test_sub_state_change_elided(self):
        sub = self.log.subroutines[0x800A]
        self.assertEqual(len(sub.state_changes), 1)

        change = next(iter(sub.state_changes))
        self.assertEqual(change.m, None)
        self.assertEqual(change.x, None)


class PhpPlpTest(LogTest, TestCase):
    asm = "php_plp.asm"

    def test_instructions(self):
        self.assertEqual(len(self.log.instructions), 9)

    def test_sub_state_change_elided(self):
        sub = self.log.subroutines[0x800A]
        self.assertEqual(len(sub.state_changes), 1)

        change = next(iter(sub.state_changes))
        self.assertEqual(change.m, None)
        self.assertEqual(change.x, None)


class JumpInsideSubroutineTest(LogTest, TestCase):
    asm = "jump_inside_subroutine.asm"

    def test_sub_state_change(self):
        sub = self.log.subroutines[0x8016]
        self.assertEqual(len(sub.state_changes), 1)

        change = next(iter(sub.state_changes))
        self.assertEqual(change.m, 0)


class UnknownJumpTest(LogTest, TestCase):
    asm = "unknown_jump.asm"

    def test_sub_state_change_unknown(self):
        reset = self.log.subroutines_by_label["reset"]
        sub = self.log.subroutines[0x800B]

        self.assertSetEqual(sub.state_changes, {StateChange(unknown=True)})
        self.assertTrue(sub.has_unknown_return_state())

        self.assertNotIn(0x8005, reset.instructions)
        self.assertNotIn(0x800E, sub.instructions)

        self.assertTrue(reset.instructions[0x8002].stopped_execution)
        self.assertTrue(sub.instructions[0x800B].stopped_execution)

    def test_assert_state_change(self):
        sub = self.log.subroutines[0x800B]
        self.log.set_subroutine_state_change(sub, StateChange())

        self.log.analyze()
        reset = self.log.subroutines_by_label["reset"]
        sub = self.log.subroutines[0x800B]

        self.assertIn(0x8005, reset.instructions)
        self.assertIn(0x8008, reset.instructions)
        self.assertFalse(sub.has_unknown_return_state())
