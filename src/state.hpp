#pragma once

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

  std::size_t sizeA() const { return m ? 1 : 2; }
  std::size_t sizeX() const { return x ? 1 : 2; }

  bool operator==(const State& other) const { return p == other.p; }
};
