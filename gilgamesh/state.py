M_BIT = 5
X_BIT = 4


class State:
    def __init__(self, m=0, x=0):
        self.p = 0b0000_0000
        self.p |= m << M_BIT
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
