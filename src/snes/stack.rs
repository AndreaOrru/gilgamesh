use std::collections::HashMap;

use derive_new::new;
use getset::CopyGetters;

use crate::snes::instruction::Instruction;
use crate::snes::state::{State, StateChange};

/// Optional payload (value pushed onto the stack).
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum Data {
    None,
    Value(usize),
    State(State, StateChange),
}

/// Stack entry.
#[derive(new, Copy, Clone, Debug, Eq, PartialEq)]
pub struct Entry {
    pub instruction: Option<Instruction>,
    pub data: Data,
}

/// SNES stack.
#[derive(CopyGetters, Clone)]
pub struct Stack {
    memory: HashMap<u16, Entry>,

    #[getset(get_copy = "pub")]
    pointer: u16,

    last_pointer_changer: Option<Instruction>,
}

impl Stack {
    /// Instantiate a new stack object.
    #[allow(clippy::new_without_default)]
    pub fn new() -> Self {
        Self {
            memory: HashMap::new(),
            pointer: 0x100,
            last_pointer_changer: None,
        }
    }

    /// Set a new stack pointer.
    pub fn set_pointer(&mut self, instruction: Instruction, pointer: u16) {
        self.last_pointer_changer = Some(instruction);
        self.pointer = pointer;
    }

    /// Push one or more values onto the stack.
    pub fn push(&mut self, instruction: Instruction, data: Data, size: usize) {
        for i in (0..size).rev() {
            let data = match data {
                Data::Value(b) => Data::Value((b >> (i * 8)) & 0xFF),
                _ => data,
            };

            self.memory
                .insert(self.pointer, Entry::new(Some(instruction), data));
            self.pointer -= 1;
        }
    }

    /// Push one value onto the stack.
    pub fn push_one(&mut self, instruction: Instruction, data: Data) {
        self.push(instruction, data, 1);
    }

    /// Pop one or more values from the stack.
    pub fn pop(&mut self, size: usize) -> Vec<Entry> {
        let mut v = Vec::new();
        for _ in 0..size {
            v.push(self.pop_one());
        }
        v
    }

    /// Pop one value from the stack.
    pub fn pop_one(&mut self) -> Entry {
        self.pointer += 1;
        match self.memory.get(&self.pointer) {
            Some(entry) => *entry,
            None => Entry::new(self.last_pointer_changer, Data::None),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_stack() -> Stack {
        let mut stack = Stack::new();
        let tcs = Instruction::test(0x8000, 0x8000, 0b0011_0000, 0x1B, 0x00);
        stack.set_pointer(tcs, 0x100);
        stack
    }

    #[test]
    fn test_push_pop_one() {
        let mut stack = setup_stack();

        let pha = Instruction::test(0x8001, 0x8000, 0b0011_0000, 0x48, 0x00);
        stack.push_one(pha, Data::Value(0xFF));
        assert_eq!(stack.pop_one().data, Data::Value(0xFF));
    }

    #[test]
    fn test_push_pop() {
        let mut stack = setup_stack();

        let pha = Instruction::test(0x8001, 0x8000, 0b0000_0000, 0x48, 0x00);
        stack.push(pha, Data::Value(0x1234), 2);

        let values: Vec<_> = stack.pop(2).iter().map(|e| e.data).collect();
        assert_eq!(values, vec![Data::Value(0x34), Data::Value(0x12)]);
    }
}
