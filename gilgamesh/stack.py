from copy import copy
from dataclasses import dataclass
from typing import Any, List

from gilgamesh.instruction import Instruction


@dataclass
class StackEntry:
    instruction: Instruction
    data: Any = None


class Stack:
    def __init__(self):
        self.memory: List[StackEntry] = []

    def copy(self) -> "Stack":
        stack = copy(self)
        stack.memory = copy(self.memory)
        return stack

    def push(self, instruction: Instruction, data: Any = None, size=1) -> None:
        if size > 1:
            assert data is None
        for _ in range(size):
            self.memory.append(StackEntry(instruction, data))

    def pop_one(self) -> StackEntry:
        return self.memory.pop()

    def pop(self, size: int) -> List[StackEntry]:
        return [self.pop_one() for _ in range(size)]
