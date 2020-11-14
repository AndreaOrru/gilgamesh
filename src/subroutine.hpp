#pragma once

#include <map>

#include "types.hpp"

class Instruction;

class Subroutine {
 private:
  u24 pc;
  std::map<u24, const Instruction*> instructions;

 public:
  void addInstruction(const Instruction* instruction);
};
