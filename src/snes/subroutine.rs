use std::collections::BTreeSet;

use crate::snes::instruction::InstructionID;

pub struct Subroutine {
    pc: usize,
    instructions: BTreeSet<InstructionID>,
}

impl Subroutine {
    pub fn new(pc: usize) -> Self {
        Self {
            pc,
            instructions: BTreeSet::new(),
        }
    }

    pub fn add_instruction(&mut self, instruction: InstructionID) {
        self.instructions.insert(instruction);
    }
}
