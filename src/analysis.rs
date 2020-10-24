use std::cell::RefCell;
use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::rc::Rc;

use bimap::BiHashMap;
use derive_new::new;
use getset::Getters;
use itertools::Itertools;
use regex::Regex;
use serde::{Deserialize, Serialize};

use crate::prompt::error::{Error, Result};
use crate::snes::cpu::CPU;
use crate::snes::instruction::{Instruction, InstructionType};
use crate::snes::opcodes::Op;
use crate::snes::rom::{ROMType, ROM};
use crate::snes::state::{State, StateChange, UnknownReason};
use crate::snes::subroutine::Subroutine;

/// ROM's entry point.
#[derive(new, Deserialize, Eq, Hash, PartialEq, Serialize)]
struct EntryPoint {
    label: String,
    pc: usize,
    p: u8,
}

/// Code reference.
#[derive(Debug, Eq, Hash, PartialEq)]
pub struct Reference {
    pub target: usize,
    pub subroutine: usize,
}

/// Jump table entry.
#[derive(new, Copy, Clone, Deserialize, Eq, Hash, PartialEq, Serialize)]
pub struct JumpTableEntry {
    pub x: Option<usize>,
    pub target: usize,
}
impl PartialOrd for JumpTableEntry {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for JumpTableEntry {
    fn cmp(&self, other: &Self) -> Ordering {
        self.x.cmp(&other.x)
    }
}

/// Suggested assertions.
#[derive(Debug)]
pub enum Assertion {
    Instruction(StateChange),
    Subroutine(StateChange),
}

/// Types of indirect jumps.
pub enum IndirectJump {
    Call,
    Jump,
    ReturnCall,
    ReturnJump,
}

/// Structure holding the state of the analysis.
#[derive(Deserialize, Getters, Serialize)]
pub struct Analysis {
    /// All analyzed instructions.
    #[serde(skip)]
    instructions: RefCell<HashMap<usize, HashSet<Instruction>>>,

    /// All analyzed subroutines.
    #[getset(get = "pub")]
    #[serde(skip)]
    subroutines: RefCell<BTreeMap<usize, Subroutine>>,

    /// Instructions referenced by other instructions.
    #[getset(get = "pub")]
    #[serde(skip)]
    references: RefCell<HashMap<usize, HashSet<Reference>>>,

    /// Instructions acting like indirect jumps.
    #[getset(get = "pub")]
    #[serde(skip)]
    indirect_jumps: RefCell<HashMap<usize, IndirectJump>>,

    /// Instructions that manipulate the stack in tricky ways.
    #[getset(get = "pub")]
    #[serde(skip)]
    stack_manipulations: RefCell<HashSet<usize>>,

    /// Subroutine labels.
    #[getset(get = "pub")]
    #[serde(skip)]
    subroutine_labels: RefCell<BiHashMap<String, usize>>,

    /// Subroutine local labels.
    #[getset(get = "pub")]
    #[serde(skip)]
    local_labels: RefCell<HashMap<usize, BiHashMap<String, usize>>>,

    /***************************************************************************/
    /// Reference to the ROM being analyzed.
    pub rom: ROM,

    /// ROM's entry points.
    entry_points: RefCell<HashSet<EntryPoint>>,

    /// Labels set by the user.
    custom_labels: RefCell<HashMap<usize, String>>,

    /// Assertions on instruction state changes.
    #[getset(get = "pub")]
    instruction_assertions: RefCell<HashMap<usize, StateChange>>,

    /// Assertions on subroutine state changes.
    #[getset(get = "pub")]
    subroutine_assertions: RefCell<HashMap<usize, HashMap<usize, StateChange>>>,

    /// Assertions on jump table targets.
    #[getset(get = "pub")]
    jump_assertions: RefCell<HashMap<usize, BTreeSet<JumpTableEntry>>>,

    /// Addresses that are targets for jump tables.
    #[getset(get = "pub")]
    jump_table_targets: RefCell<HashMap<usize, usize>>,

    /// Instruction comments.
    #[getset(get = "pub")]
    comments: RefCell<HashMap<usize, String>>,
}

impl Analysis {
    /// Instantiate a new Analysis object.
    pub fn new(rom: ROM) -> Rc<Self> {
        let entry_points = Self::default_entry_points(&rom);
        Rc::new(Self {
            rom,
            instructions: RefCell::new(HashMap::new()),
            subroutines: RefCell::new(BTreeMap::new()),
            references: RefCell::new(HashMap::new()),
            indirect_jumps: RefCell::new(HashMap::new()),
            stack_manipulations: RefCell::new(HashSet::new()),
            subroutine_labels: RefCell::new(BiHashMap::new()),
            local_labels: RefCell::new(HashMap::new()),
            /******************************************************************/
            entry_points: RefCell::new(entry_points),
            custom_labels: RefCell::new(HashMap::new()),
            instruction_assertions: RefCell::new(HashMap::new()),
            subroutine_assertions: RefCell::new(HashMap::new()),
            jump_assertions: RefCell::new(HashMap::new()),
            jump_table_targets: RefCell::new(HashMap::new()),
            comments: RefCell::new(HashMap::new()),
        })
    }

    /// Instantiate a new Analysis from a serialized JSON document.
    pub fn from_json(json: String) -> Result<Rc<Self>> {
        let mut analysis: Analysis = serde_json::from_str(&json).unwrap();
        analysis.rom.load(analysis.rom.path().to_owned())?;

        let analysis = Rc::new(analysis);
        analysis.run();
        Ok(analysis)
    }

    /// Return the analysis serialized as JSON.
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap()
    }

    /// Return the default entry points for the ROM under analysis.
    fn default_entry_points(rom: &ROM) -> HashSet<EntryPoint> {
        if rom.rom_type() == ROMType::Unknown {
            HashSet::new()
        } else {
            maplit::hashset! {
                EntryPoint { label: "reset".into(), pc: rom.reset_vector(), p: 0b0011_0000},
                EntryPoint { label: "nmi".into(),   pc: rom.nmi_vector(),   p: 0b0011_0000},
            }
        }
    }

    /// Reset the analysis (start from scratch).
    pub fn reset(self: &Rc<Self>) {
        // Clear serializable attributes.
        *self.entry_points.borrow_mut() = Self::default_entry_points(&self.rom);
        self.custom_labels.borrow_mut().clear();
        self.instruction_assertions.borrow_mut().clear();
        self.subroutine_assertions.borrow_mut().clear();
        self.jump_assertions.borrow_mut().clear();
        self.jump_table_targets.borrow_mut().clear();
        self.comments.borrow_mut().clear();
        // Clear everything else.
        self.clear();
    }

    /// Clear the results of the analysis.
    fn clear(&self) {
        // Clear non-serializable attributes.
        self.instructions.borrow_mut().clear();
        self.subroutines.borrow_mut().clear();
        self.references.borrow_mut().clear();
        self.indirect_jumps.borrow_mut().clear();
        self.stack_manipulations.borrow_mut().clear();
        self.subroutine_labels.borrow_mut().clear();
        self.local_labels.borrow_mut().clear();
    }

    /// Analyze the ROM.
    pub fn run(self: &Rc<Self>) {
        self.clear();

        for EntryPoint { label, pc, p } in self.entry_points.borrow().iter() {
            self.add_subroutine(*pc, Some(label.clone()), Vec::new());
            let mut cpu = CPU::new(self, *pc, *pc, *p);
            cpu.run();
        }

        self.generate_local_labels();
        self.generate_asserted_subroutines();
    }

    /// Analyze and apply suggested assertions as far as possible.
    pub fn auto_run(self: &Rc<Self>) {
        let mut applied_suggestion = true;

        // Continue until we don't have any more assertions to apply.
        while applied_suggestion {
            self.run();

            // Gather unknown subroutines.
            let subroutines = self.subroutines.borrow();
            let unknown_subs = subroutines
                .values()
                .filter(|s| s.is_responsible_for_unknown());

            applied_suggestion = false;
            for sub in unknown_subs {
                // Get unknown states (ordered by priority).
                let changes = sub.unknown_state_changes().iter().sorted_by_key(|t| t.1);

                for (instr_pc, _) in changes {
                    let instr = match sub.instructions().get(instr_pc) {
                        Some(instr) => *instr,
                        None => continue, // Code in RAM.
                    };
                    let assertions = self.suggest_assertions(instr, sub);

                    // Apply suggested assertions.
                    for assertion in assertions.iter() {
                        match assertion {
                            Assertion::Instruction(s) => {
                                self.add_instruction_assertion(*instr_pc, *s)
                            }
                            Assertion::Subroutine(s) => {
                                self.add_subroutine_assertion(sub.pc(), *instr_pc, *s)
                            }
                        }
                        applied_suggestion = true;
                    }
                }
            }
            drop(subroutines);
        }
    }

    /// Return true if the instruction has already been analyzed, false otherwise.
    pub fn is_visited(&self, instruction: Instruction) -> bool {
        let instructions = self.instructions.borrow();
        match instructions.get(&instruction.pc()) {
            Some(instr_set) => instr_set.contains(&instruction),
            None => false,
        }
    }

    /// Return true if an instruction with the same address
    /// has already been analyzed, false otherwise.
    pub fn is_visited_pc(&self, pc: usize) -> bool {
        self.instructions.borrow().contains_key(&pc)
    }

    /// Return true if a subroutine at the given PC is an entry point.
    pub fn is_entry_point(&self, pc: usize) -> bool {
        let entry_points = self.entry_points.borrow();
        entry_points.iter().any(|ep| ep.pc == pc)
    }

    /// Find the instruction that contains the given address, if any.
    pub fn find_instruction(&self, address: usize) -> Option<usize> {
        let size = |pc| self.any_instruction(pc).unwrap().size();
        if self.is_visited_pc(address) {
            Some(address)
        } else if self.is_visited_pc(address - 1) && size(address - 1) >= 2 {
            Some(address - 1)
        } else if self.is_visited_pc(address - 2) && size(address - 2) >= 3 {
            Some(address - 2)
        } else if self.is_visited_pc(address - 3) && size(address - 3) >= 4 {
            Some(address - 3)
        } else {
            None
        }
    }

    /// Return true if the given subroutine is part of the analysis, false otherwise.
    pub fn is_subroutine(&self, pc: usize) -> bool {
        self.subroutines.borrow().contains_key(&pc)
    }

    /// Return true if the given address is the target of a jump table, false otherwise.
    pub fn is_jump_table_target(&self, pc: usize) -> bool {
        self.jump_table_targets.borrow().contains_key(&pc)
    }

    /// Add an instruction to the analysis.
    pub fn add_instruction(&self, instruction: Instruction) -> Instruction {
        let mut instructions = self.instructions.borrow_mut();
        instructions
            .entry(instruction.pc())
            .or_default()
            .insert(instruction);

        let mut subroutines = self.subroutines.borrow_mut();
        let subroutine = subroutines.get_mut(&instruction.subroutine()).unwrap();
        subroutine.add_instruction(instruction);

        instruction
    }

    /// Add a subroutine to the analysis.
    pub fn add_subroutine(&self, pc: usize, label: Option<String>, stack_trace: Vec<usize>) {
        // Register subroutine's label or fetch saved one.
        let mut custom_labels = self.custom_labels.borrow_mut();
        let label = match custom_labels.get(&pc) {
            Some(l) => l.to_owned(),
            None => match label {
                Some(l) => {
                    custom_labels.insert(pc, l.to_owned());
                    l
                }
                None => format!("sub_{:06X}", pc),
            },
        };
        self.subroutine_labels
            .borrow_mut()
            .insert(label.to_owned(), pc);

        // Create and register subroutine (unless it already exists).
        let mut subroutines = self.subroutines.borrow_mut();
        let subroutine = subroutines
            .entry(pc)
            .or_insert_with(|| Subroutine::new(pc, label.to_owned()));

        // Add stack trace to the subroutine.
        subroutine.add_stack_trace(stack_trace);
    }

    /// Add a state change to a subroutine.
    pub fn add_state_change(&self, subroutine: usize, pc: usize, state_change: StateChange) {
        let mut subroutines = self.subroutines.borrow_mut();
        let sub = subroutines.get_mut(&subroutine).unwrap();
        sub.add_state_change(pc, state_change);
    }

    /// Add a reference from an instruction to another.
    pub fn add_reference(&self, source: usize, target: usize, subroutine: usize) {
        let mut references = self.references.borrow_mut();
        references
            .entry(source)
            .or_default()
            .insert(Reference { target, subroutine });
    }

    /// Add an assertion on an instruction state change.
    pub fn add_instruction_assertion(&self, pc: usize, state_change: StateChange) {
        let mut assertions = self.instruction_assertions.borrow_mut();
        assertions.insert(pc, state_change);
    }

    /// Add an assertion on a subroutine state change.
    pub fn add_subroutine_assertion(&self, sub_pc: usize, pc: usize, state_change: StateChange) {
        let mut assertions = self.subroutine_assertions.borrow_mut();
        assertions
            .entry(sub_pc)
            .or_default()
            .insert(pc, state_change);
    }

    /// Add a jump assertion: caller jumps to target when X = n (if relevant).
    pub fn add_jump_assertion(&self, caller_pc: usize, target_pc: Option<usize>, x: Option<usize>) {
        let mut assertions = self.jump_assertions.borrow_mut();
        let mut targets = self.jump_table_targets.borrow_mut();
        let entries = assertions.entry(caller_pc).or_default();
        if let Some(target) = target_pc {
            entries.insert(JumpTableEntry::new(x, target));
            *targets.entry(target).or_default() += 1;
        }
    }

    /// Add a jumptable assertion: caller spans a jumptable that goes from x to y (included).
    pub fn add_jumptable_assertion(&self, caller_pc: usize, range: (usize, usize)) {
        let caller = self.any_instruction(caller_pc).unwrap();
        for x in ((range.0)..=(range.1)).step_by(2) {
            let offset = caller.argument().unwrap() + x;
            let bank = caller.pc() & 0xFF0000;
            let target_pc = bank | (self.rom.read_word(bank | offset)) as usize;
            self.add_jump_assertion(caller_pc, Some(target_pc), Some(x));
        }
    }

    /// Add an entry point to the analysis.
    pub fn add_entry_point(&self, pc: usize, name: String, state: State) -> Result<()> {
        if self.is_entry_point(pc) || self.is_visited_pc(pc) {
            return Err(Error::AlreadyAnalyzed);
        }
        let mut entry_points = self.entry_points.borrow_mut();
        entry_points.insert(EntryPoint::new(name, pc, state.p()));
        Ok(())
    }

    /// Add a stack manipulating instruction to the analysis.
    pub fn add_stack_manipulation(&self, pc: usize) {
        let mut stack_manipulations = self.stack_manipulations.borrow_mut();
        stack_manipulations.insert(pc);
    }

    /// Add an indirect jump instruction to the analysis.
    pub fn add_indirect_jump(&self, sub_pc: usize, pc: usize, kind: IndirectJump) {
        let mut indirect_jumps = self.indirect_jumps.borrow_mut();
        indirect_jumps.insert(pc, kind);

        let mut subroutines = self.subroutines.borrow_mut();
        let subroutine = subroutines.get_mut(&sub_pc).unwrap();
        subroutine.set_contains_indirect_jumps(true);
    }

    /// Remove an assertion on an instruction state change.
    pub fn del_instruction_assertion(&self, pc: usize) {
        let mut assertions = self.instruction_assertions.borrow_mut();
        assertions.remove(&pc);
    }

    /// Remove an assertion on a subroutine state change.
    pub fn del_subroutine_assertion(&self, subroutine: usize, pc: usize) {
        let mut assertions = self.subroutine_assertions.borrow_mut();
        let sub_assertions = assertions.get_mut(&subroutine);
        if let Some(h) = sub_assertions {
            h.remove(&pc);
            if h.is_empty() {
                assertions.remove(&subroutine);
            }
        };
    }

    /// Remove a jump assertion. If no target is specified, removes all the targets.
    pub fn del_jump_assertion(&self, caller_pc: usize, target_pc: Option<usize>) {
        let mut assertions = self.jump_assertions.borrow_mut();
        let mut jt_targets = self.jump_table_targets.borrow_mut();

        // Decrement target count by diff.
        let mut decr_target_count = |target, diff: usize| {
            let jt_target = jt_targets.get_mut(&target).unwrap();
            *jt_target -= diff;
            if *jt_target == 0 {
                jt_targets.remove(&target);
            }
        };

        match target_pc {
            Some(target) => {
                // Remove all entries that match target_pc.
                let orig_set = assertions.get(&caller_pc).unwrap();
                let new_set: BTreeSet<_> = orig_set
                    .iter()
                    .copied()
                    .filter(|jt| jt.target != target)
                    .collect();
                let diff = orig_set.len() - new_set.len();

                // Store the new entry set.
                if new_set.is_empty() {
                    assertions.remove(&caller_pc);
                } else {
                    assertions.insert(caller_pc, new_set);
                }

                // Update the jump table targets.
                decr_target_count(target, diff);
            }
            None => {
                // Remove all entries.
                let entries = assertions.get(&caller_pc).unwrap();
                for entry in entries.iter() {
                    decr_target_count(entry.target, 1);
                }
                assertions.remove(&caller_pc);
            }
        }
    }

    /// Remove a jumptable assertion (in the specified range).
    pub fn del_jumptable_assertion(&self, caller_pc: usize, range: (usize, usize)) {
        let assertions = self.jump_assertions.borrow();
        let entries = assertions.get(&caller_pc).unwrap();
        let filtered_entries = entries.iter().filter(|e| match e.x {
            Some(x) => (x >= range.0) && (x <= range.1),
            None => false,
        });
        let targets: HashSet<_> = filtered_entries.map(|e| e.target).collect();

        drop(assertions);
        for target in targets {
            self.del_jump_assertion(caller_pc, Some(target));
        }
    }

    /// Return a list of suggested assertions to be applied against the given instruction.
    pub fn suggest_assertions(&self, i: Instruction, sub: &Subroutine) -> Vec<Assertion> {
        let mut assertions = Vec::new();
        let indirect_jumps = self.indirect_jumps.borrow();

        let mut assert_combined_state = || match sub.combined_state_change() {
            Some(combined_state) => assertions.push(Assertion::Subroutine(combined_state)),
            None if sub.saves_state_in_incipit() => {
                assertions.push(Assertion::Subroutine(StateChange::new_empty()))
            }
            _ => {
                // TODO: this should only run when the unsafe flag is set.
                assertions.push(Assertion::Subroutine(i.state_change()));
            }
        };

        // No suggested assertions if some assertions were already declared.
        if self.instruction_assertion(i.pc()).is_some()
            || self.subroutine_assertion(sub.pc(), i.pc()).is_some()
        {
            return assertions;
        }

        // If the state change for this instruction is known, no assertion is necessary.
        let reason = match sub.unknown_state_changes().get(&i.pc()) {
            Some(state_change) => state_change.unknown_reason(),
            None => return assertions,
        };

        match i.typ() {
            // Indirect JSR/JSL typically don't rely on a specific state being set.
            InstructionType::Call => match reason {
                UnknownReason::IndirectJump => {
                    assertions.push(Assertion::Instruction(StateChange::new_empty()))
                }
                // TODO: this should only run when the unsafe flag is set.
                UnknownReason::MultipleReturnStates => {
                    assertions.push(Assertion::Instruction(StateChange::new_empty()))
                }
                _ => {}
            },

            // Indirect JMP/JML.
            InstructionType::Jump if reason == UnknownReason::IndirectJump => {
                if sub.saves_state_in_incipit() {
                    // Typically, if there's a PHP in the incipit, the state will
                    // be restored before returning, so we assume the subroutine
                    // does not change the state.
                    assertions.push(Assertion::Subroutine(StateChange::new_empty()));
                } else {
                    // Otherwise, we will use our knowledge of other
                    // return states to inform the decision.
                    assert_combined_state();
                }
            }

            // RTS/RTL to manipulated address.
            InstructionType::Return => match reason {
                UnknownReason::StackManipulation => assert_combined_state(),
                UnknownReason::IndirectJump => match indirect_jumps[&i.pc()] {
                    IndirectJump::ReturnCall => {
                        assertions.push(Assertion::Instruction(StateChange::new_empty()))
                    }
                    // TODO: find concrete cases for this.
                    IndirectJump::ReturnJump => {}
                    _ => {}
                },
                _ => {}
            },

            // PLP from manipulated stack.
            _ if i.operation() == Op::PLP && reason == UnknownReason::StackManipulation => {
                assertions.push(Assertion::Instruction(StateChange::new_empty()));
            }

            // Recursive functions.
            _ if reason == UnknownReason::Recursion => assert_combined_state(),

            _ => {}
        };

        assertions
    }

    /// Get a state change assertion for an instruction, if any.
    pub fn instruction_assertion(&self, pc: usize) -> Option<StateChange> {
        let assertions = self.instruction_assertions.borrow();
        assertions.get(&pc).copied()
    }

    /// Get a state change assertion for a subroutine, if any.
    pub fn subroutine_assertion(&self, subroutine: usize, pc: usize) -> Option<StateChange> {
        let assertions = self.subroutine_assertions.borrow();
        match assertions.get(&subroutine) {
            Some(h) => h.get(&pc).copied(),
            None => None,
        }
    }

    /// Return the label associated with an address, if any.
    pub fn label(&self, pc: usize, subroutine: Option<usize>) -> Option<String> {
        let sub_labels = self.subroutine_labels.borrow();
        let local_labels = self.local_labels.borrow();

        // Try and get the label of a subroutine first.
        match sub_labels.get_by_right(&pc) {
            // If there's a subroutine label, return it.
            Some(label) => Some(label.clone()),

            // Retrieve the local labels internal to the given subroutine.
            None if subroutine.is_some() => match local_labels.get(&subroutine.unwrap()) {
                // Return the local label, if it exists.
                Some(labels) => match labels.get_by_right(&pc) {
                    Some(label) => Some(format!(".{}", label)),
                    None => None,
                },
                // There is no local label at the given address.
                None => None,
            },

            // No subroutine was provided.
            _ => None,
        }
    }

    /// Return the value associated with a label, if any.
    pub fn label_value(&self, label: String) -> Option<usize> {
        let labels = self.subroutine_labels.borrow();
        match labels.get_by_left(&label) {
            Some(&pc) => Some(pc),
            None => None,
        }
    }

    /// Rename a subroutine or local label. If renaming a local label,
    /// the subroutine it belongs to is required as a parameter.
    pub fn rename_label(&self, old: String, new: String, subroutine: Option<usize>) -> Result<()> {
        if old.starts_with('.') {
            self.rename_local_label(old, new, subroutine.ok_or(Error::NoSelectedSubroutine)?)
        } else {
            self.rename_subroutine(old, new)
        }
    }

    /// Rename a local label.
    fn rename_local_label(&self, _old: String, _new: String, subroutine: usize) -> Result<()> {
        if !_new.starts_with('.') {
            return Err(Error::InvalidLabelType);
        }
        let (old, new) = (_old[1..].to_string(), _new[1..].to_string());

        let mut local_labels = self.local_labels.borrow_mut();
        let labels = local_labels.get_mut(&subroutine).unwrap();
        let pc = *labels.get_by_left(&old).ok_or(Error::UnknownLabel(_old))?;

        self.validate_label(&labels, new.to_owned())?;
        labels.remove_by_left(&old);
        labels.insert(new.to_owned(), pc);

        self.custom_labels.borrow_mut().insert(pc, new);
        Ok(())
    }

    /// Rename a subroutine.
    fn rename_subroutine(&self, old: String, new: String) -> Result<()> {
        if new.starts_with('.') {
            return Err(Error::InvalidLabelType);
        }
        let mut subroutines = self.subroutines.borrow_mut();
        let mut labels = self.subroutine_labels.borrow_mut();

        let pc = *labels
            .get_by_left(&old)
            .ok_or_else(|| Error::UnknownLabel(old.to_owned()))?;
        let subroutine = subroutines.get_mut(&pc).unwrap();

        self.validate_label(&labels, new.to_owned())?;
        labels.remove_by_left(&old);
        labels.insert(new.to_owned(), pc);
        subroutine.set_label(new.to_owned());

        self.custom_labels.borrow_mut().insert(pc, new);
        Ok(())
    }

    /// Check that the given label is a valid label for a subroutine or local label.
    fn validate_label(&self, labels: &BiHashMap<String, usize>, label: String) -> Result<()> {
        if labels.contains_left(&label) {
            return Err(Error::LabelAlreadyUsed(label));
        }

        let ident = Regex::new(r"^[_A-Za-z][_A-Za-z0-9]*$").unwrap();
        if !ident.is_match(&label) {
            return Err(Error::InvalidLabel(label));
        }

        if label.starts_with("sub_") || label.starts_with("loc_") {
            return Err(Error::ReservedLabel(label));
        }

        Ok(())
    }

    /// Return all the subroutines that contain the given instruction.
    pub fn instruction_subroutines(&self, pc: usize) -> HashSet<usize> {
        match self.instructions.borrow().get(&pc) {
            Some(instructions) => instructions.iter().map(|i| i.subroutine()).collect(),
            None => HashSet::new(),
        }
    }

    /// Return list of subroutine labels containing the given instruction.
    pub fn instruction_subroutine_labels(&self, instr_pc: usize) -> Vec<String> {
        let subroutines = self.instruction_subroutines(instr_pc);
        let labels: Vec<_> = subroutines
            .iter()
            .map(|pc| self.label(*pc, None).unwrap())
            .collect();
        labels
    }

    /// Return any of the instructions at address PC.
    pub fn any_instruction(&self, pc: usize) -> Option<Instruction> {
        let instructions = self.instructions.borrow();
        instructions
            .get(&pc)
            .map(|h| h.iter().next().unwrap())
            .copied()
    }

    /// Generate local label names.
    fn generate_local_labels(&self) {
        let custom_labels = self.custom_labels.borrow();
        let mut local_labels = self.local_labels.borrow_mut();

        for references in self.references.borrow().values() {
            for Reference { target, subroutine } in references {
                if !self.is_subroutine(*target) {
                    // Get custom label or assigned default one.
                    let label = custom_labels
                        .get(&target)
                        .cloned()
                        .unwrap_or_else(|| format!("loc_{:06X}", *target));

                    local_labels
                        .entry(*subroutine)
                        .or_default()
                        .insert(label.to_owned(), *target);
                }
            }
        }
    }

    /// Generate the list of subroutines containing assertions.
    fn generate_asserted_subroutines(&self) {
        for instr_pc in self.instruction_assertions.borrow().keys() {
            self.flag_asserted_subroutines(*instr_pc);
        }
        for sub_pc in self.subroutine_assertions.borrow().keys() {
            self.flag_asserted_subroutine(*sub_pc);
        }
        for caller_pc in self.jump_assertions.borrow().keys() {
            self.flag_asserted_subroutines(*caller_pc);
        }
    }

    /// Flag a given subroutine as containing an assertion.
    fn flag_asserted_subroutine(&self, sub_pc: usize) {
        let mut subroutines = self.subroutines.borrow_mut();
        let subroutine = subroutines.get_mut(&sub_pc).unwrap();
        subroutine.set_contains_assertions(true);
    }

    /// Flag all the subroutines associated with the given instruction as asserted.
    fn flag_asserted_subroutines(&self, instr_pc: usize) {
        let mut subroutines = self.subroutines.borrow_mut();
        for sub_pc in self.instruction_subroutines(instr_pc) {
            let subroutine = subroutines.get_mut(&sub_pc).unwrap();
            subroutine.set_contains_assertions(true);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::snes::opcodes::Op;
    use crate::snes::state::UnknownReason;
    use crate::test_rom;

    #[test]
    fn test_instruction_subroutine_references() {
        let analysis = Analysis::new(ROM::new());

        analysis.add_subroutine(0x8000, None, Vec::new());
        assert!(analysis.is_subroutine(0x8000));

        let nop = Instruction::test(0x8000, 0x8000, 0b0011_0000, 0xEA, 0x00);
        analysis.add_instruction(nop);
        assert!(analysis.is_visited_pc(0x8000));
    }

    /***************************************************************************/

    test_rom!(setup_elidable_state_change, "elidable_state_change.asm");
    #[test]
    fn test_elidable_state_change() {
        let analysis = Analysis::new(setup_elidable_state_change());
        analysis.run();

        // Test there are two subroutines (+ NMI).
        let subroutines = analysis.subroutines.borrow();
        assert_eq!(subroutines.len(), 3);

        // Test there's a `reset` sub with the correct number of instructions.
        let reset_sub = &subroutines[&0x8000];
        assert_eq!(reset_sub.label(), "reset");
        assert_eq!(reset_sub.instructions().len(), 4);

        // Test there's a sub with the correct number of instructions.
        let elidable_change_sub = &subroutines[&0x800A];
        assert_eq!(elidable_change_sub.instructions().len(), 6);

        // Test that the state is preserved.
        let state_changes = elidable_change_sub.state_changes();
        assert_eq!(state_changes.len(), 1);
        let state_change = state_changes.values().next().unwrap();
        assert_eq!(state_change.to_string(), "none");
    }

    test_rom!(setup_infinite_loop, "infinite_loop.asm");
    #[test]
    fn test_infinite_loop() {
        let analysis = Analysis::new(setup_infinite_loop());
        analysis.run();

        // Check there is a single subroutine with one instruction.
        let subroutines = analysis.subroutines.borrow();
        assert_eq!(subroutines.len() - 1, 1);
        assert_eq!(subroutines[&0x8000].pc(), 0x8000);
        assert_eq!(subroutines[&0x8000].instructions().len(), 1);

        // Check there is a single instruction.
        let instructions = analysis.instructions.borrow();
        assert_eq!(instructions.len(), 1);
        assert_eq!(instructions[&0x8000].len(), 1);

        // Check the instruction is a jump.
        let jmp = instructions[&0x8000].iter().next().unwrap();
        assert_eq!(jmp.pc(), 0x8000);
        assert_eq!(jmp.subroutine(), 0x8000);
        assert_eq!(jmp.operation(), Op::JMP);

        // Check the instruction points to itself.
        let references = analysis.references.borrow();
        assert_eq!(references.len(), 1);
        assert!(references[&0x8000].contains(&Reference {
            target: 0x8000,
            subroutine: 0x8000
        }));
    }

    test_rom!(setup_jump_tables, "jump_tables.asm");
    #[test]
    fn test_jump_tables() {
        let analysis = Analysis::new(setup_jump_tables());
        analysis.run();

        // Test that there's a single subroutine, which is unknown
        // because of an unexplored indirect jump instruction.
        {
            let subroutines = analysis.subroutines.borrow();
            let reset_sub = &subroutines[&0x8000];
            assert_eq!(reset_sub.label(), "reset");
            assert_eq!(reset_sub.instructions().len(), 1);
            assert!(reset_sub.is_unknown_because_of(UnknownReason::IndirectJump));
        }

        // Specify the limits of the jumptable.
        analysis.add_jumptable_assertion(0x8000, (0, 2));
        analysis.run();

        // Verify that the subroutines that contains the jumptable
        // has been flagged as containing assertions.
        let reset_sub = analysis.subroutines.borrow()[&0x8000];
        assert!(reset_sub.contains_assertions());

        // Verify that the subroutines pointed by
        // the jumptable have been explored.
        {
            let subroutines = analysis.subroutines.borrow();
            assert_eq!(subroutines.len() - 1, 3);
            assert!(analysis.is_subroutine(0x8100));
            assert!(analysis.is_subroutine(0x8200));
            assert!(analysis.is_jump_table_target(0x8100));
            assert!(analysis.is_jump_table_target(0x8200));
        }

        // Verify that, after deleting the assertions, the targets
        // are not considered to be part of a jump table anymore.
        analysis.del_jumptable_assertion(0x8000, (0, 0));
        assert!(!analysis.is_jump_table_target(0x8100));

        analysis.del_jump_assertion(0x8000, None);
        assert!(!analysis.is_jump_table_target(0x8200));
    }

    test_rom!(setup_php_plp, "php_plp.asm");
    #[test]
    fn test_php_plp() {
        let analysis = Analysis::new(setup_php_plp());
        analysis.run();

        // Test there are two subroutines (+ NMI).
        let subroutines = analysis.subroutines.borrow();
        assert_eq!(subroutines.len() - 1, 2);

        // Test there's a `reset` sub with the correct number of instructions.
        let reset_sub = &subroutines[&0x8000];
        assert_eq!(reset_sub.label(), "reset");
        assert_eq!(reset_sub.instructions().len(), 4);
        assert!(!reset_sub.saves_state_in_incipit());

        // Test there's a PHP/PLP sub with the correct number of instructions.
        let php_plp_sub = &subroutines[&0x800A];
        assert_eq!(php_plp_sub.instructions().len(), 5);
        assert!(php_plp_sub.saves_state_in_incipit());

        // Test that the state is preserved.
        let state_changes = php_plp_sub.state_changes();
        assert_eq!(state_changes.len(), 1);
        let state_change = state_changes.values().next().unwrap();
        assert_eq!(state_change.to_string(), "none");

        drop(subroutines);

        // Test that renaming subroutine label works (even after analysis).
        analysis
            .rename_label("reset".to_string(), "new_reset".to_string(), None)
            .ok();
        analysis.run();
        assert_eq!(
            analysis.label(0x8000, None).unwrap(),
            "new_reset".to_string()
        );

        // Test that renaming local labels works.
        analysis
            .rename_label(".loc_008007".to_string(), ".loop".to_string(), Some(0x8000))
            .ok();
        analysis.run();
        assert_eq!(
            analysis.label(0x8007, Some(0x8000)).unwrap(),
            ".loop".to_string()
        );
    }

    test_rom!(
        setup_simplified_state_changes,
        "simplified_state_changes.asm"
    );
    #[test]
    fn test_simplified_state_changes() {
        let analysis = Analysis::new(setup_simplified_state_changes());
        analysis.run();

        // Test there are two subroutines (+ NMI).
        let subroutines = analysis.subroutines.borrow();
        assert_eq!(subroutines.len() - 1, 2);

        // Test there's a `reset` sub with the correct number of instructions.
        let reset_sub = &subroutines[&0x8000];
        assert_eq!(reset_sub.label(), "reset");
        assert_eq!(reset_sub.instructions().len(), 5);

        // Test there's a `double_state_change` with the correct number of instructions.
        let double_state_sub = &subroutines[&0x800E];
        assert_eq!(double_state_sub.instructions().len(), 5);

        // Test that the state is simplified.
        let state_changes = double_state_sub.state_changes();
        assert_eq!(state_changes.len(), 2);
        assert!(!reset_sub.has_unknown_state_change());
    }

    test_rom!(setup_state_change, "state_change.asm");
    #[test]
    fn test_state_change() {
        let analysis = Analysis::new(setup_state_change());
        analysis.run();

        // Check there are two subroutines (+ NMI).
        let subroutines = analysis.subroutines.borrow();
        assert_eq!(subroutines.len() - 1, 2);

        // Check the subroutines have the right name and number of instructions.
        let reset_sub = &subroutines[&0x8000];
        assert_eq!(reset_sub.label(), "reset");
        assert_eq!(reset_sub.instructions().len(), 5);
        let state_change_sub = &subroutines[&0x800E];
        assert_eq!(state_change_sub.label(), "sub_00800E");
        assert_eq!(state_change_sub.instructions().len(), 2);

        // Check the `state_change` subroutine sets M/X to 0.
        let state_change = state_change_sub.state_changes().values().next().unwrap();
        assert_eq!(state_change_sub.state_changes().len(), 1);
        assert_eq!(state_change.m().unwrap(), false);
        assert_eq!(state_change.x().unwrap(), false);

        // Check LDA and LDX have the right operand size.
        let instructions = analysis.instructions.borrow();
        let lda = instructions[&0x8005].iter().next().unwrap();
        assert_eq!(lda.operation(), Op::LDA);
        assert_eq!(lda.argument().unwrap(), 0x1234);
        let ldx = instructions[&0x8008].iter().next().unwrap();
        assert_eq!(ldx.operation(), Op::LDX);
        assert_eq!(ldx.argument().unwrap(), 0x1234);
    }

    test_rom!(setup_unknown_call_jump, "unknown_call_jump.asm");
    #[test]
    fn test_unknown_call_jump() {
        let analysis = Analysis::new(setup_unknown_call_jump());
        analysis.run();

        {
            let subroutines = analysis.subroutines.borrow();
            assert_eq!(subroutines.len(), 2);

            let reset_sub = &subroutines[&0x8000];
            assert_eq!(reset_sub.label(), "reset");
            assert_eq!(reset_sub.instructions().len(), 1);
            let nmi_sub = &subroutines[&0x8003];
            assert_eq!(nmi_sub.label(), "nmi");
            assert_eq!(nmi_sub.instructions().len(), 2);

            assert!(reset_sub.has_unknown_state_change());
            assert!(nmi_sub.has_unknown_state_change());
        }

        // Test adding a custom entry point.
        analysis
            .add_entry_point(0x9002, "loop".to_string(), State::from_mx(true, true))
            .unwrap();
        analysis.run();

        let subroutines = analysis.subroutines.borrow();
        let loop_sub = &subroutines[&0x9002];
        assert_eq!(loop_sub.label(), "loop");
        assert_eq!(loop_sub.instructions().len(), 1);
    }

    test_rom!(setup_unknown_responsibility, "unknown_responsibility.asm");
    #[test]
    fn test_unknown_responsibility() {
        let analysis = Analysis::new(setup_unknown_responsibility());
        analysis.run();
        let subroutines = analysis.subroutines.borrow();

        let reset_sub = &subroutines[&0x8000];
        assert!(reset_sub.has_unknown_state_change());
        assert!(!reset_sub.is_responsible_for_unknown());

        let unknown_sub = &subroutines[&0x8006];
        assert!(unknown_sub.has_unknown_state_change());
        assert!(unknown_sub.is_responsible_for_unknown());
    }
}
