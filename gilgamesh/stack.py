from copy import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gilgamesh.instruction import Instruction


@dataclass
class StackEntry:
    instruction: Optional[Instruction] = None
    data: Any = None


class Stack:
    def __init__(self):
        self.memory: Dict[int, StackEntry] = {}
        self.pointer = 0

    def copy(self) -> "Stack":
        stack = copy(self)
        stack.memory = copy(self.memory)
        return stack

    def push(self, instruction: Instruction, data: Any = None, size=1) -> None:
        if size > 1:
            assert data is None
        for _ in range(size):
            self.memory[self.pointer] = StackEntry(instruction, data)
            self.pointer -= 1

    def pop_one(self) -> StackEntry:
        self.pointer += 1
        try:
            return self.memory[self.pointer]
        except KeyError:
            return StackEntry()

    def pop(self, size: int) -> List[StackEntry]:
        return [self.pop_one() for _ in range(size)]
