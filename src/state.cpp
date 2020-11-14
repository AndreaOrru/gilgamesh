#include "state.hpp"

using namespace std;

bool StateChange::operator==(const StateChange& other) const {
  return m == other.m && x == other.x;
};

std::size_t hash_value(const StateChange& stateChange) {
  size_t seed = 0;
  boost::hash_combine(seed, stateChange.m);
  boost::hash_combine(seed, stateChange.x);
  return seed;
}

std::size_t State::sizeA() const {
  return m ? 1 : 2;
}
std::size_t State::sizeX() const {
  return x ? 1 : 2;
}

bool State::operator==(const State& other) const {
  return p == other.p;
}
