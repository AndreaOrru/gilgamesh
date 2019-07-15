from unittest import TestCase

from gilgamesh.state import State, StateChange


class StateTestCase(TestCase):
    def test_repr(self):
        state = State(m=1, x=1)
        self.assertEqual(repr(state), "<State: M=1, X=1>")

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


class StateChangeTestCase(TestCase):
    def test_repr(self):
        change = StateChange()
        self.assertEqual(repr(change), "<StateChange: None>")

        change = StateChange(m=1)
        self.assertEqual(repr(change), "<StateChange: M=1>")

        change = StateChange(m=1, x=1)
        self.assertEqual(repr(change), "<StateChange: M=1, X=1>")

    def test_eq_hash(self):
        changes = set()
        changes.add(StateChange(m=1, x=1))
        changes.add(StateChange(m=1, x=1))
        changes.add(StateChange(m=0, x=0))
        self.assertEqual(len(changes), 2)

    def test_set_reset(self):
        change = StateChange()

        change.set(0b0011_0000)
        self.assertEqual(change.m, 1)
        self.assertEqual(change.x, 1)

        change.reset(0b0011_0000)
        self.assertEqual(change.m, 0)
        self.assertEqual(change.x, 0)

    def test_apply_assertion(self):
        change = StateChange(m=1, x=1)
        assertion = StateChange(m=1, x=None)

        change.apply_assertion(assertion)
        self.assertEqual(change.m, None)
        self.assertEqual(change.x, 1)
