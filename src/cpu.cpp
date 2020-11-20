#include "cpu.hpp"

#include "analysis.hpp"
#include "instruction.hpp"
#include "rom.hpp"

using namespace std;

// Constructor.
CPU::CPU(Analysis* analysis,
         InstructionPC pc,
         SubroutinePC subroutinePC,
         State state)
    : pc{pc}, subroutinePC{subroutinePC}, state{state}, analysis{analysis} {}

// Start emulating.
void CPU::run() {
  while (!stop) {
    step();
  }
}

// Fetch and execute the next instruction.
void CPU::step() {
  // Stop if we have jumped into RAM.
  if (ROM::isRAM(pc)) {
    return unknownStateChange(pc, UnknownReason::MutableCode);
  }

  auto opcode = analysis->rom.readByte(pc);
  auto argument = analysis->rom.readAddress(pc + 1);
  auto instruction =
      analysis->addInstruction(pc, subroutinePC, opcode, argument, state);

  // Stop the analysis if we have already visited this instruction.
  if (instruction == nullptr) {
    stop = true;
  } else {
    execute(instruction);
  }
}

// Emulate an instruction.
void CPU::execute(const Instruction* instruction) {
  pc += instruction->size();

  // See if we can learn something about the *required*
  // state of the CPU based on the current instruction.
  deriveStateInference(instruction);

  switch (instruction->type()) {
    case InstructionType::Branch:
      return branch(instruction);
    case InstructionType::Call:
      return call(instruction);
    case InstructionType::Interrupt:
      return interrupt(instruction);
    case InstructionType::Jump:
      return jump(instruction);
    case InstructionType::Return:
      return ret(instruction);
    case InstructionType::SepRep:
      return sepRep(instruction);
    case InstructionType::Pop:
      return pop(instruction);
    case InstructionType::Push:
      return push(instruction);
    default:
      return;
  }
}

// Branch emulation.
void CPU::branch(const Instruction* instruction) {
  // Run a parallel instance of the CPU to cover
  // the case in which the branch is not taken.
  CPU cpu(*this);
  cpu.run();

  // Log the fact that the current instruction references the
  // instruction pointed by the branch. Then take the branch.
  auto target = *instruction->absoluteArgument();
  analysis->addReference(instruction->pc, target, subroutinePC);
  pc = target;
}

// Call emulation.
void CPU::call(const Instruction* instruction) {
  auto target = instruction->absoluteArgument();
  if (!target.has_value()) {
    return unknownStateChange(instruction->pc, UnknownReason::IndirectJump);
  }

  CPU cpu(*this);
  cpu.pc = *target;
  cpu.subroutinePC = *target;
  cpu.stateChange = StateChange();
  switch (instruction->operation()) {
    case Op::JSR:
      cpu.stack.push(2, instruction->pc, instruction);
      break;
    case Op::JSL:
      cpu.stack.push(3, instruction->pc, instruction);
      break;
    default:
      __builtin_unreachable();
  }

  analysis->addSubroutine(*target);
  analysis->addReference(instruction->pc, *target, subroutinePC);
  cpu.run();

  propagateSubroutineState(pc, *target);
}

// Interrupt emulation.
void CPU::interrupt(const Instruction* instruction) {
  return unknownStateChange(instruction->pc, UnknownReason::SuspectInstruction);
}

void CPU::jump(const Instruction* instruction) {
  if (auto target = instruction->absoluteArgument()) {
    analysis->addReference(instruction->pc, *target, subroutinePC);
    pc = *target;
  } else {
    return unknownStateChange(instruction->pc, UnknownReason::IndirectJump);
  }
}

// Return emulation.
void CPU::ret(const Instruction* instruction) {
  if (instruction->operation() == Op::RTI) {
    return standardRet(instruction);
  }

  size_t retSize = instruction->operation() == Op::RTS ? 2 : 3;
  auto stackEntries = stack.pop(retSize);
  if (checkReturnManipulation(instruction, stackEntries) == false) {
    return standardRet(instruction);
  }

  return unknownStateChange(instruction->pc, UnknownReason::StackManipulation);
}

// Emulate a simple return.
void CPU::standardRet(const Instruction* instruction) {
  subroutine()->addStateChange(instruction->pc, stateChange);
  stop = true;
}

// SEP/REP emulation.
void CPU::sepRep(const Instruction* instruction) {
  auto arg = *instruction->absoluteArgument();

  switch (instruction->operation()) {
    case Op::SEP:
      state.set(arg);
      stateChange.set(arg);
      break;

    case Op::REP:
      state.reset(arg);
      stateChange.reset(arg);
      break;

    default:
      __builtin_unreachable();
  }

  // Simplify the state change by applying our knowledge of the current state.
  // If we know that the processor is operating in 8-bits accumulator mode and
  // we switch to that mode, effectively no state change is being performed.
  stateChange.applyInference(stateInference);
}

// Pop value from stack.
void CPU::pop(const Instruction* instruction) {
  switch (instruction->operation()) {
    case Op::PLP: {
      auto entry = stack.popOne();
      if (entry.instruction && entry.instruction->operation() == Op::PHP) {
        // Regular state restoring.
        auto [state, stateChange] = get<pair<State, StateChange>>(entry.data);
        this->state = state;
        this->stateChange = stateChange;
      } else {
        // Stack manipulation. Stop here.
        return unknownStateChange(instruction->pc,
                                  UnknownReason::StackManipulation);
      }
    } break;

    case Op::PLA:
      stack.pop(state.sizeA());
      break;

    case Op::PLX:
    case Op::PLY:
      stack.pop(state.sizeX());
      break;

    case Op::PLB:
      stack.popOne();
      break;

    case Op::PLD:
      stack.pop(2);
      break;

    default:
      __builtin_unreachable();
  }
}

// Push value onto stack.
void CPU::push(const Instruction* instruction) {
  switch (instruction->operation()) {
    case Op::PHP:
      return stack.pushState(state, stateChange, instruction);

    case Op::PHA:
      return stack.push(state.sizeA(), nullopt, instruction);

    case Op::PHX:
    case Op::PHY:
      return stack.push(state.sizeX(), nullopt, instruction);

    case Op::PHB:
    case Op::PHK:
      return stack.pushOne(nullopt, instruction);

    case Op::PHD:
    case Op::PEA:
    case Op::PER:
    case Op::PEI:
      return stack.push(2, nullopt, instruction);

    default:
      __builtin_unreachable();
  }
}

// Apply a state change to the current CPU instance.
void CPU::applyStateChange(StateChange stateChange) {
  if (auto m = stateChange.m) {
    this->state.m = *m;
    this->stateChange.m = *m;
  }
  if (auto x = stateChange.x) {
    this->state.x = *x;
    this->stateChange.x = *x;
  }
}

// Check whether the return instruction is operating on a manipulated stack.
bool CPU::checkReturnManipulation(const Instruction* instruction,
                                  vector<StackEntry> entries) const {
  auto op = instruction->operation();

  for (auto& entry : entries) {
    auto caller = entry.instruction;
    if (caller == nullptr) {
      return true;
    }

    if (op == Op::RTS && caller->operation() != Op::JSR) {
      return true;
    } else if (op == Op::RTL && caller->operation() != Op::JSL) {
      return true;
    }
  }

  return false;
}

// Derive a state inference from the current state and instruction.
void CPU::deriveStateInference(const Instruction* instruction) {
  // If we're executing an instruction with a certain operand size,
  // and no state change has been performed in the current subroutine,
  // then we can infer that the state of the processor as we enter
  // the subroutine *must* be the same in all cases.
  if (instruction->addressMode() == AddressMode::ImmediateM &&
      !stateChange.m.has_value()) {
    stateInference.m = (bool)state.m;
  }
  if (instruction->addressMode() == AddressMode::ImmediateX &&
      !stateChange.x.has_value()) {
    stateInference.x = (bool)state.x;
  }
}

// Return a pointer to the current subroutine object.
Subroutine* CPU::subroutine() const {
  return &analysis->subroutines.at(subroutinePC);
}

// Take the state change of the given subroutine and
// propagate it to to the current subroutine state.
void CPU::propagateSubroutineState(InstructionPC pc, InstructionPC target) {
  auto& subroutine = analysis->subroutines.at(target);
  if (!subroutine.unknownStateChanges.empty()) {
    return unknownStateChange(pc, UnknownReason::Unknown);
  }

  auto& stateChanges = subroutine.knownStateChanges;
  if ((stateChanges.size()) == 1) {
    applyStateChange(stateChanges.begin()->second);
  } else {
    return unknownStateChange(pc, UnknownReason::MultipleReturnStates);
  }
}

// Signal an unknown subroutine state change.
void CPU::unknownStateChange(InstructionPC pc, UnknownReason reason) {
  // Check if we have an assertion to specify what the state change is.
  auto assertion = analysis->getAssertion(pc, subroutinePC);
  if (assertion.has_value()) {
    switch (assertion->type) {
      case AssertionType::Instruction:
        applyStateChange(assertion->stateChange);
        break;

      case AssertionType::Subroutine:
        subroutine()->addStateChange(pc, assertion->stateChange);
        stop = true;
        break;
    }
  } else {
    // No assertions, we need stop here.
    subroutine()->addStateChange(pc, StateChange(UnknownReason(reason)));
    stop = true;
  }
}
