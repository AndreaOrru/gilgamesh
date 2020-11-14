#include <unordered_set>

#include "cpu.hpp"

#include "analysis.hpp"
#include "instruction.hpp"
#include "rom.hpp"

CPU::CPU(Analysis* analysis, u24 pc, u24 subroutinePC, State state)
    : analysis{analysis}, pc{pc}, subroutinePC{subroutinePC}, state{state} {}

void CPU::run() {
  while (!stop) {
    step();
  }
}

void CPU::step() {
  if (ROM::isRAM(pc)) {
    return unknownStateChange(UnknownReason::MutableCode);
  }

  auto opcode = analysis->rom.readByte(pc);
  auto argument = analysis->rom.readAddress(pc + 1);
  auto instruction =
      Instruction(analysis, pc, subroutinePC, opcode, argument, state);

  if (analysis->hasVisited(instruction)) {
    stop = true;
  } else {
    analysis->addInstruction(instruction);
    execute(instruction);
  }
}

void CPU::execute(const Instruction& instruction) {
  pc += instruction.size();

  deriveStateInference(instruction);

  switch (instruction.type()) {
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
    // case InstructionType::Pop:
    //   return pop(instruction);
    // case InstructionType::Push:
    //   return push(instruction);
    default:
      return;
  }
}

void CPU::branch(const Instruction& instruction) {
  CPU cpu(*this);
  cpu.run();

  auto target = *instruction.absoluteArgument();
  analysis->addReference(instruction.pc, target, subroutinePC);
  pc = target;
}

void CPU::call(const Instruction& instruction) {
  auto target = instruction.absoluteArgument();
  if (!target.has_value()) {
    return unknownStateChange(UnknownReason::IndirectJump);
  }

  CPU cpu(*this);
  cpu.pc = *target;
  cpu.subroutinePC = *target;
  cpu.stateChange = StateChange();
  switch (instruction.operation()) {
    case Op::JSR:
      cpu.stack.push(instruction.pc, 2);
      break;
    case Op::JSL:
      cpu.stack.push(instruction.pc, 3);
      break;
    default:
      __builtin_unreachable();
  }

  analysis->addSubroutine(*target);
  analysis->addReference(instruction.pc, *target, subroutinePC);
  cpu.run();

  propagateSubroutineState(*target);
}

void CPU::interrupt(const Instruction& instruction) {
  return unknownStateChange(UnknownReason::SuspectInstruction);
}

void CPU::jump(const Instruction& instruction) {
  if (auto target = instruction.absoluteArgument()) {
    analysis->addReference(instruction.pc, *target, subroutinePC);
    pc = *target;
  } else {
    return unknownStateChange(UnknownReason::IndirectJump);
  }
}

void CPU::ret(const Instruction& instruction) {
  size_t retSize = instruction.operation() == Op::RTS ? 2 : 3;
  auto stackEntries = stack.pop(retSize);
  // TODO: check manipulation...

  subroutine()->addStateChange(stateChange);
  stop = true;
}

void CPU::sepRep(const Instruction& instruction) {
  auto arg = *instruction.absoluteArgument();

  switch (instruction.operation()) {
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

  stateChange.applyInference(stateInference);
}

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

void CPU::deriveStateInference(const Instruction& instruction) {
  if (instruction.addressMode() == AddressMode::ImmediateM &&
      !stateChange.m.has_value()) {
    stateInference.m = (bool)state.m;
  }
  if (instruction.addressMode() == AddressMode::ImmediateX &&
      !stateChange.x.has_value()) {
    stateInference.x = (bool)state.x;
  }
}

Subroutine* CPU::subroutine() {
  return &analysis->subroutines.at(subroutinePC);
}

void CPU::propagateSubroutineState(u24 target) {
  auto& subroutine = analysis->subroutines.at(target);
  if (!subroutine.unknownStateChanges.empty()) {
    return unknownStateChange(UnknownReason::Unknown);
  }

  auto& stateChanges = subroutine.knownStateChanges;
  if ((stateChanges.size()) == 1) {
    applyStateChange(*stateChanges.begin());
  } else {
    return unknownStateChange(UnknownReason::MultipleReturnStates);
  }
}

void CPU::unknownStateChange(UnknownReason reason) {
  subroutine()->addStateChange(StateChange(reason));
  stop = true;
}
