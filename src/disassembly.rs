use std::iter::repeat;
use std::rc::Rc;

use colored::*;
use inflections::case::to_sentence_case;

use crate::analysis::Analysis;
use crate::snes::instruction::Instruction;
use crate::snes::subroutine::Subroutine;

const SEPARATOR_WIDTH: usize = 38;

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
            s.push_str(&self.unknown_state(*i, sub));
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

    fn header(title: &str, color: &str) -> String {
        let n = SEPARATOR_WIDTH;
        let left_n = (n / 2) - (title.len() / 2);
        let right_n = n - (left_n + title.len());

        let left: String = repeat("-").take(left_n).collect();
        let right: String = repeat("-").take(right_n).collect();

        format!(
            "  {}{}{}{}\n",
            ";".bright_black(),
            left.bright_black(),
            title.color(color),
            right.bright_black()
        )
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

    fn unknown_state(&self, i: Instruction, subroutine: &Subroutine) -> String {
        match subroutine.unknown_state_changes().get(&i.pc()) {
            Some(state_change) => {
                let mut s = Self::header("[UNKNOWN STATE]", "red");

                let reason = to_sentence_case(state_change.unknown_reason().into());
                s.push_str(
                    &format!("  ; Reason: {}\n", reason)
                        .bright_black()
                        .to_string(),
                );

                s.push_str(
                    &format!(
                        "  ; Last known state change: {}\n",
                        i.state_change().to_string().green()
                    )
                    .bright_black()
                    .to_string(),
                );

                s.push_str(&Self::header("", "bright_black"));

                s
            }
            None => String::new(),
        }
    }
}
