use std::rc::Rc;

use colored::*;

use crate::analysis::Analysis;
use crate::snes::instruction::Instruction;

pub struct Disassembly {
    analysis: Rc<Analysis>,
}

impl Disassembly {
    pub fn new(analysis: Rc<Analysis>) -> Self {
        Self { analysis }
    }

    pub fn subroutine(&self, subroutine: usize) -> String {
        let subroutines = self.analysis.subroutines().borrow();
        let sub = &subroutines[&subroutine];
        let mut s = String::new();

        for i in sub.instructions().iter() {
            s.push_str(&self.label(i.pc(), subroutine));
            s.push_str(&self.instruction(*i));
        }

        s
    }

    fn label(&self, pc: usize, subroutine: usize) -> String {
        match self.analysis.label(pc, Some(subroutine)) {
            Some(label) => format!("{}:\n", label.red()),
            None => String::new(),
        }
    }

    fn instruction(&self, i: Instruction) -> String {
        let arg = match i.argument_alias(self.analysis.clone()) {
            Some(arg) => arg.red(),
            None => i.argument_string().normal(),
        };
        let comment = format!("; ${:06X}", i.pc()).bright_black();
        format!("  {:4}{:25}{}\n", i.name().green(), arg, comment)
    }
}