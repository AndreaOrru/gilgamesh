#pragma once

#include <unordered_set>
#include <utility>
#include <vector>

#include "register.hpp"
#include "stack.hpp"
#include "state.hpp"
#include "types.hpp"

class Analysis;
class Instruction;
class Subroutine;

class CPU {
 public:
  // Constructor.
  CPU(Analysis* analysis,
      InstructionPC pc,
      SubroutinePC subroutinePC,
      State state);
  // Copy constructor.
  CPU(const CPU& cpu);

  void run();   // Start emulating.
  void step();  // Fetch and execute the next instruction.

  // Whether we should stop emulating after the current instruction.
  bool stop = false;

  InstructionPC pc;           // Program Counter.
  SubroutinePC subroutinePC;  // Subroutine currently being executed.
  Stack stack;                // CPU stack.
  State state;                // CPU state.
  // CPU state change caused by the execution of the current subroutine.
  StateChange stateChange;
  // What we know about the CPU state based on the
  // sequence of instructions we have executed.
  StateChange stateInference;

  Register A;  // Accumulator.
  Register X;  // Index X.

 private:
  // Emulate an instruction.
  void execute(const Instruction* instruction);

  void branch(const Instruction* instruction);       // Branch emulation.
  void call(const Instruction* instruction);         // Call emulation.
  void interrupt(const Instruction* instruction);    // Interrupt emulation.
  void jump(const Instruction* instruction);         // Jump emulation.
  void ret(const Instruction* instruction);          // Return emulation.
  void standardRet(const Instruction* instruction);  // Emulate a simple return.
  void sepRep(const Instruction* instruction);       // SEP/REP emulation.
  void pop(const Instruction* instruction);          // Pop value from stack.
  void push(const Instruction* instruction);         // Push value onto stack.

  // Emulate instructions that modify the value of A.
  void changeA(const Instruction* instruction);
  // Emulate instructions that modify the value of X.
  void changeX(const Instruction* instruction);
  // Emulate instructions that modify the value of the stack pointer.
  void changeStackPointer(const Instruction* instruction);

  // Apply a state change to the current CPU instance.
  void applyStateChange(StateChange stateChange);

  // Check whether the return instruction is operating on a manipulated stack.
  bool checkReturnManipulation(const Instruction* instruction,
                               std::vector<StackEntry> entries) const;

  // Given a jump or call instruction, return its target(s), if any.
  // Additionally, track jump tables when they're seen for the first time.
  std::optional<std::unordered_set<InstructionPC>> computeJumpTargets(
      const Instruction* instruction);

  // Derive a state inference from the current state and instruction.
  void deriveStateInference(const Instruction* instruction);

  // Return a pointer to the current subroutine object.
  Subroutine* subroutine() const;

  // Take the state change of the given subroutines and
  // propagate it to to the current subroutine state.
  void propagateSubroutineState(
      InstructionPC pc,
      const std::unordered_set<InstructionPC>& target);

  // Apply assertions to the current instruction, if any.
  void tryApplyAssertion(InstructionPC pc);

  // Signal an unknown subroutine state change.
  void unknownStateChange(InstructionPC pc, UnknownReason reason);

  // Pointer to the analysis.
  Analysis* analysis;

  // Test functions.
  friend void runInstruction(CPU& cpu, u8 opcode, u24 argument);
};
