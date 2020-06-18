use getset::CopyGetters;
use std::cmp::Ordering;
use std::hash::{Hash, Hasher};
use std::rc::Rc;

use crate::analysis::Analysis;
use crate::snes::hardware_registers::HARDWARE_REGISTERS;
use crate::snes::opcodes::{AddressMode, Op, ARGUMENT_SIZES, OPCODES};
use crate::snes::state::StateRegister;

/// Categories of instructions.
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum InstructionType {
    Branch,
    Call,
    Interrupt,
    Other,
    Jump,
    Pop,
    Push,
    Return,
    SepRep,
}

/// Structure representing an instruction.
#[derive(Copy, Clone, CopyGetters, Debug, Eq)]
pub struct Instruction {
    /// The address of the instruction.
    #[getset(get_copy = "pub")]
    pc: usize,

    /// The address of the subroutine this instruction belongs to.
    #[getset(get_copy = "pub")]
    subroutine: usize,

    /// Processor state in which the instruction is executed.
    state: StateRegister,

    /// The instruction's opcode byte.
    opcode: u8,

    /// The instruction argument (if any).
    _argument: usize,
}

// Implement some traits for Instruction.
impl Hash for Instruction {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.pc.hash(state);
        self.subroutine.hash(state);
        self.state.p().hash(state);
    }
}
impl PartialEq for Instruction {
    fn eq(&self, other: &Self) -> bool {
        self.pc == other.pc
            && self.subroutine == other.subroutine
            && self.state.p() == other.state.p()
    }
}
impl PartialOrd for Instruction {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for Instruction {
    fn cmp(&self, other: &Self) -> Ordering {
        self.pc.cmp(&other.pc)
    }
}

impl Instruction {
    /// Instantiate an instruction.
    pub fn new(pc: usize, subroutine: usize, p: u8, opcode: u8, argument: usize) -> Self {
        Self {
            pc,
            subroutine,
            state: StateRegister::new(p),
            opcode,
            _argument: argument,
        }
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

    /// Category of the instruction.
    pub fn typ(&self) -> InstructionType {
        match self.operation() {
            // Call instructions.
            Op::JSR | Op::JSL => InstructionType::Call,

            // Jump instructions.
            Op::JMP | Op::JML | Op::BRA | Op::BRL => InstructionType::Jump,

            // Return instructions.
            Op::RTS | Op::RTL | Op::RTI => InstructionType::Return,

            // Interrupt instructions.
            Op::BRK => InstructionType::Interrupt,

            // SEP/REP instructions.
            Op::SEP | Op::REP => InstructionType::SepRep,

            // Pop instructions.
            Op::PLA | Op::PLB | Op::PLD | Op::PLP | Op::PLX | Op::PLY => InstructionType::Pop,

            // Push instructions.
            Op::PEA
            | Op::PEI
            | Op::PER
            | Op::PHA
            | Op::PHB
            | Op::PHD
            | Op::PHK
            | Op::PHP
            | Op::PHX
            | Op::PHY => InstructionType::Push,

            // Branch instructions.
            Op::BCC | Op::BCS | Op::BEQ | Op::BMI | Op::BNE | Op::BPL | Op::BVC | Op::BVS => {
                InstructionType::Branch
            }

            // Other instructions.
            _ => InstructionType::Other,
        }
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
            AddressMode::ImmediateM => self.state.a_size(),
            AddressMode::ImmediateX => self.state.x_size(),
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
        // No argument.
        if self.argument() == None {
            return None;
        }
        let (pc, size, argument) = (
            self.pc as isize,
            self.size() as isize,
            self.argument().unwrap() as isize,
        );

        match self.address_mode() {
            // Fully specified argument.
            AddressMode::ImmediateM
            | AddressMode::ImmediateX
            | AddressMode::Immediate8
            | AddressMode::AbsoluteLong => Some(argument as usize),

            // Partially specified argument.
            AddressMode::Absolute => {
                if self.is_control() {
                    Some(((pc & 0xFF0000) | argument) as usize)
                } else {
                    None
                }
            }

            // Branches.
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

    /// Return whether this is a control instruction.
    pub fn is_control(&self) -> bool {
        let typ = self.typ();
        typ == InstructionType::Branch
            || typ == InstructionType::Call
            || typ == InstructionType::Jump
            || typ == InstructionType::Return
            || typ == InstructionType::Interrupt
    }

    /// Return whether this instruction modifies A.
    pub fn changes_a(&self) -> bool {
        let op = self.operation();
        op == Op::ADC
            || op == Op::AND
            || op == Op::ASL
            || op == Op::DEC
            || op == Op::EOR
            || op == Op::INC
            || op == Op::LDA
            || op == Op::LSR
            || op == Op::ORA
            || op == Op::PLA
            || op == Op::ROL
            || op == Op::ROR
            || op == Op::SBC
            || op == Op::TDC
            || op == Op::TSC
            || op == Op::TXA
            || op == Op::TYA
            || op == Op::XBA
    }

    /// Return whether this instruction modifies the stack pointer.
    pub fn changes_stack(&self) -> bool {
        let op = self.operation();
        op == Op::TCS || op == Op::TXS
    }

    /// Return the instruction's argument as a string.
    pub fn argument_string(&self) -> String {
        // Return the string corresponding to the argument size.
        let arg = || match self.argument_size() {
            1 => format!("${:02X}", self.argument().unwrap()),
            2 => format!("${:04X}", self.argument().unwrap()),
            _ => format!("${:06X}", self.argument().unwrap()),
        };

        match self.address_mode() {
            AddressMode::Implied => String::from(""),
            AddressMode::ImpliedAccumulator => String::from("a"),

            AddressMode::ImmediateM | AddressMode::ImmediateX | AddressMode::Immediate8 => {
                format!("#{}", arg())
            }

            AddressMode::Relative
            | AddressMode::RelativeLong
            | AddressMode::DirectPage
            | AddressMode::Absolute
            | AddressMode::AbsoluteLong
            | AddressMode::StackAbsolute => arg(),

            AddressMode::DirectPageIndexedX
            | AddressMode::AbsoluteIndexedX
            | AddressMode::AbsoluteIndexedLong => format!("{},x", arg()),

            AddressMode::DirectPageIndexedY | AddressMode::AbsoluteIndexedY => {
                format!("{},y", arg())
            }

            AddressMode::DirectPageIndirect
            | AddressMode::AbsoluteIndirect
            | AddressMode::PeiDirectPageIndirect => format!("({})", arg()),

            AddressMode::DirectPageIndirectLong | AddressMode::AbsoluteIndirectLong => {
                format!("[{}]", arg())
            }

            AddressMode::DirectPageIndexedIndirect | AddressMode::AbsoluteIndexedIndirect => {
                format!("({},x)", arg())
            }

            AddressMode::DirectPageIndirectIndexed => format!("({}),y", arg()),

            AddressMode::DirectPageIndirectIndexedLong => format!("[{}],y", arg()),

            AddressMode::StackRelative => format!("{},s", arg()),

            AddressMode::StackRelativeIndirectIndexed => format!("({},s),y", arg()),

            AddressMode::Move => {
                let arg = self.argument().unwrap();
                format!("${:02X},${:02X}", arg >> 8, arg & 0xFF)
            }
        }
    }

    /// Return an argument alias (a label or hardware register), if any.
    pub fn argument_alias(&self, analysis: Rc<Analysis>) -> Option<String> {
        match self.absolute_argument() {
            Some(arg) => {
                if let Some(hw_register) = HARDWARE_REGISTERS.get_by_right(&arg) {
                    Some(hw_register.to_string())
                } else if self.is_control() {
                    analysis.label(arg, Some(self.subroutine))
                } else {
                    None
                }
            }
            None => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_instruction_lda() {
        let instruction = Instruction::new(0x8000, 0x8000, 0b0000_0000, 0xA9, 0x1234);
        assert_eq!(instruction.name(), "lda");
        assert_eq!(instruction.operation(), Op::LDA);
        assert_eq!(instruction.address_mode(), AddressMode::ImmediateM);
        assert_eq!(instruction.typ(), InstructionType::Other);
        assert_eq!(instruction.argument_size(), 2);
        assert_eq!(instruction.size(), 3);
        assert_eq!(instruction.argument().unwrap(), 0x1234);
        assert_eq!(instruction.absolute_argument().unwrap(), 0x1234);
        assert_eq!(instruction.argument_string(), "#$1234");
        assert!(!instruction.is_control());
    }

    #[test]
    fn test_instruction_brl() {
        let instruction = Instruction::new(0x8000, 0x8000, 0b0000_0000, 0x82, 0xFFFD);

        assert_eq!(instruction.name(), "brl");
        assert_eq!(instruction.operation(), Op::BRL);
        assert_eq!(instruction.address_mode(), AddressMode::RelativeLong);
        assert_eq!(instruction.argument_size(), 2);
        assert_eq!(instruction.size(), 3);
        assert_eq!(instruction.argument().unwrap(), 0xFFFD);
        assert_eq!(instruction.absolute_argument().unwrap(), 0x8000);
        assert_eq!(instruction.argument_string(), "$FFFD");
        assert_eq!(instruction.typ(), InstructionType::Jump);
        assert!(instruction.is_control());
    }
}
