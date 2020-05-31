from copy import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gilgamesh.snes.instruction import Instruction


@dataclass
class StackEntry:
    instruction: Optional[Instruction] = None
    data: Any = None


class Stack:
    def __init__(self):
        self.memory: Dict[int, StackEntry] = {}
        self.stack_change_instruction: Optional[Instruction] = None
        self.pointer = 0

    def copy(self) -> "Stack":
        stack = copy(self)
        stack.memory = copy(self.memory)
        return stack

    def set_pointer(
        self, instruction: Instruction, pointer: Optional[int] = None
    ) -> None:
        self.stack_change_instruction = instruction
        if pointer is not None:
            self.pointer = pointer

    def push(self, instruction: Instruction, data: Any = None, size=1) -> None:
        for i in range(size - 1, -1, -1):
            byte = (data >> i * 8) & 0xFF if isinstance(data, int) else data
            self.memory[self.pointer] = StackEntry(instruction, byte)
            self.pointer -= 1

    def pop_one(self) -> StackEntry:
        self.pointer += 1
        try:
            return self.memory[self.pointer]
        except KeyError:
            return StackEntry(self.stack_change_instruction)

    def pop(self, size: int) -> List[StackEntry]:
        return [self.pop_one() for _ in range(size)]

    def peek(self, size: int) -> List[StackEntry]:
        return [self.memory[self.pointer + i] for i in range(1, size + 1)]

    def match(self, value: int, size: int) -> bool:
        try:
            peek = self.peek(size)
        except KeyError:
            return False

        for i in range(size):
            if peek[i].data != (value >> (i * 8)) & 0xFF:
                return False
        return True
