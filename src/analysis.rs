use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::Rc;

use crate::snes::cpu::CPU;
use crate::snes::instruction::{Instruction, InstructionID};
use crate::snes::rom::ROM;
use crate::snes::subroutine::Subroutine;

/// ROM's entry point.
struct EntryPoint {
    name: String,
    p: u8,
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
    entry_points: HashMap<usize, EntryPoint>,
}

impl Analysis {
    /// Instantiate a new Analysis object.
    pub fn new(rom: ROM) -> Rc<Self> {
        Rc::new(Self {
            rom,
            instructions: RefCell::new(HashMap::new()),
            subroutines: RefCell::new(HashMap::new()),
            entry_points: HashMap::new(),
        })
    }

    /// Analyze the ROM.
    pub fn run(self: &Rc<Self>) {
        for (pc, EntryPoint { name: _, p }) in self.entry_points.iter() {
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
}
