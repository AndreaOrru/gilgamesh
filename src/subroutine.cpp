#include "subroutine.hpp"

#include "instruction.hpp"

// Constructor.
Subroutine::Subroutine(u24 pc, std::string label) : pc{pc}, label{label} {}

// Add an instruction.
void Subroutine::addInstruction(Instruction* instruction) {
  instructions[instruction->pc] = instruction;
}

// Add a state change.
void Subroutine::addStateChange(StateChange stateChange) {
  if (stateChange.unknown()) {
    unknownStateChanges.insert(stateChange);
  } else {
    knownStateChanges.insert(stateChange);
  }
}
