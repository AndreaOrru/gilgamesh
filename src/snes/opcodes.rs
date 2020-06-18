use enum_map::{enum_map, Enum, EnumMap};
use lazy_static::lazy_static;
use strum_macros::{EnumString, ToString};

/// Memory addressing modes.
#[derive(Copy, Clone, Debug, Enum, Eq, Hash, PartialEq)]
pub enum AddressMode {
    Implied,
    ImmediateM,
    ImmediateX,
    Immediate8,
    Relative,
    RelativeLong,
    DirectPage,
    DirectPageIndexedX,
    DirectPageIndexedY,
    DirectPageIndirect,
    DirectPageIndexedIndirect,
    DirectPageIndirectIndexed,
    DirectPageIndirectLong,
    DirectPageIndirectIndexedLong,
    Absolute,
    AbsoluteIndexedX,
    AbsoluteIndexedY,
    AbsoluteLong,
    AbsoluteIndexedLong,
    StackRelative,
    StackRelativeIndirectIndexed,
    AbsoluteIndirect,
    AbsoluteIndirectLong,
    AbsoluteIndexedIndirect,
    ImpliedAccumulator,
    Move,
    StackAbsolute,
    PeiDirectPageIndirect,
}

// Size of the argument for each addressing mode.
// A value of -1 means the size depends on the state register.
lazy_static! {
    pub static ref ARGUMENT_SIZES: EnumMap<AddressMode, isize> = enum_map! {
        AddressMode::Implied => 0,
        AddressMode::ImmediateM => -1,
        AddressMode::ImmediateX => -1,
        AddressMode::Immediate8 => 1,
        AddressMode::Relative => 1,
        AddressMode::RelativeLong => 2,
        AddressMode::DirectPage => 1,
        AddressMode::DirectPageIndexedX => 1,
        AddressMode::DirectPageIndexedY => 1,
        AddressMode::DirectPageIndirect => 1,
        AddressMode::DirectPageIndexedIndirect => 1,
        AddressMode::DirectPageIndirectIndexed => 1,
        AddressMode::DirectPageIndirectLong => 1,
        AddressMode::DirectPageIndirectIndexedLong => 1,
        AddressMode::Absolute => 2,
        AddressMode::AbsoluteIndexedX => 2,
        AddressMode::AbsoluteIndexedY => 2,
        AddressMode::AbsoluteLong => 3,
        AddressMode::AbsoluteIndexedLong => 3,
        AddressMode::StackRelative => 1,
        AddressMode::StackRelativeIndirectIndexed => 1,
        AddressMode::AbsoluteIndirect => 2,
        AddressMode::AbsoluteIndirectLong => 2,
        AddressMode::AbsoluteIndexedIndirect => 2,
        AddressMode::ImpliedAccumulator => 0,
        AddressMode::Move => 2,
        AddressMode::StackAbsolute => 2,
        AddressMode::PeiDirectPageIndirect => 1,
    };
}

/// 65c816 operations.
#[derive(Copy, Clone, Debug, Enum, EnumString, Eq, PartialEq, Hash, ToString)]
pub enum Op {
    ADC,
    AND,
    ASL,
    BCC,
    BCS,
    BEQ,
    BIT,
    BMI,
    BNE,
    BPL,
    BRA,
    BRK,
    BRL,
    BVC,
    BVS,
    CLC,
    CLD,
    CLI,
    CLV,
    CMP,
    COP,
    CPX,
    CPY,
    DEC,
    DEX,
    DEY,
    EOR,
    INC,
    INX,
    INY,
    JML,
    JMP,
    JSL,
    JSR,
    LDA,
    LDX,
    LDY,
    LSR,
    MVN,
    MVP,
    NOP,
    ORA,
    PEA,
    PEI,
    PER,
    PHA,
    PHB,
    PHD,
    PHK,
    PHP,
    PHX,
    PHY,
    PLA,
    PLB,
    PLD,
    PLP,
    PLX,
    PLY,
    REP,
    ROL,
    ROR,
    RTI,
    RTL,
    RTS,
    SBC,
    SEC,
    SED,
    SEI,
    SEP,
    STA,
    STP,
    STX,
    STY,
    STZ,
    TAX,
    TAY,
    TCD,
    TCS,
    TDC,
    TRB,
    TSB,
    TSC,
    TSX,
    TXA,
    TXS,
    TXY,
    TYA,
    TYX,
    WAI,
    WDM,
    XBA,
    XCE,
}

impl Op {
    /// Return the operation's description.
    pub fn description(self) -> &'static str {
        DESCRIPTIONS[self]
    }
}

// All 65c816 opcodes expressed as a combination of
// operations and addressing modes.
lazy_static! {
    pub static ref OPCODES: Vec<(Op, AddressMode)> = vec![
        (Op::BRK, AddressMode::Immediate8),
        (Op::ORA, AddressMode::DirectPageIndexedIndirect),
        (Op::COP, AddressMode::Immediate8),
        (Op::ORA, AddressMode::StackRelative),
        (Op::TSB, AddressMode::DirectPage),
        (Op::ORA, AddressMode::DirectPage),
        (Op::ASL, AddressMode::DirectPage),
        (Op::ORA, AddressMode::DirectPageIndirectLong),
        (Op::PHP, AddressMode::Implied),
        (Op::ORA, AddressMode::ImmediateM),
        (Op::ASL, AddressMode::ImpliedAccumulator),
        (Op::PHD, AddressMode::Implied),
        (Op::TSB, AddressMode::Absolute),
        (Op::ORA, AddressMode::Absolute),
        (Op::ASL, AddressMode::Absolute),
        (Op::ORA, AddressMode::AbsoluteLong),
        (Op::BPL, AddressMode::Relative),
        (Op::ORA, AddressMode::DirectPageIndirectIndexed),
        (Op::ORA, AddressMode::DirectPageIndirect),
        (Op::ORA, AddressMode::StackRelativeIndirectIndexed),
        (Op::TRB, AddressMode::DirectPage),
        (Op::ORA, AddressMode::DirectPageIndexedX),
        (Op::ASL, AddressMode::DirectPageIndexedX),
        (Op::ORA, AddressMode::DirectPageIndirectIndexedLong),
        (Op::CLC, AddressMode::Implied),
        (Op::ORA, AddressMode::AbsoluteIndexedY),
        (Op::INC, AddressMode::ImpliedAccumulator),
        (Op::TCS, AddressMode::Implied),
        (Op::TRB, AddressMode::Absolute),
        (Op::ORA, AddressMode::AbsoluteIndexedX),
        (Op::ASL, AddressMode::AbsoluteIndexedX),
        (Op::ORA, AddressMode::AbsoluteIndexedLong),
        (Op::JSR, AddressMode::Absolute),
        (Op::AND, AddressMode::DirectPageIndexedIndirect),
        (Op::JSL, AddressMode::AbsoluteLong),
        (Op::AND, AddressMode::StackRelative),
        (Op::BIT, AddressMode::DirectPage),
        (Op::AND, AddressMode::DirectPage),
        (Op::ROL, AddressMode::DirectPage),
        (Op::AND, AddressMode::DirectPageIndirectLong),
        (Op::PLP, AddressMode::Implied),
        (Op::AND, AddressMode::ImmediateM),
        (Op::ROL, AddressMode::ImpliedAccumulator),
        (Op::PLD, AddressMode::Implied),
        (Op::BIT, AddressMode::Absolute),
        (Op::AND, AddressMode::Absolute),
        (Op::ROL, AddressMode::Absolute),
        (Op::AND, AddressMode::AbsoluteLong),
        (Op::BMI, AddressMode::Relative),
        (Op::AND, AddressMode::DirectPageIndirectIndexed),
        (Op::AND, AddressMode::DirectPageIndirect),
        (Op::AND, AddressMode::StackRelativeIndirectIndexed),
        (Op::BIT, AddressMode::DirectPageIndexedX),
        (Op::AND, AddressMode::DirectPageIndexedX),
        (Op::ROL, AddressMode::DirectPageIndexedX),
        (Op::AND, AddressMode::DirectPageIndirectIndexedLong),
        (Op::SEC, AddressMode::Implied),
        (Op::AND, AddressMode::AbsoluteIndexedY),
        (Op::DEC, AddressMode::ImpliedAccumulator),
        (Op::TSC, AddressMode::Implied),
        (Op::BIT, AddressMode::AbsoluteIndexedX),
        (Op::AND, AddressMode::AbsoluteIndexedX),
        (Op::ROL, AddressMode::AbsoluteIndexedX),
        (Op::AND, AddressMode::AbsoluteIndexedLong),
        (Op::RTI, AddressMode::Implied),
        (Op::EOR, AddressMode::DirectPageIndexedIndirect),
        (Op::WDM, AddressMode::Immediate8),
        (Op::EOR, AddressMode::StackRelative),
        (Op::MVP, AddressMode::Move),
        (Op::EOR, AddressMode::DirectPage),
        (Op::LSR, AddressMode::DirectPage),
        (Op::EOR, AddressMode::DirectPageIndirectLong),
        (Op::PHA, AddressMode::Implied),
        (Op::EOR, AddressMode::ImmediateM),
        (Op::LSR, AddressMode::ImpliedAccumulator),
        (Op::PHK, AddressMode::Implied),
        (Op::JMP, AddressMode::Absolute),
        (Op::EOR, AddressMode::Absolute),
        (Op::LSR, AddressMode::Absolute),
        (Op::EOR, AddressMode::AbsoluteLong),
        (Op::BVC, AddressMode::Relative),
        (Op::EOR, AddressMode::DirectPageIndirectIndexed),
        (Op::EOR, AddressMode::DirectPageIndirect),
        (Op::EOR, AddressMode::StackRelativeIndirectIndexed),
        (Op::MVN, AddressMode::Move),
        (Op::EOR, AddressMode::DirectPageIndexedX),
        (Op::LSR, AddressMode::DirectPageIndexedX),
        (Op::EOR, AddressMode::DirectPageIndirectIndexedLong),
        (Op::CLI, AddressMode::Implied),
        (Op::EOR, AddressMode::AbsoluteIndexedY),
        (Op::PHY, AddressMode::Implied),
        (Op::TCD, AddressMode::Implied),
        (Op::JML, AddressMode::AbsoluteLong),
        (Op::EOR, AddressMode::AbsoluteIndexedX),
        (Op::LSR, AddressMode::AbsoluteIndexedX),
        (Op::EOR, AddressMode::AbsoluteIndexedLong),
        (Op::RTS, AddressMode::Implied),
        (Op::ADC, AddressMode::DirectPageIndexedIndirect),
        (Op::PER, AddressMode::RelativeLong),
        (Op::ADC, AddressMode::StackRelative),
        (Op::STZ, AddressMode::DirectPage),
        (Op::ADC, AddressMode::DirectPage),
        (Op::ROR, AddressMode::DirectPage),
        (Op::ADC, AddressMode::DirectPageIndirectLong),
        (Op::PLA, AddressMode::Implied),
        (Op::ADC, AddressMode::ImmediateM),
        (Op::ROR, AddressMode::ImpliedAccumulator),
        (Op::RTL, AddressMode::Implied),
        (Op::JMP, AddressMode::AbsoluteIndirect),
        (Op::ADC, AddressMode::Absolute),
        (Op::ROR, AddressMode::Absolute),
        (Op::ADC, AddressMode::AbsoluteLong),
        (Op::BVS, AddressMode::Relative),
        (Op::ADC, AddressMode::DirectPageIndirectIndexed),
        (Op::ADC, AddressMode::DirectPageIndirect),
        (Op::ADC, AddressMode::StackRelativeIndirectIndexed),
        (Op::STZ, AddressMode::DirectPageIndexedX),
        (Op::ADC, AddressMode::DirectPageIndexedX),
        (Op::ROR, AddressMode::DirectPageIndexedX),
        (Op::ADC, AddressMode::DirectPageIndirectIndexedLong),
        (Op::SEI, AddressMode::Implied),
        (Op::ADC, AddressMode::AbsoluteIndexedY),
        (Op::PLY, AddressMode::Implied),
        (Op::TDC, AddressMode::Implied),
        (Op::JMP, AddressMode::AbsoluteIndexedIndirect),
        (Op::ADC, AddressMode::AbsoluteIndexedX),
        (Op::ROR, AddressMode::AbsoluteIndexedX),
        (Op::ADC, AddressMode::AbsoluteIndexedLong),
        (Op::BRA, AddressMode::Relative),
        (Op::STA, AddressMode::DirectPageIndexedIndirect),
        (Op::BRL, AddressMode::RelativeLong),
        (Op::STA, AddressMode::StackRelative),
        (Op::STY, AddressMode::DirectPage),
        (Op::STA, AddressMode::DirectPage),
        (Op::STX, AddressMode::DirectPage),
        (Op::STA, AddressMode::DirectPageIndirectLong),
        (Op::DEY, AddressMode::Implied),
        (Op::BIT, AddressMode::ImmediateM),
        (Op::TXA, AddressMode::Implied),
        (Op::PHB, AddressMode::Implied),
        (Op::STY, AddressMode::Absolute),
        (Op::STA, AddressMode::Absolute),
        (Op::STX, AddressMode::Absolute),
        (Op::STA, AddressMode::AbsoluteLong),
        (Op::BCC, AddressMode::Relative),
        (Op::STA, AddressMode::DirectPageIndirectIndexed),
        (Op::STA, AddressMode::DirectPageIndirect),
        (Op::STA, AddressMode::StackRelativeIndirectIndexed),
        (Op::STY, AddressMode::DirectPageIndexedX),
        (Op::STA, AddressMode::DirectPageIndexedX),
        (Op::STX, AddressMode::DirectPageIndexedY),
        (Op::STA, AddressMode::DirectPageIndirectIndexedLong),
        (Op::TYA, AddressMode::Implied),
        (Op::STA, AddressMode::AbsoluteIndexedY),
        (Op::TXS, AddressMode::Implied),
        (Op::TXY, AddressMode::Implied),
        (Op::STZ, AddressMode::Absolute),
        (Op::STA, AddressMode::AbsoluteIndexedX),
        (Op::STZ, AddressMode::AbsoluteIndexedX),
        (Op::STA, AddressMode::AbsoluteIndexedLong),
        (Op::LDY, AddressMode::ImmediateX),
        (Op::LDA, AddressMode::DirectPageIndexedIndirect),
        (Op::LDX, AddressMode::ImmediateX),
        (Op::LDA, AddressMode::StackRelative),
        (Op::LDY, AddressMode::DirectPage),
        (Op::LDA, AddressMode::DirectPage),
        (Op::LDX, AddressMode::DirectPage),
        (Op::LDA, AddressMode::DirectPageIndirectLong),
        (Op::TAY, AddressMode::Implied),
        (Op::LDA, AddressMode::ImmediateM),
        (Op::TAX, AddressMode::Implied),
        (Op::PLB, AddressMode::Implied),
        (Op::LDY, AddressMode::Absolute),
        (Op::LDA, AddressMode::Absolute),
        (Op::LDX, AddressMode::Absolute),
        (Op::LDA, AddressMode::AbsoluteLong),
        (Op::BCS, AddressMode::Relative),
        (Op::LDA, AddressMode::DirectPageIndirectIndexed),
        (Op::LDA, AddressMode::DirectPageIndirect),
        (Op::LDA, AddressMode::StackRelativeIndirectIndexed),
        (Op::LDY, AddressMode::DirectPageIndexedX),
        (Op::LDA, AddressMode::DirectPageIndexedX),
        (Op::LDX, AddressMode::DirectPageIndexedY),
        (Op::LDA, AddressMode::DirectPageIndirectIndexedLong),
        (Op::CLV, AddressMode::Implied),
        (Op::LDA, AddressMode::AbsoluteIndexedY),
        (Op::TSX, AddressMode::Implied),
        (Op::TYX, AddressMode::Implied),
        (Op::LDY, AddressMode::AbsoluteIndexedX),
        (Op::LDA, AddressMode::AbsoluteIndexedX),
        (Op::LDX, AddressMode::AbsoluteIndexedY),
        (Op::LDA, AddressMode::AbsoluteIndexedLong),
        (Op::CPY, AddressMode::ImmediateX),
        (Op::CMP, AddressMode::DirectPageIndexedIndirect),
        (Op::REP, AddressMode::Immediate8),
        (Op::CMP, AddressMode::StackRelative),
        (Op::CPY, AddressMode::DirectPage),
        (Op::CMP, AddressMode::DirectPage),
        (Op::DEC, AddressMode::DirectPage),
        (Op::CMP, AddressMode::DirectPageIndirectLong),
        (Op::INY, AddressMode::Implied),
        (Op::CMP, AddressMode::ImmediateM),
        (Op::DEX, AddressMode::Implied),
        (Op::WAI, AddressMode::Implied),
        (Op::CPY, AddressMode::Absolute),
        (Op::CMP, AddressMode::Absolute),
        (Op::DEC, AddressMode::Absolute),
        (Op::CMP, AddressMode::AbsoluteLong),
        (Op::BNE, AddressMode::Relative),
        (Op::CMP, AddressMode::DirectPageIndirectIndexed),
        (Op::CMP, AddressMode::DirectPageIndirect),
        (Op::CMP, AddressMode::DirectPageIndirect),
        (Op::PEI, AddressMode::PeiDirectPageIndirect),
        (Op::CMP, AddressMode::DirectPageIndexedX),
        (Op::DEC, AddressMode::DirectPageIndexedX),
        (Op::CMP, AddressMode::DirectPageIndirectIndexedLong),
        (Op::CLD, AddressMode::Implied),
        (Op::CMP, AddressMode::AbsoluteIndexedY),
        (Op::PHX, AddressMode::Implied),
        (Op::STP, AddressMode::Implied),
        (Op::JML, AddressMode::AbsoluteIndirectLong),
        (Op::CMP, AddressMode::AbsoluteIndexedX),
        (Op::DEC, AddressMode::AbsoluteIndexedX),
        (Op::CMP, AddressMode::AbsoluteIndexedLong),
        (Op::CPX, AddressMode::ImmediateX),
        (Op::SBC, AddressMode::DirectPageIndexedIndirect),
        (Op::SEP, AddressMode::Immediate8),
        (Op::SBC, AddressMode::StackRelative),
        (Op::CPX, AddressMode::DirectPage),
        (Op::SBC, AddressMode::DirectPage),
        (Op::INC, AddressMode::DirectPage),
        (Op::SBC, AddressMode::DirectPageIndirectLong),
        (Op::INX, AddressMode::Implied),
        (Op::SBC, AddressMode::ImmediateM),
        (Op::NOP, AddressMode::Implied),
        (Op::XBA, AddressMode::Implied),
        (Op::CPX, AddressMode::Absolute),
        (Op::SBC, AddressMode::Absolute),
        (Op::INC, AddressMode::Absolute),
        (Op::SBC, AddressMode::AbsoluteLong),
        (Op::BEQ, AddressMode::Relative),
        (Op::SBC, AddressMode::DirectPageIndirectIndexed),
        (Op::SBC, AddressMode::DirectPageIndirect),
        (Op::SBC, AddressMode::StackRelativeIndirectIndexed),
        (Op::PEA, AddressMode::StackAbsolute),
        (Op::SBC, AddressMode::DirectPageIndexedX),
        (Op::INC, AddressMode::DirectPageIndexedX),
        (Op::SBC, AddressMode::DirectPageIndirectIndexedLong),
        (Op::SED, AddressMode::Implied),
        (Op::SBC, AddressMode::AbsoluteIndexedY),
        (Op::PLX, AddressMode::Implied),
        (Op::XCE, AddressMode::Implied),
        (Op::JSR, AddressMode::AbsoluteIndexedIndirect),
        (Op::SBC, AddressMode::AbsoluteIndexedX),
        (Op::INC, AddressMode::AbsoluteIndexedX),
        (Op::SBC, AddressMode::AbsoluteIndexedLong),
    ];
}

// Human-readable description of each operation.
lazy_static! {
    pub static ref DESCRIPTIONS: EnumMap<Op, &'static str> = enum_map! {
        Op::ADC => "Add With Carry",
        Op::AND => "AND Accumulator With Memory",
        Op::ASL => "Accumulator or Memory Shift Left",
        Op::BCC => "Branch if Carry Clear",
        Op::BCS => "Branch if Carry Set",
        Op::BEQ => "Branch if Equal",
        Op::BIT => "Test Bits",
        Op::BMI => "Branch if Minus",
        Op::BNE => "Branch if Not Equal",
        Op::BPL => "Branch if Plus",
        Op::BRA => "Branch Always",
        Op::BRK => "Break",
        Op::BRL => "Branch Long Always",
        Op::BVC => "Branch if Overflow Clear",
        Op::BVS => "Branch if Overflow Set",
        Op::CLC => "Clear Carry",
        Op::CLD => "Clear Decimal Mode Flag",
        Op::CLI => "Clear Interrupt Disable Flag",
        Op::CLV => "Clear Overflow Flag",
        Op::CMP => "Compare Accumulator With Memory",
        Op::COP => "Co-Processor Enable",
        Op::CPX => "Compare Index Register X with Memory",
        Op::CPY => "Compare Index Register Y with Memory",
        Op::DEC => "Decrement",
        Op::DEX => "Decrement Index Register X",
        Op::DEY => "Decrement Index Register Y",
        Op::EOR => "Exclusive-OR Accumulator with Memory",
        Op::INC => "Increment",
        Op::INX => "Increment Index Register X",
        Op::INY => "Increment Index Register Y",
        Op::JML => "Jump Long",
        Op::JMP => "Jump",
        Op::JSL => "Jump to Subroutine Long",
        Op::JSR => "Jump to Subroutine",
        Op::LDA => "Load Accumulator from Memory",
        Op::LDX => "Load Index Register X from Memory",
        Op::LDY => "Load Index Register Y from Memory",
        Op::LSR => "Logical Shift Memory or Accumulator Right",
        Op::MVN => "Block Move Negative",
        Op::MVP => "Block Move Positive",
        Op::NOP => "No Operation",
        Op::ORA => "OR Accumulator with Memory",
        Op::PEA => "Push Effective Absolute Address",
        Op::PEI => "Push Effective Indirect Address",
        Op::PER => "Push Effective PC Relative Indirect Address",
        Op::PHA => "Push Accumulator",
        Op::PHB => "Push Data Bank Register",
        Op::PHD => "Push Direct Page Register",
        Op::PHK => "Push Program Bank Register",
        Op::PHP => "Push Processor Status Register",
        Op::PHX => "Push Index Register X",
        Op::PHY => "Push Index Register Y",
        Op::PLA => "Pull Accumulator",
        Op::PLB => "Pull Data Bank Register",
        Op::PLD => "Pull Direct Page Register",
        Op::PLP => "Pull Processor Status Register",
        Op::PLX => "Pull Index Register X",
        Op::PLY => "Pull Index Register Y",
        Op::REP => "Reset Processor Status Bits",
        Op::ROL => "Rotate Memory or Accumulator Left",
        Op::ROR => "Rotate Memory or Accumulator Right",
        Op::RTI => "Return from Interrupt",
        Op::RTL => "Return from Subroutine Long",
        Op::RTS => "Return from Subroutine",
        Op::SBC => "Subtract with Borrow from Accumulator",
        Op::SEC => "Set Carry Flag",
        Op::SED => "Set Decimal Flag",
        Op::SEI => "Set Interrupt Disable Flag",
        Op::SEP => "Set Processor Status Bits",
        Op::STA => "Store Accumulator to Memory",
        Op::STP => "Stop Processor",
        Op::STX => "Store Index Register X to Memory",
        Op::STY => "Store Index Register Y to Memory",
        Op::STZ => "Store Zero to Memory",
        Op::TAX => "Transfer Accumulator to Index Register X",
        Op::TAY => "Transfer Accumulator to Index Register Y",
        Op::TCD => "Transfer 16-bit Accumulator to Direct Page Register",
        Op::TCS => "Transfer 16-bit Accumulator to Stack Pointer",
        Op::TDC => "Transfer Direct Page Register to 16-bit Accumulator",
        Op::TRB => "Test and Reset Memory Bits Against Accumulator",
        Op::TSB => "Test and Set Memory Bits Against Accumulator",
        Op::TSC => "Transfer Stack Pointer to 16-bit Accumulator",
        Op::TSX => "Transfer Stack Pointer to Index Register X",
        Op::TXA => "Transfer Index Register X to Accumulator",
        Op::TXS => "Transfer Index Register X to Stack Pointer",
        Op::TXY => "Transfer Index Register X to Index Register Y",
        Op::TYA => "Transfer Index Register Y to Accumulator",
        Op::TYX => "Transfer Index Register Y to Index Register X",
        Op::WAI => "Wait for Interrupt",
        Op::WDM => "Reserved for Future Expansion",
        Op::XBA => "Exchange B and A 8-bit Accumulators",
        Op::XCE => "Exchange Carry and Emulation Flags",
    };
}
