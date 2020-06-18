use std::rc::Rc;

use colored::*;

use crate::analysis::Analysis;
use crate::snes::instruction::Instruction;
use crate::snes::subroutine::Subroutine;

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
            s.push_str(&self.unknown_state(i.pc(), sub));
        }
        s
    }

    fn comment(&self, pc: usize) -> String {
        let comments = self.analysis.comments().borrow();
        let comment = match comments.get(&pc) {
            Some(s) => s.to_owned(),
            None => String::new(),
        };
        format!("; ${:06X} | {}", pc, comment)
    }

    fn instruction(&self, i: Instruction) -> String {
        let arg = match i.argument_alias(self.analysis.clone()) {
            Some(arg) => arg.red(),
            None => i.argument_string().normal(),
        };

        let comment = self.comment(i.pc()).bright_black();
        format!("  {:4}{:25}{}\n", i.name().green(), arg, comment)
    }

    fn label(&self, pc: usize, subroutine: usize) -> String {
        match self.analysis.label(pc, Some(subroutine)) {
            Some(label) => format!("{}:\n", label.red()),
            None => String::new(),
        }
    }

    fn unknown_state(&self, pc: usize, subroutine: &Subroutine) -> String {
        match subroutine.unknown_state_changes().get(&pc) {
            Some(state_change) => {
                let reason = state_change.unknown_reason().to_string();
                format!("  ; {}\n", reason).red().to_string()
            }
            None => String::new(),
        }
    }
}
