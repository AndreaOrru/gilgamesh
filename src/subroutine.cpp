#include "subroutine.hpp"
#include "instruction.hpp"

void Subroutine::addInstruction(const Instruction* instruction) {
  instructions[instruction->pc] = instruction;
}
