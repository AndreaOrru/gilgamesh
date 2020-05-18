from unittest import TestCase

from gilgamesh.snes.state import State, StateChange


class StateTest(TestCase):
    def test_repr(self):
        state = State(m=1, x=1)
        self.assertEqual(repr(state), "<State: m=1,x=1>")

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

    def test_from_state_expr(self):
        state = State.from_expr("m=0,x=1")
        self.assertEqual(state, State(m=0, x=1))

        state = State.from_expr("x=0,m=1")
        self.assertEqual(state, State(x=0, m=1))

    def test_state_expr(self):
        state = State(m=1, x=1)
        self.assertEqual(state.expr, "m=1,x=1")


class StateChangeTest(TestCase):
    def test_repr(self):
        change = StateChange()
        self.assertEqual(repr(change), "<StateChange: none>")

        change = StateChange(unknown=True)
        self.assertEqual(repr(change), "<StateChange: unknown>")

        change = StateChange(m=1)
        self.assertEqual(repr(change), "<StateChange: m=1>")

        change = StateChange(m=1, x=1)
        self.assertEqual(repr(change), "<StateChange: m=1,x=1>")

    def test_from_state_expr(self):
        change = StateChange.from_expr("none")
        self.assertEqual(change, StateChange())

        change = StateChange.from_expr("m=0")
        self.assertEqual(change, StateChange(m=0))
        change = StateChange.from_expr("x=1")
        self.assertEqual(change, StateChange(x=1))

        change = StateChange.from_expr("m=0,x=1")
        self.assertEqual(change, StateChange(m=0, x=1))
        change = StateChange.from_expr("x=0,m=1")
        self.assertEqual(change, StateChange(x=0, m=1))

    def test_state_expr(self):
        change = StateChange()
        self.assertEqual(change.expr, "none")

        change = StateChange(m=0)
        self.assertEqual(change.expr, "m=0")
        change = StateChange(x=1)
        self.assertEqual(change.expr, "x=1")

        change = StateChange(m=0, x=1)
        self.assertEqual(change.expr, "m=0,x=1")

    def test_eq_hash(self):
        changes = set()

        changes.add(StateChange(m=0, unknown=True))
        changes.add(StateChange(m=1, unknown=True))

        changes.add(StateChange(m=1, x=1))
        changes.add(StateChange(m=1, x=1))

        self.assertEqual(len(changes), 2)

    def test_set_reset(self):
        change = StateChange()

        change.set(0b0011_0000)
        self.assertEqual(change.m, 1)
        self.assertEqual(change.x, 1)

        change.reset(0b0011_0000)
        self.assertEqual(change.m, 0)
        self.assertEqual(change.x, 0)

    def test_apply_inference(self):
        change = StateChange(m=1, x=1)
        inference = StateChange(m=1, x=None)

        change.apply_inference(inference)
        self.assertEqual(change.m, None)
        self.assertEqual(change.x, 1)

    def test_simplify(self):
        state = State(m=0, x=1)

        change = StateChange()
        self.assertEqual(change.simplify(state), StateChange())

        change = StateChange(m=0)
        self.assertEqual(change.simplify(state), StateChange())

        change = StateChange(m=0, x=1)
        self.assertEqual(change.simplify(state), StateChange())

        change = StateChange(m=0, x=0)
        self.assertEqual(change.simplify(state), StateChange(x=0))

        change = StateChange(unknown=True)
        self.assertEqual(change.simplify(state), StateChange(unknown=True))
