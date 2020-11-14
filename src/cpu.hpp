#pragma once

#include "state.hpp"
#include "types.hpp"

class Analysis;
class Instruction;
class Subroutine;

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

  void applyStateChange(StateChange stateChange);
  Subroutine* subroutine();
  void propagateSubroutineState(u24 target);

  Analysis* analysis;
  bool stop = false;

  u24 pc;
  u24 subroutinePC;
  State state;
  StateChange stateChange;
};
