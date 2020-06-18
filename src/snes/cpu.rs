use std::rc::Rc;

use crate::analysis::Analysis;
use crate::snes::instruction::{Instruction, InstructionType};
use crate::snes::opcodes::{AddressMode, Op};
use crate::snes::register::Register;
use crate::snes::rom::ROM;
use crate::snes::stack;
use crate::snes::state::{StateRegister, SubStateChange, UnknownReason};

/// SNES CPU emulation.
#[allow(non_snake_case)]
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

    /// Processor state change caused by the execution of this subroutine.
    sub_state_change: SubStateChange,

    /// Stack.
    stack: stack::Stack,

    /// Registers.
    A: Register,
}

impl CPU {
    /// Instantiate a CPU object.
    pub fn new(analysis: &Rc<Analysis>, pc: usize, subroutine: usize, p: u8) -> Self {
        Self {
            analysis: analysis.clone(),
            stop: false,
            pc,
            subroutine,
            state: StateRegister::new(p),
            sub_state_change: SubStateChange::new_empty(),
            stack: stack::Stack::new(),
            A: Register::new(true),
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
        // Stop if we have jumped into RAM.
        if ROM::is_ram(self.pc) {
            return self.stop = true;
        }

        let opcode = self.analysis.rom.read_byte(self.pc);
        let argument = self.analysis.rom.read_address(self.pc + 1);
        let instruction =
            Instruction::new(self.pc, self.subroutine, self.state.p(), opcode, argument);

        // Stop the analysis if we have already visited this instruction.
        if self.analysis.is_visited(instruction) {
            self.stop = true;
        } else {
            self.analysis.add_instruction(instruction);
            self.execute(instruction);
        }
    }

    /// Emulate an instruction.
    fn execute(&mut self, instruction: Instruction) {
        self.pc += instruction.size();

        match instruction.typ() {
            InstructionType::Branch => self.branch(instruction),
            InstructionType::Call => self.call(instruction),
            InstructionType::Interrupt => self.interrupt(instruction),
            InstructionType::Jump => self.jump(instruction),
            InstructionType::Return => self.ret(instruction),
            InstructionType::SepRep => self.sep_rep(instruction),
            InstructionType::Pop => self.pop(instruction),
            InstructionType::Push => self.push(instruction),
            _ if instruction.changes_a() => self.change_a(instruction),
            _ if instruction.changes_stack() => self.change_stack(instruction),
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
        self.analysis
            .add_reference(instruction.pc(), target, self.subroutine);
        self.pc = target;
    }

    /// Call instruction emulation.
    fn call(&mut self, instruction: Instruction) {
        match instruction.absolute_argument() {
            Some(target) => {
                // Create a parallel instance of the CPU to
                // execute the subroutine that is being called.
                let mut cpu = self.clone();
                cpu.sub_state_change = SubStateChange::new_empty();
                cpu.subroutine = target;
                cpu.pc = target;

                // Emulate the called subroutine.
                self.analysis.add_subroutine(target, None);
                self.analysis
                    .add_reference(instruction.pc(), target, self.subroutine);
                cpu.run();

                // Propagate called subroutine state to caller.
                self.propagate_subroutine_state(target);
            }
            None => self.unknown_sub_state_change(UnknownReason::IndirectJump),
        }
    }

    /// Emulate instructions that modify the value of A.
    fn change_a(&mut self, i: Instruction) {
        #[allow(non_snake_case)]
        let A = &mut self.A;
        let s = self.state;

        match i.address_mode() {
            AddressMode::ImmediateM => {
                let a = A.get(s);
                let arg = i.argument().unwrap() as u16;
                match i.operation() {
                    Op::LDA => A.set(s, Some(arg)),
                    Op::ADC if a.is_some() => A.set(s, Some(a.unwrap() + arg)),
                    Op::SBC if a.is_some() => A.set(s, Some(a.unwrap() - arg)),
                    _ => A.set(s, None),
                }
            }
            _ => {
                match i.operation() {
                    Op::TSC => A.set_whole(Some(self.stack.pointer() as u16)),
                    Op::PLA => {
                        // TODO: assign value to A.
                        self.stack.pop(self.state.a_size());
                    }
                    _ => A.set(s, None),
                }
            }
        }
    }

    /// Emulate instructions that modify the stack pointer.
    fn change_stack(&mut self, i: Instruction) {
        match i.operation() {
            Op::TCS => match self.A.get_whole() {
                Some(a) => self.stack.set_pointer(i, a),
                None => self.unknown_sub_state_change(UnknownReason::StackManipulation),
            },
            _ => {}
        }
    }

    /// Interrupt instruction emulation.
    fn interrupt(&mut self, _instruction: Instruction) {
        self.unknown_sub_state_change(UnknownReason::SuspectInstruction);
    }

    /// Jump instruction emulation.
    fn jump(&mut self, instruction: Instruction) {
        match instruction.absolute_argument() {
            Some(target) => {
                self.pc = target;
                self.analysis
                    .add_reference(instruction.pc(), target, self.subroutine);
            }
            None => self.unknown_sub_state_change(UnknownReason::IndirectJump),
        }
    }

    /// Return instruction emulation.
    fn ret(&mut self, _instruction: Instruction) {
        self.stop = true;
        self.analysis
            .add_sub_state_change(self.subroutine, self.sub_state_change);
    }

    /// SEP/REP instruction emulation.
    fn sep_rep(&mut self, instruction: Instruction) {
        let arg = instruction.absolute_argument().unwrap();
        match instruction.operation() {
            Op::SEP => {
                self.state.set(arg as u8);
                self.sub_state_change.set(arg as u8);
            }
            // Op::REP
            _ => {
                self.state.reset(arg as u8);
                self.sub_state_change.reset(arg as u8);
            }
        }
    }

    /// Push a value onto the stack.
    fn push(&mut self, instruction: Instruction) {
        match instruction.operation() {
            Op::PHP => self.stack.push_one(
                instruction,
                stack::Data::State(self.state, self.sub_state_change),
            ),
            // TODO: emulate other push instructions.
            _ => {}
        }
    }

    /// Pop a value from the stack.
    fn pop(&mut self, instruction: Instruction) {
        match instruction.operation() {
            Op::PLP => {
                let entry = self.stack.pop_one();
                match entry.instruction {
                    // Regular state restore.
                    Some(i) if i.operation() == Op::PHP => match entry.data {
                        stack::Data::State(state, state_change) => {
                            self.state = state;
                            self.sub_state_change = state_change;
                        }
                        _ => unreachable!(),
                    },
                    // Stack manipulation. Stop here.
                    _ => {
                        self.unknown_sub_state_change(UnknownReason::StackManipulation);
                        self.stop = true;
                    }
                }
            }
            // TODO: emulate other pop instructions.
            _ => {}
        }
    }

    /// Take the state change of the given subroutine and
    /// propagate it to to the current subroutine state.
    fn propagate_subroutine_state(&mut self, subroutine: usize) {
        let subroutines = self.analysis.subroutines().borrow();
        let sub = &subroutines[&subroutine];

        // Unknown or ambiguous state change.
        if sub.state_changes().len() != 1 || sub.has_unknown_state_change() {
            drop(subroutines);
            return self.unknown_sub_state_change(UnknownReason::Unknown);
        }

        // Apply state change.
        let state_change = *sub.state_changes().values().next().unwrap();
        if let Some(m) = state_change.m() {
            self.state.set_m(m);
            self.sub_state_change.set_m(m);
        }
        if let Some(x) = state_change.x() {
            self.state.set_x(x);
            self.sub_state_change.set_x(x);
        }
    }

    /// Signal an unknown subroutine state change.
    fn unknown_sub_state_change(&mut self, reason: UnknownReason) {
        self.stop = true;
        self.analysis
            .add_sub_state_change(self.subroutine, SubStateChange::new_unknown(reason));
    }

    #[cfg(test)]
    fn setup_instruction(&self, opcode: u8, argument: usize) -> Instruction {
        Instruction::new(self.pc, self.subroutine, self.state.p(), opcode, argument)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_cpu(p: u8) -> CPU {
        let analysis = Analysis::new(ROM::new());
        analysis.add_subroutine(0x8000, None);
        CPU::new(&analysis, 0x8000, 0x8000, p)
    }

    #[test]
    fn test_branch() {
        let mut cpu = setup_cpu(0b0000_0000);
        cpu.stop = true;

        let bcc = cpu.setup_instruction(0x90, 0x10);
        cpu.execute(bcc);
        assert_eq!(cpu.pc, 0x8012);
    }

    #[test]
    fn test_call() {
        let mut cpu = setup_cpu(0b0000_0000);
        cpu.stop = true;

        let jsr = cpu.setup_instruction(0x20, 0x9000);
        cpu.execute(jsr);

        assert_eq!(cpu.pc, 0x8003);
        assert!(cpu.analysis.is_subroutine(0x9000));
    }

    #[test]
    fn test_interrupt() {
        let mut cpu = setup_cpu(0b0000_0000);
        let brk = cpu.setup_instruction(0x00, 0x00);
        cpu.execute(brk);
        assert!(cpu.stop);
    }

    #[test]
    fn test_jump() {
        let mut cpu = setup_cpu(0b0000_0000);
        let jmp = cpu.setup_instruction(0x4C, 0x9000);
        cpu.execute(jmp);
        assert_eq!(cpu.pc, 0x9000);
    }

    #[test]
    fn test_ret() {
        let mut cpu = setup_cpu(0b0000_0000);
        let rts = cpu.setup_instruction(0x60, 0x00);
        cpu.execute(rts);
        assert!(cpu.stop);

        let mut cpu = setup_cpu(0b0000_0000);
        let rtl = cpu.setup_instruction(0x6B, 0x00);
        cpu.execute(rtl);
        assert!(cpu.stop);
    }

    #[test]
    fn test_sep_rep() {
        let mut cpu = setup_cpu(0b0000_0000);

        let sep = cpu.setup_instruction(0xE2, 0x30);
        cpu.execute(sep);
        assert_eq!(cpu.pc, sep.pc() + 2);
        assert_eq!(cpu.state.p(), 0b0011_0000);

        let rep = cpu.setup_instruction(0xC2, 0x30);
        cpu.execute(rep);
        assert_eq!(cpu.pc, rep.pc() + 2);
        assert_eq!(cpu.state.p(), 0b0000_0000);
    }
}
