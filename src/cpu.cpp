#include "cpu.hpp"
#include "analysis.hpp"
#include "instruction.hpp"
#include "rom.hpp"

CPU::CPU(Analysis* analysis, u24 pc, u24 subroutine, State state)
    : analysis{analysis}, pc{pc}, subroutine{subroutine}, state{state} {}

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
      Instruction(analysis, pc, subroutine, opcode, argument, state);

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
      branch(instruction);

    default:
      return;
  }
}

void CPU::branch(const Instruction& instruction) {
  return;
}
