#pragma once

#include <vector>

#include "types.hpp"

class Instruction;

class Subroutine {
 private:
  u24 pc;
  std::vector<Instruction*> instructions;
};
