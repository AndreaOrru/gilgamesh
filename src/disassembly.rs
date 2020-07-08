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

        for i in sub.instructions().values() {
            s.push_str(&self.label(i.pc(), subroutine));
            s.push_str(&self.instruction(*i));
            s.push_str(&self.asserted_state(*i, sub));
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

    pub fn instruction_raw(i: Option<Instruction>) -> String {
        match i {
            Some(i) => format!("{:4}{}", i.name().green(), i.argument_string()),
            None => "unknown".red().to_string(),
        }
    }

    fn label(&self, pc: usize, subroutine: usize) -> String {
        match self.analysis.label(pc, Some(subroutine)) {
            Some(label) => format!("{}:\n", label.red()),
            None => String::new(),
        }
    }

    fn asserted_state(&self, i: Instruction, sub: &Subroutine) -> String {
        let (state_change, typ) = match self.analysis.instruction_assertion(i.pc()) {
            Some(state_change) => (Some(state_change), "instruction"),
            None => match self.analysis.subroutine_assertion(sub.pc(), i.pc()) {
                Some(state_change) => (Some(state_change), "subroutine"),
                None => (None, ""),
            },
        };

        match state_change {
            Some(state_change) => {
                let mut s = Self::header("[ASSERTED STATE]", "magenta");

                s.push_str(&format!(
                    "  {} {}\n",
                    "; Assertion type:".bright_black(),
                    typ.magenta(),
                ));

                s.push_str(&format!(
                    "  {} {}\n",
                    "; Asserted state change:".bright_black(),
                    state_change.to_string().magenta()
                ));

                s.push_str(&Self::header("", "bright_black"));

                s
            }
            None => String::new(),
        }
    }

    fn unknown_state(&self, i: Instruction, subroutine: &Subroutine) -> String {
        match subroutine.unknown_state_changes().get(&i.pc()) {
            Some(state_change) => {
                let mut s = Self::header("[UNKNOWN STATE]", "red");

                let reason = to_sentence_case(state_change.unknown_reason().into());
                s.push_str(&format!(
                    "  {} {}\n",
                    "; Reason:".bright_black(),
                    reason.red()
                ));

                s.push_str(&format!(
                    "  {} {}\n",
                    "; Last known state change:".bright_black(),
                    i.state_change().to_string().green(),
                ));

                s.push_str(&Self::header("", "bright_black"));

                s
            }
            None => String::new(),
        }
    }
}
