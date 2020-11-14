#include "subroutine.hpp"

#include "instruction.hpp"

Subroutine::Subroutine(u24 pc, std::string label) : pc{pc}, label{label} {}

void Subroutine::addInstruction(Instruction* instruction) {
  instructions[instruction->pc] = instruction;
}
