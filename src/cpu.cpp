#include <unordered_set>

#include "cpu.hpp"

#include "analysis.hpp"
#include "instruction.hpp"
#include "rom.hpp"

using namespace std;

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
      analysis->addInstruction(pc, subroutinePC, opcode, argument, state);

  if (instruction == nullptr) {
    stop = true;
  } else {
    execute(instruction);
  }
}

void CPU::execute(const Instruction* instruction) {
  pc += instruction->size();

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

void CPU::branch(const Instruction* instruction) {
  CPU cpu(*this);
  cpu.run();

  auto target = *instruction->absoluteArgument();
  analysis->addReference(instruction->pc, target, subroutinePC);
  pc = target;
}

void CPU::call(const Instruction* instruction) {
  auto target = instruction->absoluteArgument();
  if (!target.has_value()) {
    return unknownStateChange(UnknownReason::IndirectJump);
  }

  CPU cpu(*this);
  cpu.pc = *target;
  cpu.subroutinePC = *target;
  cpu.stateChange = StateChange();
  switch (instruction->operation()) {
    case Op::JSR:
      cpu.stack.push(instruction, instruction->pc, 2);
      break;
    case Op::JSL:
      cpu.stack.push(instruction, instruction->pc, 3);
      break;
    default:
      __builtin_unreachable();
  }

  analysis->addSubroutine(*target);
  analysis->addReference(instruction->pc, *target, subroutinePC);
  cpu.run();

  propagateSubroutineState(*target);
}

void CPU::interrupt(const Instruction* instruction) {
  return unknownStateChange(UnknownReason::SuspectInstruction);
}

void CPU::jump(const Instruction* instruction) {
  if (auto target = instruction->absoluteArgument()) {
    analysis->addReference(instruction->pc, *target, subroutinePC);
    pc = *target;
  } else {
    return unknownStateChange(UnknownReason::IndirectJump);
  }
}

void CPU::ret(const Instruction* instruction) {
  if (instruction->operation() == Op::RTI) {
    return standardRet();
  }

  size_t retSize = instruction->operation() == Op::RTS ? 2 : 3;
  auto stackEntries = stack.pop(retSize);
  if (checkReturnManipulation(instruction, stackEntries) == false) {
    return standardRet();
  }

  return unknownStateChange(UnknownReason::StackManipulation);
}

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

  stateChange.applyInference(stateInference);
}

void CPU::push(const Instruction* instruction) {
  switch (instruction->operation()) {
    case Op::PHP:
      return stack.pushState(instruction, state, stateChange);

    case Op::PHA:
      return stack.push(instruction, nullopt, state.sizeA());

    case Op::PHX:
    case Op::PHY:
      return stack.push(instruction, nullopt, state.sizeX());

    case Op::PHB:
    case Op::PHK:
      return stack.push(instruction, nullopt, 1);

    case Op::PHD:
    case Op::PEA:
    case Op::PER:
    case Op::PEI:
      return stack.push(instruction, nullopt, 2);

    default:
      __builtin_unreachable();
  }
}

void CPU::pop(const Instruction* instruction) {
  switch (instruction->operation()) {
    case Op::PLP: {
      auto entry = stack.popOne();
      if (entry.instruction && entry.instruction->operation() == Op::PHP) {
        auto [state, stateChange] = get<pair<State, StateChange>>(entry.data);
        this->state = state;
        this->stateChange = stateChange;
      } else {
        return unknownStateChange(UnknownReason::StackManipulation);
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

bool CPU::checkReturnManipulation(const Instruction* instruction,
                                  vector<StackEntry> entries) {
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

void CPU::deriveStateInference(const Instruction* instruction) {
  if (instruction->addressMode() == AddressMode::ImmediateM &&
      !stateChange.m.has_value()) {
    stateInference.m = (bool)state.m;
  }
  if (instruction->addressMode() == AddressMode::ImmediateX &&
      !stateChange.x.has_value()) {
    stateInference.x = (bool)state.x;
  }
}

void CPU::standardRet() {
  subroutine()->addStateChange(stateChange);
  stop = true;
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
