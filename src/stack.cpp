#include "stack.hpp"

using namespace std;

void Stack::setPointer(const Instruction* instruction, u16 pointer) {
  lastManipulator = instruction;
  this->pointer = pointer;
}

void Stack::push(const Instruction* instruction,
                 optional<u24> data,
                 size_t size) {
  for (size_t i = size; i > 0; i--) {
    StackData stackData = nullopt;
    if (data.has_value()) {
      stackData = (*data >> (i * 8)) & 0xFF;
    }
    memory[pointer--] = {instruction, stackData};
  }
}

void Stack::pushState(const Instruction* instruction,
                      State state,
                      StateChange stateChange) {
  memory[pointer--] = {instruction,
                       pair<State, StateChange>(state, stateChange)};
}

StackEntry Stack::popOne() {
  auto search = memory.find(++pointer);
  if (search != memory.end()) {
    return search->second;
  } else {
    return StackEntry();
  }
}

vector<StackEntry> Stack::pop(size_t size) {
  vector<StackEntry> result;
  for (size_t i = 0; i < size; i++) {
    result.push_back(popOne());
  }
  return result;
}
