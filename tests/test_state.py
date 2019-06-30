from unittest import TestCase

from gilgamesh.state import State


class StateTestCase(TestCase):
    def test_defaults_to_8bits(self):
        state = State()
        self.assertEqual(state.m, 1)
        self.assertEqual(state.x, 1)
        self.assertEqual(state.p, 0b0011_0000)

    def test_sizes(self):
        state = State(0b0011_0000)
        self.assertEqual(state.a_size, 1)
        self.assertEqual(state.x_size, 1)

        state = State(m=1, x=0)
        self.assertEqual(state.a_size, 1)
        self.assertEqual(state.x_size, 2)

        state = State(m=0, x=1)
        self.assertEqual(state.a_size, 2)
        self.assertEqual(state.x_size, 1)

    def test_p_register(self):
        state = State(m=0, x=0)
        self.assertEqual(state.p, 0b0000_0000)

        state = State(m=0, x=1)
        self.assertEqual(state.p, 0b0001_0000)

        state = State(m=1, x=1)
        self.assertEqual(state.p, 0b0011_0000)

    def test_set(self):
        state = State()
        state.set(0b0011_0000)
        self.assertEqual(state.m, 1)
        self.assertEqual(state.x, 1)

    def test_reset(self):
        state = State(m=1, x=1)
        state.reset(0b0011_0000)
        self.assertEqual(state.m, 0)
        self.assertEqual(state.x, 0)
