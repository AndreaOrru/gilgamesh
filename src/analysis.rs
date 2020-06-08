use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::rc::Rc;

use crate::snes::cpu::CPU;
use crate::snes::instruction::Instruction;
use crate::snes::rom::ROM;
use crate::snes::subroutine::Subroutine;

/// ROM's entry point.
#[derive(Eq, Hash, PartialEq)]
struct EntryPoint {
    name: String,
    pc: usize,
    p: u8,
}

/// Structure holding the state of the analysis.
pub struct Analysis {
    /// Reference to the ROM being analyzed.
    pub rom: ROM,

    /// All analyzed subroutines.
    subroutines: RefCell<HashMap<usize, Subroutine>>,

    /// All analyzed instructions.
    instructions: RefCell<HashMap<usize, HashSet<Instruction>>>,

    /// ROM's entry points.
    entry_points: HashSet<EntryPoint>,

    /// Instructions referenced by other instructions.
    references: RefCell<HashMap<usize, usize>>,
}

impl Analysis {
    /// Instantiate a new Analysis object.
    pub fn new(rom: ROM) -> Rc<Self> {
        let entry_points = Self::default_entry_points(&rom);
        Rc::new(Self {
            rom,
            instructions: RefCell::new(HashMap::new()),
            subroutines: RefCell::new(HashMap::new()),
            entry_points,
            references: RefCell::new(HashMap::new()),
        })
    }

    /// Return the default entry points for the ROM under analysis.
    #[cfg(not(test))]
    fn default_entry_points(rom: &ROM) -> HashSet<EntryPoint> {
        maplit::hashset! {
            EntryPoint { name: "reset".into(), pc: rom.reset_vector(), p: 0b0011_0000},
            EntryPoint { name: "nmi".into(),   pc: rom.nmi_vector(),   p: 0b0011_0000},
        }
    }
    #[cfg(test)]
    fn default_entry_points(_rom: &ROM) -> HashSet<EntryPoint> {
        HashSet::new()
    }

    /// Analyze the ROM.
    pub fn run(self: &Rc<Self>) {
        for EntryPoint { name: _, pc, p } in self.entry_points.iter() {
            self.add_subroutine(*pc);
            let mut cpu = CPU::new(self, *pc, *pc, *p);
            cpu.run();
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
    pub fn add_subroutine(&self, pc: usize) {
        // Do not log subroutines in RAM.
        if ROM::is_ram(pc) {
            return;
        }
        // Create and register subroutine (unless it already exists).
        let mut subroutines = self.subroutines.borrow_mut();
        subroutines.entry(pc).or_insert_with(|| Subroutine::new(pc));
    }

    /// Add a reference from an instruction to another.
    pub fn add_reference(&self, source: usize, target: usize) {
        let mut references = self.references.borrow_mut();
        references.insert(source, target);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_analysis() -> Rc<Analysis> {
        Analysis::new(ROM::new())
    }

    #[test]
    fn test_add_instruction_and_subroutine() {
        let analysis = setup_analysis();

        analysis.add_subroutine(0x8000);
        assert!(analysis.is_subroutine(0x8000));

        let nop = Instruction::new(0x8000, 0x8000, 0b0011_0000, 0xEA, 0x00);
        analysis.add_instruction(nop);
        assert!(analysis.is_visited_pc(0x8000));
    }
}
