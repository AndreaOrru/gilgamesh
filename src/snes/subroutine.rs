use std::collections::BTreeSet;

use getset::{CopyGetters, Getters};

use crate::snes::instruction::Instruction;

#[derive(Debug, CopyGetters, Getters)]
pub struct Subroutine {
    #[getset(get_copy = "pub")]
    pc: usize,

    #[getset(get = "pub")]
    instructions: BTreeSet<Instruction>,
}

impl Subroutine {
    pub fn new(pc: usize) -> Self {
        Self {
            pc,
            instructions: BTreeSet::new(),
        }
    }

    pub fn add_instruction(&mut self, instruction: Instruction) {
        self.instructions.insert(instruction);
    }
}
