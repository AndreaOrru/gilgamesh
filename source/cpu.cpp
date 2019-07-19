#include "cpu.hpp"
#include "instruction.hpp"
#include "log.hpp"
#include "rom.hpp"

CPU::CPU(Log *log, State state, u24 subroutine)
    : state(state), log(log), subroutine(subroutine) {}

CPU::CPU(Log *log, State state)
    : state(state), log(log), subroutine(state.pc) {}

void CPU::run() {
  bool keep_going = step();
  while (keep_going) {
    keep_going = step();
  }
}

bool CPU::step() {
  if (isRAM(state.pc)) {
    return false;
  }

  u8 opcode = log->rom->readByte(state.pc);
  u24 argument = log->rom->readAddress(state.pc + 1);

  auto [instruction, inserted] =
      log->logInstruction(subroutine, state, opcode, argument);
  if (!inserted) {
    return false;
  }

  return execute(instruction);
}

bool CPU::execute(const Instruction &instruction) {
  state.pc += instruction.size();

  if (instruction.addressMode() == IMMEDIATE_M && !state_change.m.has_value()) {
    state_assertion.m = (bool)state.m;
  } else if (instruction.addressMode() == IMMEDIATE_X &&
             !state_change.x.has_value()) {
    state_assertion.x = (bool)state.x;
  }

  if (instruction.operation() == BRK) {
    return false;
  } else if (instruction.isReturn()) {
    log->logSubroutine(subroutine, state_change);
    return false;
  } else if (instruction.isBranch()) {
    branch(instruction);
  } else if (instruction.isCall()) {
    return call(instruction);
  } else if (instruction.isJump()) {
    jump(instruction);
  } else if (instruction.isSepRep()) {
    sepRep(instruction);
  } else if (instruction.operation() == PHP) {
    push_state();
  } else if (instruction.operation() == PLP) {
    pop_state();
  }

  return true;
}

void CPU::branch(const Instruction &instruction) {
  CPU cpu(*this);
  cpu.run();

  state.pc = *instruction.absoluteArgument();
}

bool CPU::call(const Instruction &instruction) {
  if (auto target = instruction.absoluteArgument()) {
    CPU cpu(*this);
    cpu.subroutine = cpu.state.pc = *target;
    log->logSubroutine(*target);
    cpu.state_change = {};
    cpu.run();

    bool known = propagateSubroutineState(*target);
    if (known) {
      return true;
    }
  }

  return false;
}

void CPU::jump(const Instruction &instruction) {
  if (auto target = instruction.absoluteArgument()) {
    state.pc = *target;
  }
}

void CPU::sepRep(const Instruction &instruction) {
  State change = {.p = (u8)*instruction.argument()};

  if (instruction.operation() == SEP) {
    state.p |= change.p;
    state_change.m = change.m ? true : state_change.m;
    state_change.x = change.x ? true : state_change.x;
  } else {
    state.p &= ~change.p;
    state_change.m = change.m ? false : state_change.m;
    state_change.x = change.x ? false : state_change.x;
  }

  if (state_assertion.m.has_value() && state_change.m.has_value() &&
      *state_assertion.m == *state_change.m) {
    state_change.m = {};
  }
  if (state_assertion.x.has_value() && state_change.x.has_value() &&
      *state_assertion.x == *state_change.x) {
    state_change.x = {};
  }
}

void CPU::push_state() { state_stack.push({state.p, state_change}); }

void CPU::pop_state() {
  auto [state_p, state_change] = state_stack.top();
  state_stack.pop();
  this->state.p = state_p;
  this->state_change = state_change;
}

bool CPU::propagateSubroutineState(u24 subroutine) {
  auto state_changes = log->subroutineStateChanges(subroutine);

  if (state_changes.size() == 1) {
    auto change = *state_changes.begin();
    if (change.m.has_value()) {
      state_change.m = (bool)(state.m = *change.m);
    }
    if (change.x.has_value()) {
      state_change.x = (bool)(state.x = *change.x);
    }
    return true;
  }

  return false;
}

bool CPU::isRAM(u24 address) {
  return (address <= 0x001FFF) || (address >= 0x7E0000 && address <= 0x7FFFFF);
}
