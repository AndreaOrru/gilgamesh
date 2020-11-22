#pragma once

#include "state.hpp"

/**
 * Type of state assertions.
 */
enum class AssertionType {
  None,
  Instruction,
  Subroutine,
};

/**
 * Structure representing a state assertion.
 */
struct Assertion {
  Assertion(AssertionType type, StateChange stateChange = StateChange())
      : type{type}, stateChange{stateChange} {}

  AssertionType type;
  StateChange stateChange;
};
