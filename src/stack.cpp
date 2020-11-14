#include "stack.hpp"

using namespace std;

void Stack::setPointer(u16 pointer) {
  this->pointer = pointer;
}

void Stack::push(u24 data, size_t size) {
  for (size_t i = size; i > 0; i--) {
    u8 byte = (data >> (i * 8)) & 0xFF;
    memory[pointer--] = byte;
  }
}

optional<u8> Stack::popByte() {
  auto search = memory.find(++pointer);
  return (search != memory.end()) ? optional(search->second) : nullopt;
}

vector<optional<u8>> Stack::pop(size_t size) {
  vector<optional<u8>> result;
  for (size_t i = 0; i < size; i++) {
    result.push_back(popByte());
  }
  return result;
}
