from copy import copy
from typing import Optional

M_BIT = 5
X_BIT = 4


class State:
    def __init__(self, p=0b0011_0000, m: Optional[int] = None, x: Optional[int] = None):
        # State can be specified by either passing a P integer value,
        # or individual M & X values to specify A and X/Y sizes.
        if (m is None) and (x is None):
            self.p = p
        else:
            assert (m is not None) and (x is not None)
            self.p = m << M_BIT
            self.p |= x << X_BIT

    def __repr__(self) -> str:
        return f"<State: M={self.m}, X={self.x}>"

    def __eq__(self, other) -> bool:
        return self.p == other.p

    def __hash__(self) -> int:
        return hash(self.p)

    @property
    def m(self) -> int:
        return (self.p >> M_BIT) & 1

    @m.setter
    def m(self, m: int) -> None:
        if m:
            self.set(1 << M_BIT)
        else:
            self.reset(1 << M_BIT)

    @property
    def x(self) -> int:
        return (self.p >> X_BIT) & 1

    @x.setter
    def x(self, x: int) -> None:
        if x:
            self.set(1 << X_BIT)
        else:
            self.reset(1 << X_BIT)

    @property
    def a_size(self) -> int:
        return 1 if self.m else 2

    @property
    def x_size(self) -> int:
        return 1 if self.x else 2

    def set(self, p: int) -> None:
        p &= (1 << M_BIT) | (1 << X_BIT)
        self.p |= p

    def reset(self, p: int) -> None:
        p &= (1 << M_BIT) | (1 << X_BIT)
        p = ~p & 0xFF
        self.p &= p


class StateChange:
    """Change in processor state caused by the execution of a subroutine."""

    def __init__(self, m: Optional[int] = None, x: Optional[int] = None, unknown=False):
        self.m = m
        self.x = x
        self.unknown = unknown

    @classmethod
    def from_state_expr(cls, expr: str) -> "StateChange":
        # TODO: Validate expression.
        if expr == "none":
            return cls()

        expressions = expr.split(",")
        if 1 <= len(expressions) <= 2:
            return cls(
                **{
                    str(register): int(value)
                    for register, value in (e.split("=") for e in expressions)
                }
            )
        else:
            raise Exception("Unknown syntax")

    @property
    def state_expr(self) -> str:
        r = ""
        m_str = [f"m={self.m}"] if self.m is not None else []
        x_str = [f"x={self.x}"] if self.x is not None else []
        if m_str or x_str:
            r += ",".join([*m_str, *x_str])
        else:
            r += "none"
        return r

    def __repr__(self) -> str:
        if self.unknown:
            return "<StateChange: UNKNOWN>"
        r = "<StateChange: "
        m_str = [f"M={self.m}"] if self.m is not None else []
        x_str = [f"X={self.x}"] if self.x is not None else []
        if m_str or x_str:
            r += ", ".join([*m_str, *x_str])
        else:
            r += "None"
        return r + ">"

    def __eq__(self, other) -> bool:
        return (self.unknown and other.unknown) or (
            (self.m == other.m) and (self.x == other.x)
        )

    def __hash__(self) -> int:
        if self.unknown:
            return hash((None, None, self.unknown))
        return hash((self.m, self.x, self.unknown))

    def set(self, p_change: int) -> None:
        change = State(p_change)
        self.m = 1 if change.m else self.m
        self.x = 1 if change.x else self.x

    def reset(self, p_change: int) -> None:
        change = State(p_change)
        self.m = 0 if change.m else self.m
        self.x = 0 if change.x else self.x

    def apply_inference(self, inference: "StateChange") -> None:
        # If we already knew that M was set, and we're currently
        # setting M, then we are not really changing its value.
        if (
            (inference.m is not None)
            and (self.m is not None)
            and (inference.m == self.m)
        ):
            self.m = None

        if (
            (inference.x is not None)
            and (self.x is not None)
            and (inference.x == self.x)
        ):
            self.x = None

    def simplify(self, state: State) -> "StateChange":
        change = copy(self)
        if (change.m is not None) and (state.m == change.m):
            change.m = None
        if (change.x is not None) and (state.x == change.x):
            change.x = None
        return change
