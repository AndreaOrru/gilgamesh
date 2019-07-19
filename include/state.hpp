#pragma once
#include "types.hpp"
#include <boost/container_hash/hash.hpp>

struct StateChange {
  std::optional<bool> m;
  std::optional<bool> x;

  friend bool operator==(const StateChange &lhs, const StateChange &rhs) {
    return lhs.m == rhs.m && lhs.x == rhs.x;
  }

  friend size_t hash_value(const StateChange &state_change) {
    size_t seed = 0;
    boost::hash_combine(seed, state_change.m);
    boost::hash_combine(seed, state_change.x);
    return seed;
  }
};

struct State {
  u24 pc = 0;

  union {
    struct {
      bool c : 1;
      bool z : 1;
      bool i : 1;
      bool d : 1;
      bool x : 1;
      bool m : 1;
      bool v : 1;
      bool n : 1;
    };
    u8 p = 0x30; // m = 1, x = 1
  };
};
