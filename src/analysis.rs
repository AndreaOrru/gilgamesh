use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::rc::Rc;

use crate::snes::cpu::CPU;
use crate::snes::instruction::{Instruction, InstructionID};
use crate::snes::rom::ROM;
use crate::snes::subroutine::Subroutine;

/// ROM's entry point.
struct EntryPoint {
    pc: usize,
    p: u8,
    name: String,
}

/// Structure holding the state of the analysis.
pub struct Analysis {
    /// Reference to the ROM being analyzed.
    pub rom: ROM,

    /// All analyzed instructions.
    instructions: RefCell<HashMap<InstructionID, Instruction>>,

    /// All analyzed subroutines.
    subroutines: RefCell<HashMap<usize, Subroutine>>,

    /// ROM's entry points.
    entry_points: HashSet<EntryPoint>,

    /// Instructions referenced by other instructions.
    references: RefCell<HashMap<usize, usize>>,
}

impl Analysis {
    /// Instantiate a new Analysis object.
    pub fn new(rom: ROM) -> Rc<Self> {
        Rc::new(Self {
            rom,
            instructions: RefCell::new(HashMap::new()),
            subroutines: RefCell::new(HashMap::new()),
            entry_points: HashSet::new(),
            references: RefCell::new(HashMap::new()),
        })
    }

    /// Analyze the ROM.
    pub fn run(self: &Rc<Self>) {
        for EntryPoint { pc, p, name: _ } in self.entry_points.iter() {
            let mut cpu = CPU::new(self, *pc, *pc, *p);
            cpu.run();
        }
    }

    /// Return true if the instruction has already been analyzed, false otherwise.
    pub fn is_visited(&self, instruction_id: InstructionID) -> bool {
        self.instructions.borrow().contains_key(&instruction_id)
    }

    /// Add an instruction to the analysis.
    pub fn add_instruction(
        &self,
        pc: usize,
        subroutine: usize,
        p: u8,
        opcode: u8,
        argument: usize,
    ) -> Instruction {
        let mut instructions = self.instructions.borrow_mut();
        let instruction = Instruction::new(pc, subroutine, p, opcode, argument);
        instructions.insert(instruction.id(), instruction);

        let mut subroutines = self.subroutines.borrow_mut();
        let subroutine = subroutines.get_mut(&subroutine).unwrap();
        subroutine.add_instruction(instruction.id());

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
