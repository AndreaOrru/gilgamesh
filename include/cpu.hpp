#pragma once
#include "state.hpp"
#include <stack>

class Instruction;
class Log;

class CPU {
public:
  State state;

  CPU(Log *log, State state, u24 subroutine);
  CPU(Log *log, State state);

  void run();
  bool step();
  bool execute(const Instruction &instruction);

private:
  Log *log;
  u24 subroutine;
  StateChange state_change;
  StateChange state_assertion;
  std::stack<std::pair<u8, StateChange>> state_stack;

  void branch(const Instruction &instruction);
  bool call(const Instruction &instruction);
  void jump(const Instruction &instruction);
  void sepRep(const Instruction &instruction);
  void push_state();
  void pop_state();

  bool propagateSubroutineState(u24 subroutine);
  static bool isRAM(u24 address);
};
