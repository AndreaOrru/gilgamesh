from unittest import TestCase

from gilgamesh.utils.invalidable import Invalidable, InvalidObjectError, bulk_invalidate
from tests.test_log import LogTest


class Obj(Invalidable):
    def fun(self):
        ...


class InvalidableTest(TestCase):
    def test_invalidate(self):
        obj = Obj()
        obj.fun()

        obj.invalidate()
        with self.assertRaises(InvalidObjectError):
            obj.fun()

    def test_bulk_invalidate(self):
        objs = [Obj(), Obj(), Obj()]
        for obj in objs:
            obj.fun()

        bulk_invalidate(objs)
        for obj in objs:
            with self.assertRaises(InvalidObjectError):
                obj.fun()


class AnalysisInvalidableTest(LogTest, TestCase):
    asm = "unknown_jump.asm"

    def test_cant_access_invalid_objects(self):
        reset_subroutine = self.log.subroutines_by_label["reset"]
        other_subroutine = self.log.subroutines[0x800B]
        reset_instruction = next(iter(reset_subroutine.instructions.values()))
        other_instruction = next(iter(other_subroutine.instructions.values()))

        self.log.reset()
        self.log.analyze()

        with self.assertRaises(InvalidObjectError):
            self.assertEqual(reset_subroutine.label, "reset")
        with self.assertRaises(InvalidObjectError):
            self.assertEqual(other_subroutine.label, "sub_00800B")
        with self.assertRaises(InvalidObjectError):
            self.assertEqual(reset_instruction.pc, 0x8000)
        with self.assertRaises(InvalidObjectError):
            self.assertEqual(other_instruction.pc, 0x800B)
