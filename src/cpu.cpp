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
    stop = true;
    return;
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

  pc = *instruction.absoluteArgument();
}

void CPU::call(const Instruction& instruction) {
  auto target = instruction.absoluteArgument();
  if (!target.has_value()) {
    stop = true;
    return;
  }

  CPU cpu(*this);
  cpu.pc = *target;
  cpu.subroutinePC = *target;
  cpu.stateChange = StateChange();

  analysis->addSubroutine(*target);
  cpu.run();

  propagateSubroutineState(*target);
}

void CPU::interrupt(const Instruction& instruction) {
  stop = true;
}

void CPU::jump(const Instruction& instruction) {
  if (auto target = instruction.absoluteArgument()) {
    pc = *target;
  } else {
    stop = true;
  }
}

void CPU::ret(const Instruction& instruction) {
  subroutine()->stateChanges.insert(stateChange);
  stop = true;
}

void CPU::sepRep(const Instruction& instruction) {
  auto arg = *instruction.absoluteArgument();

  switch (instruction.operation()) {
    case Op::SEP:
      break;

    case Op::REP:
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

Subroutine* CPU::subroutine() {
  return &analysis->subroutines.at(subroutinePC);
}

void CPU::propagateSubroutineState(u24 target) {
  auto& stateChanges = analysis->subroutines.at(target).stateChanges;

  if ((stateChanges.size()) == 1) {
    applyStateChange(*stateChanges.begin());
  } else {
    stop = true;
  }
}
