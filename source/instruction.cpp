#include "instruction.hpp"
#include <fmt/core.h>

Instruction::Instruction(State state, u8 opcode, u24 argument)
    : state(state), opcode(opcode), _argument(argument){};

std::string Instruction::name() const { return operation_names[operation()]; };

Operation Instruction::operation() const { return opcode_table[opcode].first; }

AddressMode Instruction::addressMode() const {
  return opcode_table[opcode].second;
}

size_t Instruction::argumentSize() const {
  auto address_mode = addressMode();
  auto size = argument_size_table[address_mode];
  if (size.has_value()) {
    return *size;
  }

  if (address_mode == IMMEDIATE_M) {
    return state.m ? 1 : 2;
  } else if (address_mode == IMMEDIATE_X) {
    return state.x ? 1 : 2;
  }

  assert(false);
}

size_t Instruction::size() const { return argumentSize() + 1; }

std::optional<u24> Instruction::argument() const {
  switch (argumentSize()) {
  case 1:
    return _argument & 0xFF;
  case 2:
    return _argument & 0xFFFF;
  case 3:
    return _argument & 0xFFFFFF;
  default:
    return {};
  }
}

std::optional<u24> Instruction::absoluteArgument() const {
  auto mode = addressMode();
  auto arg = argument();

  if (mode == IMMEDIATE_M || mode == IMMEDIATE_X || mode == IMMEDIATE_8 ||
      mode == ABSOLUTE_LONG) {
    return arg;
  } else if (mode == ABSOLUTE && isControl()) {
    return (state.pc & 0xFF0000) | *arg;
  } else if (mode == RELATIVE) {
    return state.pc + size() + s8(*arg);
  } else if (mode == RELATIVE_LONG) {
    return state.pc + size() + s16(*arg);
  }

  return {};
}

bool Instruction::isBranch() const {
  auto op = operation();
  return op == BCC || op == BCS || op == BEQ || op == BMI || op == BNE ||
         op == BPL || op == BVC || op == BVS;
}

bool Instruction::isCall() const {
  auto op = operation();
  return op == JSL || op == JSR;
}

bool Instruction::isJump() const {
  auto op = operation();
  return op == BRA || op == BRL || op == JMP || op == JML;
}

bool Instruction::isReturn() const {
  auto op = operation();
  return op == RTI || op == RTL || op == RTS;
}

bool Instruction::isSepRep() const {
  auto op = operation();
  return op == SEP || op == REP;
}

bool Instruction::isControl() const {
  return operation() == BRK || isBranch() || isCall() || isJump() || isReturn();
}

std::string Instruction::toString() const {
  auto name = this->name();
  auto argument = argumentString();

  if (argument.size() == 0) {
    return name;
  } else {
    return name + " " + argument;
  }
}

std::string Instruction::argumentString() const {
  auto arg = argument();
  int size = argumentSize();

  switch (addressMode()) {
  default:
  case IMPLIED:
    return "";

  case IMPLIED_ACCUMULATOR:
    return "a";

  case IMMEDIATE_M:
  case IMMEDIATE_X:
  case IMMEDIATE_8:
    return fmt::format("#${:0{}X}", *arg, size * 2);

  case RELATIVE:
  case RELATIVE_LONG:
  case DIRECT_PAGE:
  case ABSOLUTE:
  case ABSOLUTE_LONG:
  case STACK_ABSOLUTE:
    return fmt::format("${:0{}X}", *arg, size * 2);

  case DIRECT_PAGE_INDEXED_X:
  case ABSOLUTE_INDEXED_X:
  case ABSOLUTE_INDEXED_LONG:
    return fmt::format("${:0{}X},x", *arg, size * 2);

  case DIRECT_PAGE_INDEXED_Y:
  case ABSOLUTE_INDEXED_Y:
    return fmt::format("${:0{}X},y", *arg, size * 2);

  case DIRECT_PAGE_INDIRECT:
  case ABSOLUTE_INDIRECT:
  case PEI_DIRECT_PAGE_INDIRECT:
    return fmt::format("(${:0{}X})", *arg, size * 2);

  case DIRECT_PAGE_INDIRECT_LONG:
  case ABSOLUTE_INDIRECT_LONG:
    return fmt::format("[${:0{}X}]", *arg, size * 2);

  case DIRECT_PAGE_INDEXED_INDIRECT:
  case ABSOLUTE_INDEXED_INDIRECT:
    return fmt::format("(${:0{}X},x)", *arg, size * 2);

  case DIRECT_PAGE_INDIRECT_INDEXED:
    return fmt::format("(${:0{}X}),y", *arg, size * 2);

  case DIRECT_PAGE_INDIRECT_INDEXED_LONG:
    return fmt::format("[${:0{}X}],y", *arg, size * 2);

  case STACK_RELATIVE:
    return fmt::format("${:02X},s", *arg);

  case STACK_RELATIVE_INDIRECT_INDEXED:
    return fmt::format("(${:02X},s),y", *arg);

  case MOVE:
    return fmt::format("{:02X},{:02X}", *arg & 0xFF, *arg >> 8);
  }
}
