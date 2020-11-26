#pragma once

#include "state.hpp"

/**
 * Type of state assertions.
 */
enum class AssertionType {
  Instruction,
  Subroutine,
};

/**
 * Structure representing a state assertion.
 */
struct Assertion {
  Assertion(AssertionType type = AssertionType::Instruction,
            StateChange stateChange = StateChange())
      : type{type}, stateChange{stateChange} {}

  AssertionType type;
  StateChange stateChange;

  template <class Archive>
  void serialize(Archive& ar, const unsigned int) {
    ar& type;
    ar& stateChange;
  }
};
