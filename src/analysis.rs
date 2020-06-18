use std::cell::RefCell;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::rc::Rc;

use bimap::BiHashMap;
use getset::Getters;

use crate::snes::cpu::CPU;
use crate::snes::instruction::Instruction;
use crate::snes::rom::{ROMType, ROM};
use crate::snes::state::SubStateChange;
use crate::snes::subroutine::Subroutine;

/// ROM's entry point.
#[derive(Eq, Hash, PartialEq)]
struct EntryPoint {
    label: String,
    pc: usize,
    p: u8,
}

/// Code reference.
#[derive(Debug, Eq, PartialEq)]
struct Reference {
    target: usize,
    subroutine: usize,
}

/// Structure holding the state of the analysis.
#[derive(Getters)]
pub struct Analysis {
    /// Reference to the ROM being analyzed.
    pub rom: ROM,

    /// All analyzed subroutines.
    #[getset(get = "pub")]
    subroutines: RefCell<BTreeMap<usize, Subroutine>>,

    /// All analyzed instructions.
    instructions: RefCell<HashMap<usize, HashSet<Instruction>>>,

    /// ROM's entry points.
    entry_points: HashSet<EntryPoint>,

    /// Instructions referenced by other instructions.
    references: RefCell<HashMap<usize, Reference>>,

    /// Subroutine labels.
    #[getset(get = "pub")]
    subroutine_labels: RefCell<BiHashMap<String, usize>>,

    /// Subroutine local labels.
    #[getset(get = "pub")]
    local_labels: RefCell<HashMap<usize, BiHashMap<String, usize>>>,
}

impl Analysis {
    /// Instantiate a new Analysis object.
    pub fn new(rom: ROM) -> Rc<Self> {
        let entry_points = Self::default_entry_points(&rom);
        Rc::new(Self {
            rom,
            instructions: RefCell::new(HashMap::new()),
            subroutines: RefCell::new(BTreeMap::new()),
            entry_points,
            references: RefCell::new(HashMap::new()),
            subroutine_labels: RefCell::new(BiHashMap::new()),
            local_labels: RefCell::new(HashMap::new()),
        })
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

    /// Analyze the ROM.
    pub fn run(self: &Rc<Self>) {
        for EntryPoint { label, pc, p } in self.entry_points.iter() {
            self.add_subroutine(*pc, Some(label.clone()));
            let mut cpu = CPU::new(self, *pc, *pc, *p);
            cpu.run();
        }
        self.generate_local_labels();
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

    /// Return true if the given subroutine is part of the analysis, false otherwise.
    pub fn is_subroutine(&self, pc: usize) -> bool {
        self.subroutines.borrow().contains_key(&pc)
    }

    /// Add an instruction to the analysis.
    pub fn add_instruction(&self, instruction: Instruction) -> Instruction {
        let mut instructions = self.instructions.borrow_mut();
        instructions
            .entry(instruction.pc())
            .or_insert_with(HashSet::new)
            .insert(instruction);

        let mut subroutines = self.subroutines.borrow_mut();
        let subroutine = subroutines.get_mut(&instruction.subroutine()).unwrap();
        subroutine.add_instruction(instruction);

        instruction
    }

    /// Add a subroutine to the analysis.
    pub fn add_subroutine(&self, pc: usize, label: Option<String>) {
        // Do not log subroutines in RAM.
        if ROM::is_ram(pc) {
            return;
        }

        // Register subroutine's label.
        let mut labels = self.subroutine_labels.borrow_mut();
        let label = match label {
            Some(s) => s,
            None => format!("sub_{:06X}", pc),
        };
        labels.insert(label.clone(), pc);

        // Create and register subroutine (unless it already exists).
        let mut subroutines = self.subroutines.borrow_mut();
        subroutines
            .entry(pc)
            .or_insert_with(|| Subroutine::new(pc, label));
    }

    /// Add a state change to a subroutine.
    pub fn add_sub_state_change(&self, pc: usize, state_change: SubStateChange) {
        let mut subroutines = self.subroutines.borrow_mut();
        let subroutine = subroutines.get_mut(&pc).unwrap();
        subroutine.add_state_change(state_change);
    }

    /// Add a reference from an instruction to another.
    pub fn add_reference(&self, source: usize, target: usize, subroutine: usize) {
        let mut references = self.references.borrow_mut();
        references.insert(source, Reference { target, subroutine });
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

    /// Generate local label names.
    fn generate_local_labels(&self) {
        for (_, Reference { target, subroutine }) in self.references.borrow().iter() {
            if !self.is_subroutine(*target) {
                let label = format!("loc_{:06X}", *target);
                let mut local_labels = self.local_labels.borrow_mut();
                local_labels
                    .entry(*subroutine)
                    .or_insert_with(BiHashMap::new)
                    .insert(label, *target);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::snes::opcodes::Op;
    use gilgamesh::test_rom;

    test_rom!(setup_infinite_loop, "infinite_loop.asm");
    test_rom!(setup_state_change, "sub_state_change.asm");
    test_rom!(setup_unknown_call_jump, "unknown_call_jump.asm");

    #[test]
    fn test_instruction_subroutine_references() {
        let analysis = Analysis::new(ROM::new());

        analysis.add_subroutine(0x8000, None);
        assert!(analysis.is_subroutine(0x8000));

        let nop = Instruction::new(0x8000, 0x8000, 0b0011_0000, 0xEA, 0x00);
        analysis.add_instruction(nop);
        assert!(analysis.is_visited_pc(0x8000));
    }

    #[test]
    fn test_infinite_loop_analysis() {
        let analysis = Analysis::new(setup_infinite_loop());
        analysis.run();

        // Check there is a single subroutine with one instruction.
        let subroutines = analysis.subroutines.borrow();
        assert_eq!(subroutines.len(), 1);
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
        assert_eq!(
            references[&0x8000],
            Reference {
                target: 0x8000,
                subroutine: 0x8000
            }
        );
    }

    #[test]
    fn test_state_change() {
        let analysis = Analysis::new(setup_state_change());
        analysis.run();

        // Check there are two subroutines.
        let subroutines = analysis.subroutines.borrow();
        assert_eq!(subroutines.len(), 2);

        // Check the subroutines have the right name and number of instructions.
        let reset_sub = &subroutines[&0x8000];
        assert_eq!(reset_sub.label(), "reset");
        assert_eq!(reset_sub.instructions().len(), 5);
        let state_change_sub = &subroutines[&0x800E];
        assert_eq!(state_change_sub.label(), "sub_00800E");
        assert_eq!(state_change_sub.instructions().len(), 2);

        // Check the `state_change` subroutine sets M/X to 0.
        let state_change = state_change_sub.state_changes().iter().next().unwrap();
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

    #[test]
    fn test_unknown_call_jump() {
        let analysis = Analysis::new(setup_unknown_call_jump());
        analysis.run();

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
}