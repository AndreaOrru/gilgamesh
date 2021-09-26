#pragma once

#include "state.hpp"
#include "utils.hpp"

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

  operator std::string() const {
    std::string s;
    auto m = stateChange.m;
    auto x = stateChange.x;

    if (!m.has_value() && !x.has_value()) {
      return "none";
    }

    if (m.has_value()) {
      s += format("m=%d", *m);
    }

    if (x.has_value()) {
      if (m.has_value()) {
        s += ',';
      }
      s += format("x=%d", *x);
    }

    return s;
  }
};
