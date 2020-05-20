from unittest import TestCase

from tests.test_log import LogTest


class JumpTablesTest(LogTest, TestCase):
    asm = "jump_tables.asm"

    def test_value_of_register_changes(self):
        reset = self.log.subroutines_by_label["reset"]
        self.assertTrue(reset.has_unknown_return_state)
        self.assertEqual(len(reset.indirect_jumps), 1)
        self.assertTrue(reset.has_incomplete_jump_table)

        self.log.assert_jump(0x8000, 0x8100, 0)
        self.log.assert_jump(0x8000, 0x8200, 0)
        self.log.analyze()

        reset = self.log.subroutines_by_label["reset"]
        self.assertIn(0x8100, self.log.subroutines)
        self.assertIn(0x8200, self.log.subroutines)
        self.assertFalse(reset.has_unknown_return_state)
        self.assertEqual(len(reset.indirect_jumps), 1)
        self.assertTrue(reset.has_incomplete_jump_table)

        self.log.complete_jump_tables.add(0x8000)
        self.assertFalse(reset.has_incomplete_jump_table)
