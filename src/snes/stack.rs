use std::collections::HashMap;

use derive_new::new;

use crate::snes::instruction::Instruction;
use crate::snes::state::{StateRegister, SubStateChange};

/// Optional payload (value pushed onto the stack).
#[derive(Copy, Clone)]
pub enum Data {
    None,
    Byte(u8),
    State(StateRegister, SubStateChange),
}

/// Stack entry.
#[derive(new, Copy, Clone)]
pub struct Entry {
    pub instruction: Option<Instruction>,
    pub data: Data,
}

/// SNES stack.
#[derive(Clone)]
pub struct Stack {
    memory: HashMap<isize, Entry>,
    pointer: isize, // TODO: this should really be usize once TCS is implemented.
}

impl Stack {
    /// Instantiate a new stack object.
    #[allow(clippy::new_without_default)]
    pub fn new() -> Self {
        Self {
            memory: HashMap::new(),
            pointer: 0,
        }
    }

    /// Push one or more values onto the stack.
    pub fn push(&mut self, instruction: Instruction, data: Data, size: usize) {
        for i in (0..size).rev() {
            let data = match data {
                Data::Byte(b) => Data::Byte(b >> (i * 8)),
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
            None => {
                // TODO: return last instruction who changed the stack.
                Entry::new(None, Data::None)
            }
        }
    }
}
