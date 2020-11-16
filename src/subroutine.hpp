#pragma once

#include <map>
#include <string>

#include "state.hpp"
#include "types.hpp"

class Instruction;

class Subroutine {
 public:
  Subroutine(u24 pc, std::string label);          // Constructor.
  void addInstruction(Instruction* instruction);  // Add an instruction.
  void addStateChange(StateChange stateChange);   // Add a state change.

  u24 pc;             // Program Counter.
  std::string label;  // Label.
  // Map from PC to instructions.
  std::map<u24, Instruction*> instructions;

  StateChangeSet knownStateChanges;    // Known state changes.
  StateChangeSet unknownStateChanges;  // Unknown state changes.
};
