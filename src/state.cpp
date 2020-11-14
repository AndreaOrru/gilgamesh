#include "state.hpp"

using namespace std;

State::State(u8 p) : p{p} {}

State::State(bool m, bool x) : x{x}, m{m} {}

State::State() : State(true, true) {}

std::size_t State::sizeA() const {
  return m ? 1 : 2;
}
std::size_t State::sizeX() const {
  return x ? 1 : 2;
}

void State::set(u8 mask) {
  p |= mask;
}

void State::reset(u8 mask) {
  p &= !mask;
}

bool State::operator==(const State& other) const {
  return p == other.p;
}

void StateChange::set(u8 mask) {
  auto change = State(mask);
  m = change.m ? true : m;
  x = change.x ? true : x;
}

void StateChange::reset(u8 mask) {
  auto change = State(mask);
  m = change.m ? false : m;
  x = change.x ? false : x;
}

void StateChange::applyInference(StateChange inference) {
  if (m.has_value() && (m == inference.m)) {
    m = nullopt;
  }
  if (x.has_value() && (x == inference.x)) {
    x = nullopt;
  }
}

bool StateChange::operator==(const StateChange& other) const {
  return m == other.m && x == other.x;
};

std::size_t hash_value(const StateChange& stateChange) {
  size_t seed = 0;
  boost::hash_combine(seed, stateChange.m);
  boost::hash_combine(seed, stateChange.x);
  return seed;
}
