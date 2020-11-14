#pragma once

#include <vector>

#include "stack.hpp"
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
  bool checkReturnManipulation(const Instruction& instruction,
                               std::vector<StackEntry> entries);
  void deriveStateInference(const Instruction& instruction);
  void standardRet();
  Subroutine* subroutine();
  void propagateSubroutineState(u24 target);
  void unknownStateChange(UnknownReason reason);

  Analysis* analysis;
  bool stop = false;

  u24 pc;
  u24 subroutinePC;
  State state;
  StateChange stateChange;
  StateChange stateInference;
  Stack stack;
};
