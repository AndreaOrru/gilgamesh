from typing import Optional

M_BIT = 5
X_BIT = 4


class State:
    def __init__(self, p=0b0011_0000, m: Optional[int] = None, x: Optional[int] = None):
        if (m is None) and (x is None):
            self.p = p
        else:
            assert (m is not None) and (x is not None)
            self.p = m << M_BIT
            self.p |= x << X_BIT

    @property
    def m(self) -> int:
        return (self.p >> M_BIT) & 1

    @property
    def x(self) -> int:
        return (self.p >> X_BIT) & 1

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
