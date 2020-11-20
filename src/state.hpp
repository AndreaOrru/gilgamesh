#pragma once

#include <optional>
#include <unordered_map>

#include "types.hpp"

/**
 * SNES state register (P).
 */
struct State {
  union {
    struct {
      bool c : 1;  // Carry flag.
      bool z : 1;  // Zero flag.
      bool i : 1;  // Interrupt flag.
      bool d : 1;  // Decimal flag.
      bool x : 1;  // Index size flag.
      bool m : 1;  // Accumulator size flag.
      bool v : 1;  // Overflow flag.
      bool n : 1;  // Negative flag.
    };
    u8 p;  // State register.
  };

  // Constructors.
  State();
  State(u8 p);
  State(bool m, bool x);

  std::size_t sizeA() const;  // Size of A in bytes.
  std::size_t sizeX() const;  // Size of X in bytes.

  void set(u8 mask);    // Set bits in P.
  void reset(u8 mask);  // Reset bits in P.

  // Comparison function.
  bool operator==(const State& other) const;
};

/**
 * Possible reasons why a state change is unknown.
 */
enum class UnknownReason {
  Known,
  Unknown,
  SuspectInstruction,
  MultipleReturnStates,
  IndirectJump,
  StackManipulation,
  Recursion,
  MutableCode,
};

/**
 * State change caused by the execution of a subroutine.
 */
struct StateChange {
  // New empty state change (no changes).
  StateChange();
  // New unknown state change.
  StateChange(UnknownReason unknownReason);
  // New state change.
  StateChange(std::optional<bool> m, std::optional<bool> x);

  void set(u8 mask);     // Set bits that were changed to 1 in P.
  void reset(u8 mask);   // Reset bits that were changed to 1 in P.
  bool isEmpty() const;  // Return whether there are no state changes.
  bool unknown() const;  // Return whether the state is unknown.
  // Simplify the state change based on a state inference.
  void applyInference(StateChange inference);

  // Hash table utils.
  bool operator==(const StateChange& other) const;
  friend std::size_t hash_value(const StateChange& stateChange);

  std::optional<bool> m;        // Accumulator size flag.
  std::optional<bool> x;        // Index size flag.
  UnknownReason unknownReason;  // Reason for state being unknown, if any.
};

// Map from InstructionPC to StateChange.
typedef std::unordered_map<InstructionPC, StateChange> StateChangeMap;
