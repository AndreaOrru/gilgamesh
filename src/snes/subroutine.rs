use std::collections::{BTreeMap, HashMap, HashSet};

use getset::{CopyGetters, Getters, Setters};

use crate::snes::instruction::Instruction;
use crate::snes::opcodes::Op;
use crate::snes::state::{State, StateChange, UnknownReason};

/// Structure representing a subroutine.
#[derive(Debug, CopyGetters, Getters, Setters)]
pub struct Subroutine {
    #[getset(get_copy = "pub")]
    pc: usize,

    #[getset(get = "pub", set = "pub")]
    label: String,

    #[getset(get = "pub")]
    instructions: BTreeMap<usize, Instruction>,

    #[getset(get = "pub")]
    state_changes: HashMap<usize, StateChange>,

    #[getset(get = "pub")]
    unknown_state_changes: HashMap<usize, StateChange>,

    #[getset(get = "pub")]
    stack_traces: HashSet<Vec<usize>>,
}

impl Subroutine {
    /// Instantiate a new subroutine.
    pub fn new(pc: usize, label: String) -> Self {
        Self {
            pc,
            label,
            instructions: BTreeMap::new(),
            state_changes: HashMap::new(),
            unknown_state_changes: HashMap::new(),
            stack_traces: HashSet::new(),
        }
    }

    /// Add an instruction to the subroutine.
    pub fn add_instruction(&mut self, instruction: Instruction) {
        self.instructions.insert(instruction.pc(), instruction);
    }

    /// Add a state change to the subroutine.
    pub fn add_state_change(&mut self, pc: usize, state_change: StateChange) {
        if state_change.unknown() {
            self.unknown_state_changes.insert(pc, state_change);
        } else {
            self.state_changes.insert(pc, state_change);
        }
    }

    /// Add a stack trace to the subroutine.
    pub fn add_stack_trace(&mut self, stack_trace: Vec<usize>) {
        self.stack_traces.insert(stack_trace);
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

    /// Return a state change formed by combining all the possible state changes,
    /// if it's possible to do so without any contradictions.
    pub fn combined_state_change(&self) -> Option<StateChange> {
        if self.state_changes.is_empty() || self.unknown_state_changes.len() > 1 {
            return None;
        }

        let mut combined = StateChange::new_empty();
        for state_change in self.state_changes.values() {
            if let Some(m) = state_change.m() {
                match combined.m() {
                    Some(combined_m) if m != combined_m => return None,
                    _ => combined.set_m(m),
                }
            }
            if let Some(x) = state_change.x() {
                match combined.x() {
                    Some(combined_x) if x != combined_x => return None,
                    _ => combined.set_x(x),
                }
            }
        }
        Some(combined)
    }

    /// Return true if the subroutine saves the processor state at the beginning, false otherwise.
    pub fn saves_state_in_incipit(&self) -> bool {
        for i in self.instructions.values() {
            if i.operation() == Op::PHP {
                return true;
            } else if i.is_sep_rep() || i.is_control() {
                return false;
            }
        }
        false
    }

    /// Return true if the subroutine is responsible for the unknown state, false
    /// if the responsible subroutine is one of the ones it calls.
    pub fn is_responsible_for_unknown(&self) -> bool {
        self.has_unknown_state_change()
            && self
                .unknown_state_changes
                .values()
                .all(|s| s.unknown_reason() != UnknownReason::Unknown)
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
