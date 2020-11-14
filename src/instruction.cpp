#include "instruction.hpp"
#include "analysis.hpp"
#include "opcodes.hpp"
#include "utils.hpp"

using namespace std;

Instruction::Instruction(Analysis* analysis,
                         u24 pc,
                         u24 subroutine,
                         u8 opcode,
                         u24 argument,
                         State state)
    : pc{pc},
      subroutine{subroutine},
      analysis{analysis},
      opcode{opcode},
      _argument{argument},
      state{state} {}

bool Instruction::operator==(const Instruction& other) const {
  return pc == other.pc && subroutine == other.subroutine &&
         state == other.state;
}

size_t hash_value(const Instruction& instruction) {
  size_t seed = 0;
  boost::hash_combine(seed, instruction.pc);
  boost::hash_combine(seed, instruction.subroutine);
  boost::hash_combine(seed, instruction.state.p);
  return seed;
}

string Instruction::name() const {
  return OPCODE_NAMES[operation()];
}

Op Instruction::operation() const {
  return OPCODE_TABLE[opcode].first;
}

AddressMode Instruction::addressMode() const {
  return OPCODE_TABLE[opcode].second;
}

InstructionType Instruction::type() const {
  switch (operation()) {
    case Op::JSR:
    case Op::JSL:
      return InstructionType::Call;

    case Op::JMP:
    case Op::JML:
    case Op::BRA:
    case Op::BRL:
      return InstructionType::Jump;

    case Op::RTS:
    case Op::RTL:
    case Op::RTI:
      return InstructionType::Return;

    case Op::BRK:
      return InstructionType::Interrupt;

    case Op::SEP:
    case Op::REP:
      return InstructionType::SepRep;

    case Op::PLA:
    case Op::PLB:
    case Op::PLD:
    case Op::PLP:
    case Op::PLX:
    case Op::PLY:
      return InstructionType::Pop;

    case Op::PEA:
    case Op::PEI:
    case Op::PER:
    case Op::PHA:
    case Op::PHB:
    case Op::PHD:
    case Op::PHK:
    case Op::PHP:
    case Op::PHX:
    case Op::PHY:
      return InstructionType::Push;

    case Op::BCC:
    case Op::BCS:
    case Op::BEQ:
    case Op::BMI:
    case Op::BNE:
    case Op::BPL:
    case Op::BVC:
    case Op::BVS:
      return InstructionType::Branch;

    default:
      return InstructionType::Other;
  }
}

bool Instruction::isControl() const {
  switch (type()) {
    case InstructionType::Branch:
    case InstructionType::Call:
    case InstructionType::Jump:
    case InstructionType::Return:
    case InstructionType::Interrupt:
      return true;

    default:
      return false;
  }
}

size_t Instruction::size() const {
  return argumentSize() + 1;
}

size_t Instruction::argumentSize() const {
  if (auto size = ARGUMENT_SIZES[addressMode()]) {
    return *size;
  }

  switch (addressMode()) {
    case AddressMode::ImmediateM:
      return state.sizeA();
    case AddressMode::ImmediateX:
      return state.sizeX();
    default:
      __builtin_unreachable();
  }
}

optional<u24> Instruction::argument() const {
  switch (argumentSize()) {
    case 0:
      return {};
    case 1:
      return _argument & 0xFF;
    case 2:
      return _argument & 0xFFFF;
    case 3:
      return _argument & 0xFFFFFF;
  }
  __builtin_unreachable();
}

optional<u24> Instruction::absoluteArgument() const {
  auto arg = argument();
  if (!arg.has_value()) {
    return {};
  }

  switch (addressMode()) {
    case AddressMode::ImmediateM:
    case AddressMode::ImmediateX:
    case AddressMode::Immediate8:
    case AddressMode::AbsoluteLong:
      return arg;

    case AddressMode::Absolute:
      return isControl() ? optional((pc & 0xFF0000) | *arg) : nullopt;

    case AddressMode::Relative:
      return pc + size() + ((i8)*arg);
    case AddressMode::RelativeLong:
      return pc + size() + ((i16)*arg);

    default:
      return {};
  };
};

string Instruction::argumentString() const {
  auto arg = argument();
  auto sz = argumentSize();

  switch (addressMode()) {
    default:
    case Implied:
      return "";

    case ImpliedAccumulator:
      return "a";

    case ImmediateM:
    case ImmediateX:
    case Immediate8:
      return format("#$%0" + to_string(sz * 2) + "X", *arg);

    case Relative:
    case RelativeLong:
    case DirectPage:
    case Absolute:
    case AbsoluteLong:
    case StackAbsolute:
      return format("$%0" + to_string(sz * 2) + "X", *arg);

    case DirectPageIndexedX:
    case AbsoluteIndexedX:
    case AbsoluteIndexedLong:
      return format("$%0" + to_string(sz * 2) + "X,x", *arg);

    case DirectPageIndexedY:
    case AbsoluteIndexedY:
      return format("$%0" + to_string(sz * 2) + "X,y", *arg);

    case DirectPageIndirect:
    case AbsoluteIndirect:
    case PeiDirectPageIndirect:
      return format("($%0" + to_string(sz * 2) + "X)", *arg);

    case DirectPageIndirectLong:
    case AbsoluteIndirectLong:
      return format("[$%0" + to_string(sz * 2) + "X]", *arg);

    case DirectPageIndexedIndirect:
    case AbsoluteIndexedIndirect:
      return format("($%0" + to_string(sz * 2) + "X,x)", *arg);

    case DirectPageIndirectIndexed:
      return format("($%0" + to_string(sz * 2) + "X),y", *arg);

    case DirectPageIndirectIndexedLong:
      return format("[$%0" + to_string(sz * 2) + "X],y", *arg);

    case StackRelative:
      return format("$%02X,s", *arg);

    case StackRelativeIndirectIndexed:
      return format("($%02X,s),y", *arg);

    case Move:
      return format("%02X,%02X", *arg >> 8, *arg & 0xFF);
  };
}

string Instruction::toString() const {
  string s;

  s += name();
  s += " ";
  s += argumentString();

  return s;
}
