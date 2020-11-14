#include "stack.hpp"

using namespace std;

void Stack::setPointer(const Instruction* instruction, u16 pointer) {
  lastManipulator = instruction;
  this->pointer = pointer;
}

void Stack::push(const Instruction* instruction, u24 data, size_t size) {
  for (size_t i = size; i > 0; i--) {
    u8 byte = (data >> (i * 8)) & 0xFF;
    memory[pointer--] = {instruction, byte};
  }
}

StackEntry Stack::popByte() {
  auto search = memory.find(++pointer);
  if (search != memory.end()) {
    return search->second;
  } else {
    return {nullptr, nullopt};
  }
}

vector<StackEntry> Stack::pop(size_t size) {
  vector<StackEntry> result;
  for (size_t i = 0; i < size; i++) {
    result.push_back(popByte());
  }
  return result;
}
