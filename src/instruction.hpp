#pragma once

#include <optional>
#include <string>

#include "opcodes.hpp"
#include "state.hpp"
#include "types.hpp"

class Subroutine;

enum class InstructionType {
  Branch,
  Call,
  Interrupt,
  Other,
  Jump,
  Pop,
  Push,
  Return,
  SepRep,
};

class Instruction {
 public:
  Instruction(u24 pc,
              u8 opcode,
              u24 argument,
              State state,
              Subroutine* subroutine);
  std::string name() const;
  Op opcode() const;
  AddressMode addressMode() const;
  InstructionType type() const;
  bool isControl() const;
  size_t size() const;
  size_t argumentSize() const;
  std::optional<u24> argument() const;
  std::optional<u24> absoluteArgument() const;
  std::string argumentString() const;

 private:
  u24 pc;
  u8 _opcode;
  u24 _argument;
  State state;
  Subroutine* subroutine;
};
