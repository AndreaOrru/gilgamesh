#pragma once

#include "state.hpp"
#include "types.hpp"

class Analysis;
class Instruction;

class CPU {
 public:
  CPU(Analysis* analysis, u24 pc, u24 subroutine, State state);
  void run();

 private:
  void step();
  void execute(const Instruction& instruction);

  void branch(const Instruction& instruction);
  void call(const Instruction& instruction);
  void interrupt(const Instruction& instruction);
  void jump(const Instruction& instruction);
  void ret(const Instruction& instruction);
  void sepRep(const Instruction& instruction);

  Analysis* analysis;
  bool stop;

  u24 pc;
  u24 subroutine;
  State state;
};
