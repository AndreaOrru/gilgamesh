#include "subroutine.hpp"

#include "instruction.hpp"

using namespace std;

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

// Return true if this subroutine is responsible for the unknown state,
// false if the unknown state is due to one of the subroutine it calls.
bool Subroutine::isResponsibleForUnknown() const {
  for (auto& [pc, stateChange] : unknownStateChanges) {
    if (stateChange.unknownReason != UnknownReason::Unknown) {
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

// Return the state change caused by an instruction at the given PC, if any.
optional<StateChange> Subroutine::stateChangeForPC(InstructionPC pc) const {
  auto knownSearch = knownStateChanges.find(pc);
  if (knownSearch != knownStateChanges.end()) {
    return knownSearch->second;
  }

  auto unknownSearch = unknownStateChanges.find(pc);
  if (unknownSearch != unknownStateChanges.end()) {
    return unknownSearch->second;
  }

  return nullopt;
}
