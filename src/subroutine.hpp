#pragma once

#include <map>
#include <string>

#include "state.hpp"
#include "types.hpp"

class Instruction;

class Subroutine {
 public:
  Subroutine(u24 pc, std::string label);
  void addInstruction(Instruction* instruction);

  u24 pc;
  std::string label;
  std::map<u24, Instruction*> instructions;
  StateChangeSet stateChanges;
};
