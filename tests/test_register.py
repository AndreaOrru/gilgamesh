from unittest import TestCase

from gilgamesh.registers import Register
from gilgamesh.state import State


class RegisterTest(TestCase):
    def test_register(self):
        state = State(m=1, x=1)

        a = Register(state, True)
        x = Register(state, False)

        a.set(0xFF)
        self.assertEqual(a.lo, 0xFF)
        self.assertEqual(a.hi, None)
        self.assertEqual(a.get(), 0xFF)
        state.m = 0
        self.assertEqual(a.get(), None)

        x.set(0xFF)
        self.assertEqual(x.lo, 0xFF)
        self.assertEqual(x.hi, None)
        self.assertEqual(x.get(), 0xFF)
        state.x = 0
        self.assertEqual(x.get(), None)
