import os
from abc import ABC
from unittest import TestCase

from gilgamesh.log import EntryPoint, Log
from gilgamesh.rom import ROM
from gilgamesh.state import StateChange
from tests.test_rom import assemble


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
        self.assertEqual(
            self.log.entry_points[0x8000], EntryPoint("reset", 0b0011_0000)
        )
        self.assertEqual(self.log.subroutines[0x8000].label, "reset")

        self.assertEqual(self.log.entry_points[0x0000], EntryPoint("nmi", 0b0011_0000))
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

        change = sub.state_change
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

        change = sub.state_change
        self.assertEqual(change.m, None)
        self.assertEqual(change.x, None)


class PhpPlpTest(LogTest, TestCase):
    asm = "php_plp.asm"

    def test_instructions(self):
        self.assertEqual(len(self.log.instructions), 9)

    def test_sub_state_change_elided(self):
        sub = self.log.subroutines[0x800A]
        self.assertEqual(len(sub.state_changes), 1)

        change = sub.state_change
        self.assertEqual(change.m, None)
        self.assertEqual(change.x, None)


class JumpInsideSubroutineTest(LogTest, TestCase):
    asm = "jump_inside_subroutine.asm"

    def test_sub_state_change(self):
        sub = self.log.subroutines[0x8016]
        self.assertEqual(len(sub.state_changes), 1)

        change = sub.state_change
        self.assertEqual(change.m, 0)


class UnknownJumpTest(LogTest, TestCase):
    asm = "unknown_jump.asm"

    def tearDown(self):
        try:
            os.remove(self.rom.glm_path)
        except OSError:
            pass

    def test_sub_state_change_unknown(self):
        reset = self.log.subroutines_by_label["reset"]
        sub = self.log.subroutines[0x800B]

        self.assertSetEqual(sub.state_changes, {StateChange(unknown=True)})
        self.assertTrue(sub.has_jump_table)
        self.assertTrue(sub.has_unknown_return_state)

        self.assertNotIn(0x8005, reset.instructions)
        self.assertNotIn(0x800E, sub.instructions)

        self.assertTrue(reset.instructions[0x8002].stopped_execution)
        self.assertTrue(sub.instructions[0x800B].stopped_execution)

    def test_assert_state_change(self):
        # Assertion.
        unknown = self.log.subroutines[0x800B]
        self.log.assert_subroutine_state_change(unknown, StateChange())
        self.assertTrue(self.log.dirty)
        self.log.analyze()
        self.assertFalse(self.log.dirty)

        reset = self.log.subroutines_by_label["reset"]
        unknown = self.log.subroutines[0x800B]

        self.assertIn(0x8005, reset.instructions)
        self.assertIn(0x8008, reset.instructions)
        self.assertTrue(unknown.has_jump_table)
        self.assertTrue(unknown.has_asserted_state_change)
        self.assertFalse(unknown.has_unknown_return_state)

        # Deassertion.
        self.log.deassert_subroutine_state_change(0x800B)
        self.assertTrue(self.log.dirty)
        self.log.analyze()
        self.assertFalse(self.log.dirty)

        unknown = self.log.subroutines[0x800B]
        self.assertFalse(unknown.has_asserted_state_change)
        self.assertTrue(unknown.has_unknown_return_state)

    def test_load_save(self):
        unknown = self.log.subroutines[0x800B]
        self.log.rename_label(unknown.label, "unknown")
        self.log.save()

        self.log.reset()
        self.log.analyze()
        unknown = self.log.subroutines[0x800B]
        self.assertNotEqual(unknown.label, "unknown")

        self.log.load()
        unknown = self.log.subroutines[0x800B]
        self.assertEqual(unknown.label, "unknown")


class SimplifiableReturnState(LogTest, TestCase):
    asm = "simplifiable_return_state.asm"

    def test_double_state_change_simplification(self):
        reset = self.log.subroutines_by_label["reset"]

        # double_state_change is simplified.
        self.assertIn(0x8005, reset.instructions)
        self.assertIn(0x8008, reset.instructions)

        double_state_sub = self.log.subroutines[0x8017]
        self.assertFalse(double_state_sub.has_unknown_return_state)
        self.assertEqual(len(double_state_sub.state_changes), 2)

        unknown_sub = self.log.subroutines[0x801F]
        self.assertTrue(unknown_sub.has_jump_table)
        self.assertTrue(unknown_sub.has_unknown_return_state)

    def test_instruction_state_change_assertion(self):
        # Assertion.
        self.log.assert_instruction_state_change(0x8024, StateChange())
        self.assertTrue(self.log.dirty)
        self.log.analyze()
        self.assertFalse(self.log.dirty)

        unknown_sub = self.log.subroutines[0x801F]
        self.assertTrue(unknown_sub.has_jump_table)
        self.assertTrue(unknown_sub.instruction_has_asserted_state_change)
        self.assertFalse(unknown_sub.has_unknown_return_state)

        # Deassertion.
        self.log.deassert_instruction_state_change(0x8024)
        self.assertTrue(self.log.dirty)
        self.log.analyze()
        self.assertFalse(self.log.dirty)

        unknown_sub = self.log.subroutines[0x801F]
        self.assertFalse(unknown_sub.instruction_has_asserted_state_change)
        self.assertTrue(unknown_sub.has_unknown_return_state)


class SuspectInstructionsTest(LogTest, TestCase):
    asm = "suspect_instructions.asm"

    def test_detects_suspect_instruction(self):
        reset = self.log.subroutines_by_label["reset"]
        self.assertTrue(reset.has_suspect_instructions)
        self.assertTrue(reset.has_unknown_return_state)


class StackManipulationTest(LogTest, TestCase):
    asm = "stack_manipulation.asm"

    def test_stack_manipulation_is_detected(self):
        reset = self.log.subroutines_by_label["reset"]
        self.assertNotIn(0x8004, reset.instructions)

        manipulation_sub = self.log.subroutines[0x8008]
        self.assertTrue(manipulation_sub.has_unknown_return_state)


class ChangeRegisterTest(LogTest, TestCase):
    asm = "change_register.asm"

    def test_value_of_register_changes(self):
        reset = self.log.subroutines_by_label["reset"]

        # LDA
        self.assertEqual(reset.instructions[0x8006].registers["a"], 0x1234)
        self.assertEqual(reset.instructions[0x8008].registers["a"], 0x34)
        self.assertEqual(reset.instructions[0x800C].registers["a"], None)
        self.assertEqual(reset.instructions[0x800E].registers["a"], 0xFF)
        self.assertEqual(reset.instructions[0x8010].registers["a"], 0x12FF)

        # ADC
        self.assertEqual(reset.instructions[0x8013].registers["a"], 0x13FF)
        self.assertEqual(reset.instructions[0x8019].registers["a"], 0x1300)
