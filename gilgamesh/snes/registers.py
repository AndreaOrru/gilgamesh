from copy import copy
from typing import Dict, Optional

from gilgamesh.snes.state import State


class Register:
    def __init__(self, state: State, accumulator: bool):
        self.state = state
        self.accumulator = accumulator
        self.lo: Optional[int] = None
        self.hi: Optional[int] = None

    @property
    def size(self) -> int:
        return self.state.a_size if self.accumulator else self.state.x_size

    def copy(self, state: State) -> "Register":
        register = copy(self)
        register.state = state
        return register

    def get(self) -> Optional[int]:
        if self.size == 1:
            return self.lo
        else:
            if (self.lo is None) or (self.hi is None):
                return None
            return (self.hi << 8) | self.lo

    def set(self, value: Optional[int]) -> None:
        if value is None:
            if self.size == 1:
                self.lo = None
            else:
                self.lo = self.hi = None
        elif self.size == 1:
            self.lo = value & 0xFF
        else:
            self.lo = value & 0xFF
            self.hi = (value >> 8) & 0xFF

    def get_whole(self) -> Optional[int]:
        if (self.lo is None) or (self.hi is None):
            return None
        return (self.hi << 8) | self.lo

    def set_whole(self, value: Optional[int]) -> None:
        if value is None:
            self.lo = self.hi = None
        else:
            self.lo = value & 0xFF
            self.hi = (value >> 8) & 0xFF


class Registers:
    def __init__(self, state: State):
        self.state = state
        self.a = Register(state, True)
        self.x = Register(state, False)
        self.y = Register(state, False)

    def copy(self, state: State) -> "Registers":
        registers = copy(self)
        registers.state = state
        registers.a = registers.a.copy(state)
        registers.x = registers.x.copy(state)
        registers.y = registers.y.copy(state)
        return registers

    def snapshot(self) -> Dict[str, Optional[int]]:
        return {
            "a": self.a.get(),
            "x": self.x.get(),
            "y": self.y.get(),
        }
