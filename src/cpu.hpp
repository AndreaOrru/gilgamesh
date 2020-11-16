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
  CPU(Analysis* analysis, u24 pc, u24 subroutine, State state);  // Constructor.
  void run();  // Start emulating.

 private:
  // Fetch and execute the next instruction.
  void step();

  // Emulate an instruction.
  void execute(const Instruction* instruction);

  void branch(const Instruction* instruction);     // Branch emulation.
  void call(const Instruction* instruction);       // Call emulation.
  void interrupt(const Instruction* instruction);  // Interrupt emulation.
  void jump(const Instruction* instruction);       // Jump emulation.
  void ret(const Instruction* instruction);        // Return emulation.
  void standardRet();                              // Emulate a simple return.
  void sepRep(const Instruction* instruction);     // SEP/REP emulation.
  void pop(const Instruction* instruction);        // Pop value from stack.
  void push(const Instruction* instruction);       // Push value onto stack.

  // Apply a state change to the current CPU instance.
  void applyStateChange(StateChange stateChange);

  // Check whether the return instruction is operating on a manipulated stack.
  bool checkReturnManipulation(const Instruction* instruction,
                               std::vector<StackEntry> entries);

  // Derive a state inference from the current state and instruction.
  void deriveStateInference(const Instruction* instruction);

  // Return a pointer to the current subroutine object.
  Subroutine* subroutine();

  // Take the state change of the given subroutine and
  // propagate it to to the current subroutine state.
  void propagateSubroutineState(u24 target);

  // Signal an unknown subroutine state change.
  void unknownStateChange(UnknownReason reason);

  // Pointer to the analysis.
  Analysis* analysis;

  // Whether we should stop emulating after the current instruction.
  bool stop = false;

  u24 pc;            // Program Counter.
  u24 subroutinePC;  // Subroutine currently being executed.
  Stack stack;       // CPU stack.
  State state;       // CPU state.

  // CPU state change caused by the execution of the current subroutine.
  StateChange stateChange;

  // What we know about the CPU state based on the
  // sequence of instructions we have executed.
  StateChange stateInference;
};
