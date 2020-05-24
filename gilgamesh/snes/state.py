import re
from copy import copy
from enum import Enum, auto
from typing import Optional

from gilgamesh.errors import GilgameshError

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

    @classmethod
    def from_expr(cls, expr: str) -> "State":
        # TODO: Write tests for this.
        if not (
            re.match(r"m=(0|1),x=(0|1)", expr) or re.match(r"x=(0|1),m=(0|1)", expr)
        ):
            raise GilgameshError("Unknown syntax.")

        expressions = expr.split(",")
        return cls(
            **{
                str(register): int(value)
                for register, value in (e.split("=") for e in expressions)
            }
        )

    def __str__(self) -> str:
        return f"m={self.m},x={self.x}"

    def __repr__(self) -> str:
        return f"<State: {self}>"

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


class UnknownReason(Enum):
    KNOWN = auto()
    UNKNOWN = auto()
    RECURSION = auto()
    INDIRECT_JUMP = auto()
    STACK_MANIPULATION = auto()
    SUSPECT_INSTRUCTION = auto()
    MULTIPLE_RETURN_STATES = auto()


class StateChange:
    """Change in processor state caused by the execution of a subroutine."""

    def __init__(
        self,
        m: Optional[int] = None,
        x: Optional[int] = None,
        unknown_reason: Optional[UnknownReason] = None,
    ):
        self.m = m
        self.x = x
        self.unknown_reason = unknown_reason or UnknownReason.KNOWN
        self.asserted = False

    @property
    def unknown(self):
        return self.unknown_reason != UnknownReason.KNOWN

    @classmethod
    def from_expr(cls, expr: str) -> "StateChange":
        # TODO: Validate expression.
        if expr == "none":
            return cls()
        elif expr == "unknown":
            raise NotImplementedError

        expressions = expr.split(",")
        if 1 <= len(expressions) <= 2:
            return cls(
                **{  # type: ignore
                    str(register): int(value)
                    for register, value in (e.split("=") for e in expressions)
                }
            )
        else:
            raise GilgameshError("Unknown syntax.")

    def __str__(self) -> str:
        if self.unknown:
            return "unknown"

        r = ""
        m_str = [f"m={self.m}"] if self.m is not None else []
        x_str = [f"x={self.x}"] if self.x is not None else []
        if m_str or x_str:
            r += ",".join([*m_str, *x_str])
        else:
            r += "none"
        return r

    def __repr__(self) -> str:
        return f"<StateChange: {self}>"

    def __eq__(self, other) -> bool:
        return (self.unknown_reason == other.unknown_reason) or (
            (self.m == other.m) and (self.x == other.x)
        )

    def __hash__(self) -> int:
        if self.unknown:
            return hash((None, None, self.unknown_reason))
        return hash((self.m, self.x, self.unknown_reason))

    @property
    def unknown_reason_str(self) -> str:
        return self.unknown_reason.name.lower().replace("_", " ")

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
