use std::collections::{BTreeSet, HashSet};

use getset::{CopyGetters, Getters};

use crate::snes::instruction::Instruction;
use crate::snes::state::SubStateChange;

/// Structure representing a subroutine.
#[derive(Debug, CopyGetters, Getters)]
pub struct Subroutine {
    #[getset(get_copy = "pub")]
    pc: usize,

    #[getset(get = "pub")]
    instructions: BTreeSet<Instruction>,

    #[getset(get = "pub")]
    state_changes: HashSet<SubStateChange>,

    #[getset(get_copy = "pub")]
    has_unknown_state_change: bool,
}

impl Subroutine {
    /// Instantiate a new subroutine.
    pub fn new(pc: usize) -> Self {
        Self {
            pc,
            instructions: BTreeSet::new(),
            state_changes: HashSet::new(),
            has_unknown_state_change: false,
        }
    }

    /// Add an instruction to the subroutine.
    pub fn add_instruction(&mut self, instruction: Instruction) {
        self.instructions.insert(instruction);
    }

    /// Add a state change to the subroutine.
    pub fn add_state_change(&mut self, state_change: SubStateChange) {
        self.state_changes.insert(state_change);
        if state_change.unknown() {
            self.has_unknown_state_change = true;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add_state_change() {
        let mut subroutine = Subroutine::new(0x8000);

        subroutine.add_state_change(SubStateChange::new_empty());
        assert!(!subroutine.has_unknown_state_change());

        subroutine.add_state_change(SubStateChange::new_unknown());
        assert!(subroutine.has_unknown_state_change());
    }
}
