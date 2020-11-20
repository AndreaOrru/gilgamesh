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

// Whether the subroutine is unknown because of `reason`.
bool Subroutine::isUnknownBecauseOf(UnknownReason reason) const {
  for (auto& [pc, stateChange] : unknownStateChanges) {
    if (stateChange.unknownReason == reason) {
      return true;
    }
  }
  return false;
}

// Whether the subroutine saves the CPU state at the beginning.
bool Subroutine::savesStateInIncipit() const {
  for (auto& [pc, instruction] : instructions) {
    if (instruction->operation() == Op::PHP) {
      return true;
    } else if (instruction->isSepRep() || instruction->isControl()) {
      return false;
    }
  }
  return false;
}

// Return the state changes, simplified given the current state.
StateChangeSet Subroutine::simplifiedStateChanges(State state) {
  StateChangeSet stateChanges;
  for (auto& [pc, stateChange] : knownStateChanges) {
    stateChanges.insert(stateChange.simplify(state));
  }
  return stateChanges;
}
