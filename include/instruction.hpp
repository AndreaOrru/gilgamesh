#pragma once
#include "opcode.hpp"
#include "state.hpp"
#include <string>

class Instruction {
public:
  State state;
  u8 opcode;

  Instruction(State state, u8 opcode, u24 argument);

  std::string name() const;
  Operation operation() const;
  AddressMode addressMode() const;
  size_t argumentSize() const;
  size_t size() const;
  std::optional<u24> argument() const;
  std::optional<u24> absoluteArgument() const;
  std::string toString() const;

  bool isBranch() const;
  bool isCall() const;
  bool isControl() const;
  bool isJump() const;
  bool isReturn() const;
  bool isSepRep() const;

private:
  u24 _argument;

  std::string argumentString() const;
};
