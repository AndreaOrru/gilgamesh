#pragma once

#include <map>
#include <string>

#include "types.hpp"

class Instruction;

class Subroutine {
 public:
  Subroutine(u24 pc, std::string label);
  void addInstruction(const Instruction* instruction);

 private:
  u24 pc;
  std::string label;
  std::map<u24, const Instruction*> instructions;
};
