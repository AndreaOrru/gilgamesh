use std::collections::{BTreeSet, HashMap, HashSet};

use getset::{CopyGetters, Getters};

use crate::snes::instruction::Instruction;
use crate::snes::state::{State, StateChange, UnknownReason};

/// Structure representing a subroutine.
#[derive(Debug, CopyGetters, Getters)]
pub struct Subroutine {
    #[getset(get_copy = "pub")]
    pc: usize,

    #[getset(get = "pub")]
    label: String,

    #[getset(get = "pub")]
    instructions: BTreeSet<Instruction>,

    #[getset(get = "pub")]
    state_changes: HashMap<usize, StateChange>,

    #[getset(get = "pub")]
    unknown_state_changes: HashMap<usize, StateChange>,
}

impl Subroutine {
    /// Instantiate a new subroutine.
    pub fn new(pc: usize, label: String) -> Self {
        Self {
            pc,
            label,
            instructions: BTreeSet::new(),
            state_changes: HashMap::new(),
            unknown_state_changes: HashMap::new(),
        }
    }

    /// Add an instruction to the subroutine.
    pub fn add_instruction(&mut self, instruction: Instruction) {
        self.instructions.insert(instruction);
    }

    /// Add a state change to the subroutine.
    pub fn add_state_change(&mut self, pc: usize, state_change: StateChange) {
        if state_change.unknown() {
            self.unknown_state_changes.insert(pc, state_change);
        } else {
            self.state_changes.insert(pc, state_change);
        }
    }

    /// Return true if the subroutine has an unknown state change, false otherwise.
    pub fn has_unknown_state_change(&self) -> bool {
        !self.unknown_state_changes.is_empty()
    }

    /// Return true if the subroutine is unknown because of `reason`, false otherwise.
    pub fn is_unknown_because_of(&self, reason: UnknownReason) -> bool {
        self.unknown_state_changes
            .values()
            .any(|s| s.unknown_reason() == reason)
    }

    /// Return the state changes, simplified given the current state.
    pub fn simplified_state_changes(&self, state: State) -> HashSet<StateChange> {
        let mut state_changes = HashSet::new();
        for state_change in self.state_changes.values() {
            state_changes.insert(state_change.simplify(state));
        }
        state_changes
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::snes::state::UnknownReason;

    #[test]
    fn test_add_state_change() {
        let mut subroutine = Subroutine::new(0x8000, "reset".to_string());

        subroutine.add_state_change(0x8000, StateChange::new_empty());
        assert!(!subroutine.has_unknown_state_change());

        subroutine.add_state_change(0x8000, StateChange::new_unknown(UnknownReason::Unknown));
        assert!(subroutine.has_unknown_state_change());
    }
}
