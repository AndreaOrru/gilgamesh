#pragma once

#include <boost/container_hash/hash.hpp>
#include <optional>
#include <unordered_set>

#include "types.hpp"

struct State {
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
    u8 p;
  };

  State();
  State(u8 p);
  State(bool m, bool x);

  std::size_t sizeA() const;
  std::size_t sizeX() const;

  void set(u8 mask);
  void reset(u8 mask);

  bool operator==(const State& other) const;
};

struct StateChange {
  std::optional<bool> m;
  std::optional<bool> x;

  void set(u8 mask);
  void reset(u8 mask);
  void applyInference(StateChange inference);

  bool operator==(const StateChange& other) const;
  friend std::size_t hash_value(const StateChange& stateChange);
};

typedef std::unordered_set<StateChange, boost::hash<StateChange>>
    StateChangeSet;
