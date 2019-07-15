from unittest import TestCase

from gilgamesh.types import s8, s16


class TypesTest(TestCase):
    def test_s8(self):
        self.assertEqual(s8(0xFFFF), -1)

    def test_s16(self):
        self.assertEqual(s16(0xFFFF), -1)
