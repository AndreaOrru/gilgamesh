use std::rc::Rc;

use crate::analysis::Analysis;
use crate::snes::instruction::{Instruction, InstructionID, InstructionType};
use crate::snes::opcodes::Op;
use crate::snes::rom::ROM;
use crate::snes::state::StateRegister;

/// SNES CPU emulation.
#[derive(Clone)]
pub struct CPU {
    /// Reference to the analysis.
    analysis: Rc<Analysis>,

    /// Whether we should stop emulating after the current instruction.
    stop: bool,

    /// Program Counter.
    pc: usize,

    /// Subroutine currently being executed.
    subroutine: usize,

    /// Processor state.
    state: StateRegister,
}

impl CPU {
    /// Instantiate a CPU object.
    pub fn new(analysis: &Rc<Analysis>, pc: usize, subroutine: usize, p: u8) -> Self {
        Self {
            analysis: analysis.clone(),
            stop: true,
            pc,
            subroutine,
            state: StateRegister::new(p),
        }
    }

    /// Start emulating.
    pub fn run(&mut self) {
        while !self.stop {
            self.step();
        }
    }

    /// Fetch and execute the next instruction.
    fn step(&mut self) {
        if ROM::is_ram(self.pc) || self.analysis.is_visited(self.instruction_id()) {
            self.stop = true;
        }

        let opcode = self.analysis.rom.read_byte(self.pc);
        let argument = self.analysis.rom.read_address(self.pc + 1);
        let instruction = self.analysis.add_instruction(
            self.pc,
            self.subroutine,
            self.state.p(),
            opcode,
            argument,
        );

        self.execute(instruction);
    }

    /// Emulate an instruction.
    fn execute(&mut self, instruction: Instruction) {
        self.pc += instruction.size();

        match instruction.typ() {
            // InstructionType::Return => self.ret(instruction),
            InstructionType::Interrupt => unreachable!(),
            // InstructionType::Jump => self.jump(instruction),
            // InstructionType::Call => self.call(instruction),
            InstructionType::Branch => self.branch(instruction),
            InstructionType::SepRep => self.sep_rep(instruction),
            // InstructionType::Pop => self.pop(instruction),
            // InstructionType::Push => self.push(instruction),
            _ => {}
        }
    }

    /// Branch instruction emulation.
    fn branch(&mut self, instruction: Instruction) {
        // Run a parallel instance of the CPU to cover
        // the case in which the branch is not taken.
        let mut cpu = self.clone();
        cpu.run();

        // Log the fact that the current instruction references the
        // instruction pointed by the branch. Then take the branch.
        let target = instruction.absolute_argument().unwrap();
        // TODO: self.log.add_reference(instruction, target)
        self.pc = target;
    }

    /// SEP/REP instruction emulation.
    fn sep_rep(&mut self, instruction: Instruction) {
        let arg = instruction.absolute_argument().unwrap();

        match instruction.operation() {
            Op::SEP => self.state.set(arg as u8),
            Op::REP => self.state.reset(arg as u8),
            _ => unreachable!(),
        }
    }

    /// Return the InstructionID of the instruction currently being executed.
    fn instruction_id(&self) -> InstructionID {
        InstructionID {
            pc: self.pc,
            subroutine: self.subroutine,
            p: self.state.p(),
        }
    }
}
