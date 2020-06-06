use std::rc::Rc;

use derive_new::new;

use crate::analysis::Analysis;
use crate::snes::opcodes::{AddressMode, Op, ARGUMENT_SIZES, OPCODES};
use crate::snes::state::StateRegister;

/// Unique identifier of an instruction executed
/// in a specific state and subroutine.
#[derive(new)]
pub struct InstructionID {
    pc: usize,
    subroutine: usize,
    p: u8,
}

/// Structure representing an instruction.
pub struct Instruction {
    analysis: Rc<Analysis>,
    pc: usize,
    subroutine: usize,
    state_register: StateRegister,
    opcode: u8,
    _argument: usize,
}

impl Instruction {
    /// Instantiate an instruction.
    pub fn new(
        analysis: Rc<Analysis>,
        pc: usize,
        subroutine: usize,
        p: u8,
        opcode: u8,
        argument: usize,
    ) -> Self {
        Self {
            analysis,
            pc,
            subroutine,
            state_register: StateRegister::new(p),
            opcode,
            _argument: argument,
        }
    }

    /// Return the InstructionID associated with the current instruction.
    pub fn id(&self) -> InstructionID {
        InstructionID::new(self.pc, self.subroutine, self.state_register.p())
    }

    /// Return the name of the instruction's operation.
    pub fn name(&self) -> String {
        let name: &str = self.operation().into();
        name.to_lowercase()
    }

    /// Return the instruction's operation.
    pub fn operation(&self) -> Op {
        OPCODES[self.opcode as usize].0
    }

    /// Return the instruction's address mode.
    pub fn address_mode(&self) -> AddressMode {
        OPCODES[self.opcode as usize].1
    }

    /// Return the instruction's size.
    pub fn size(&self) -> usize {
        self.argument_size() + 1
    }

    /// Return the instruction's argument size.
    pub fn argument_size(&self) -> usize {
        let address_mode = self.address_mode();
        let size = ARGUMENT_SIZES[address_mode];
        if size != -1 {
            return size as usize;
        }

        match address_mode {
            AddressMode::ImmediateM => self.state_register.a_size(),
            AddressMode::ImmediateX => self.state_register.x_size(),
            _ => unreachable!(),
        }
    }

    /// Return the instruction's argument, if any.
    pub fn argument(&self) -> Option<usize> {
        match self.argument_size() {
            0 => None,
            1 => Some(self._argument & 0xFF),
            2 => Some(self._argument & 0xFFFF),
            3 => Some(self._argument & 0xFFFFFF),
            _ => unreachable!(),
        }
    }

    /// Return the instruction's argument as an absolute value, if possible.
    pub fn absolute_argument(&self) -> Option<usize> {
        if self.argument() == None {
            return None;
        }
        let (pc, size, argument) = (
            self.pc as isize,
            self.size() as isize,
            self.argument().unwrap() as isize,
        );

        match self.address_mode() {
            AddressMode::ImmediateM
            | AddressMode::ImmediateX
            | AddressMode::Immediate8
            | AddressMode::AbsoluteLong => Some(argument as usize),

            AddressMode::Absolute => {
                if self.is_control() {
                    Some(((pc & 0xFF0000) | argument) as usize)
                } else {
                    None
                }
            }

            AddressMode::Relative => {
                let argument = (argument as i8) as isize;
                Some((pc + size + argument) as usize)
            }
            AddressMode::RelativeLong => {
                let argument = (argument as i16) as isize;
                Some((pc + size + argument) as usize)
            }

            _ => None,
        }
    }

    /// Return whether the instruction is a branch.
    #[allow(clippy::needless_return)]
    pub fn is_branch(&self) -> bool {
        let op = self.operation();
        return (op == Op::BCC)
            || (op == Op::BCS)
            || (op == Op::BEQ)
            || (op == Op::BMI)
            || (op == Op::BNE)
            || (op == Op::BPL)
            || (op == Op::BVC)
            || (op == Op::BVS);
    }

    /// Return whether the instruction is a call.
    pub fn is_call(&self) -> bool {
        let op = self.operation();
        (op == Op::JSR) || (op == Op::JSL)
    }

    /// Return whether the instruction is a jump.
    pub fn is_jump(&self) -> bool {
        let op = self.operation();
        (op == Op::BRA) || (op == Op::BRL) || (op == Op::JMP) || (op == Op::JML)
    }

    /// Return whether the instruction is a return.
    pub fn is_return(&self) -> bool {
        let op = self.operation();
        (op == Op::RTS) || (op == Op::RTL) || (op == Op::RTI)
    }

    /// Return whether the instruction handles interrupts.
    pub fn is_interrupt(&self) -> bool {
        let op = self.operation();
        (op == Op::BRK) || (op == Op::RTI)
    }

    /// Return whether this is a control instruction.
    #[allow(clippy::needless_return)]
    pub fn is_control(&self) -> bool {
        return self.is_branch()
            || self.is_call()
            || self.is_jump()
            || self.is_return()
            || self.is_interrupt();
    }

    /// Return whether the instruction is a SEP/REP.
    pub fn is_sep_rep(&self) -> bool {
        let op = self.operation();
        (op == Op::SEP) || (op == Op::REP)
    }

    /// Return whether the instruction is a pop.
    #[allow(clippy::needless_return)]
    pub fn is_pop(&self) -> bool {
        let op = self.operation();
        return (op == Op::PLA)
            || (op == Op::PLB)
            || (op == Op::PLD)
            || (op == Op::PLP)
            || (op == Op::PLX)
            || (op == Op::PLY);
    }

    /// Return whether the instruction is a push.
    #[allow(clippy::needless_return)]
    pub fn is_push(&self) -> bool {
        let op = self.operation();
        return (op == Op::PEA)
            || (op == Op::PEI)
            || (op == Op::PER)
            || (op == Op::PHA)
            || (op == Op::PHB)
            || (op == Op::PHD)
            || (op == Op::PHK)
            || (op == Op::PHP)
            || (op == Op::PHX)
            || (op == Op::PHY);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::snes::rom::ROM;

    fn setup_analysis() -> Rc<Analysis> {
        let rom = ROM::new();
        let analysis = Analysis::new(rom);
        Rc::new(analysis)
    }

    #[test]
    fn test_instruction_lda() {
        let instruction =
            Instruction::new(setup_analysis(), 0x8000, 0x8000, 0b0000_0000, 0xA9, 0x1234);

        assert_eq!(instruction.name(), "lda");
        assert_eq!(instruction.operation(), Op::LDA);
        assert_eq!(instruction.address_mode(), AddressMode::ImmediateM);
        assert_eq!(instruction.argument_size(), 2);
        assert_eq!(instruction.size(), 3);
        assert_eq!(instruction.argument().unwrap(), 0x1234);
        assert_eq!(instruction.absolute_argument().unwrap(), 0x1234);
        assert!(!instruction.is_control());
    }

    #[test]
    fn test_instruction_brl() {
        let instruction =
            Instruction::new(setup_analysis(), 0x8000, 0x8000, 0b0000_0000, 0x82, 0xFFFD);

        assert_eq!(instruction.name(), "brl");
        assert_eq!(instruction.operation(), Op::BRL);
        assert_eq!(instruction.address_mode(), AddressMode::RelativeLong);
        assert_eq!(instruction.argument_size(), 2);
        assert_eq!(instruction.size(), 3);
        assert_eq!(instruction.argument().unwrap(), 0xFFFD);
        assert_eq!(instruction.absolute_argument().unwrap(), 0x8000);
        assert!(instruction.is_control());
        assert!(instruction.is_jump());
    }
}
