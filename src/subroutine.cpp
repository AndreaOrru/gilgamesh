#include "subroutine.hpp"

#include "instruction.hpp"

// Constructor.
Subroutine::Subroutine(SubroutinePC pc, std::string label)
    : pc{pc}, label{label} {}

// Add an instruction.
void Subroutine::addInstruction(Instruction* instruction) {
  instructions[instruction->pc] = instruction;
}

// Add a state change.
void Subroutine::addStateChange(SubroutinePC pc, StateChange stateChange) {
  if (stateChange.unknown()) {
    unknownStateChanges[pc] = stateChange;
  } else {
    knownStateChanges[pc] = stateChange;
  }
}
