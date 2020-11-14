#include "subroutine.hpp"

#include "instruction.hpp"

Subroutine::Subroutine(u24 pc, std::string label) : pc{pc}, label{label} {}

void Subroutine::addInstruction(Instruction* instruction) {
  instructions[instruction->pc] = instruction;
}

void Subroutine::addStateChange(StateChange stateChange) {
  if (stateChange.unknown()) {
    unknownStateChanges.insert(stateChange);
  } else {
    knownStateChanges.insert(stateChange);
  }
}
