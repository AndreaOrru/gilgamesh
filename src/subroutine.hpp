#pragma once

#include <map>
#include <optional>
#include <string>

#include "state.hpp"
#include "types.hpp"

class Instruction;

// Structure representing a subroutine.
struct Subroutine {
  // Constructor.
  Subroutine(SubroutinePC pc, std::string label);

  // Add an instruction.
  void addInstruction(Instruction* instruction);

  // Add a state change.
  void addStateChange(InstructionPC pc, StateChange stateChange);

  // Whether the subroutine is unknown because of `reason`.
  bool isUnknownBecauseOf(UnknownReason reason) const;

  // Whether the subroutine saves the CPU state at the beginning.
  bool savesStateInIncipit() const;

  // Return the state changes, simplified given the current state.
  StateChangeSet simplifiedStateChanges(State state);

  // Return the state change caused by an instruction at the given PC, if any.
  std::optional<StateChange> stateChangeForPC(InstructionPC pc) const;

  SubroutinePC pc;    // Program Counter.
  std::string label;  // Label.
  // Map from PC to instructions.
  std::map<InstructionPC, Instruction*> instructions;

  // Known state changes.
  StateChangeMap knownStateChanges;

  // Unknown state changes.
  StateChangeMap unknownStateChanges;
};
