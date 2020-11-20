#include "state.hpp"

using namespace std;

/***********
 *  State  *
 ***********/

// Constructors.
State::State() : State(true, true) {}
State::State(u8 p) : p{p} {}
State::State(bool m, bool x) : p{0} {
  this->m = m;
  this->x = x;
}

// Size of A in bytes.
std::size_t State::sizeA() const {
  return m ? 1 : 2;
}

// Size of X in bytes.
std::size_t State::sizeX() const {
  return x ? 1 : 2;
}

// Set bits in P.
void State::set(u8 mask) {
  p |= mask;
}

// Reset bits in P.
void State::reset(u8 mask) {
  p &= ~mask;
}

// Comparison function.
bool State::operator==(const State& other) const {
  return p == other.p;
}

/*****************
 *  StateChange  *
 *****************/

// New empty state change (no changes).
StateChange::StateChange() : StateChange(UnknownReason::Known) {}

// New unknown state change.
StateChange::StateChange(UnknownReason unknownReason)
    : unknownReason{unknownReason} {}

// New state change.
StateChange::StateChange(optional<bool> m, optional<bool> x)
    : m{m}, x{x}, unknownReason{UnknownReason::Known} {}

// Set bits that were changed to 1 in P.
void StateChange::set(u8 mask) {
  State change(mask);
  m = change.m ? true : m;
  x = change.x ? true : x;
}

// Reset bits that were changed to 1 in P.
void StateChange::reset(u8 mask) {
  State change(mask);
  m = change.m ? false : m;
  x = change.x ? false : x;
}

// Return whether there are no state changes.
bool StateChange::isEmpty() const {
  return !unknown() && !m.has_value() && !x.has_value();
}

// Return whether the state change is unknown.
bool StateChange::unknown() const {
  return unknownReason != UnknownReason::Known;
}

// Simplify the state change based on a state inference.
void StateChange::applyInference(StateChange inference) {
  if (m.has_value() && (m == inference.m)) {
    m = nullopt;
  }
  if (x.has_value() && (x == inference.x)) {
    x = nullopt;
  }
}

// Simplify the state change based on a state.
StateChange StateChange::simplify(State state) {
  StateChange stateChange = *this;
  if (state.m == stateChange.m) {
    stateChange.m = nullopt;
  }
  if (state.x == stateChange.x) {
    stateChange.x = nullopt;
  }
  return stateChange;
}

// Hash table utils.
bool StateChange::operator==(const StateChange& other) const {
  return m == other.m && x == other.x;
};
std::size_t hash_value(const StateChange& stateChange) {
  size_t seed = 0;
  boost::hash_combine(seed, stateChange.m);
  boost::hash_combine(seed, stateChange.x);
  return seed;
}
