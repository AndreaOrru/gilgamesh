#pragma once

#include "state.hpp"
#include "types.hpp"

class Analysis;
class Instruction;

class CPU {
 private:
  void step();
  void execute(const Instruction& instruction);
  void branch(const Instruction& instruction);

  Analysis* analysis;
  bool stop;

  u24 pc;
  u24 subroutine;
  State state;

 public:
  CPU(Analysis* analysis, u24 pc, u24 subroutine, State state);
  void run();
};
