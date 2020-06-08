use std::collections::BTreeSet;

use crate::snes::instruction::Instruction;

#[derive(Debug)]
pub struct Subroutine {
    pc: usize,
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
