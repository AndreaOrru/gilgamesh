#include "stack.hpp"

using namespace std;

// Set a new stack pointer.
void Stack::setPointer(const Instruction* instruction, u16 pointer) {
  lastManipulator = instruction;
  this->pointer = pointer;
}

// Push values onto the stack.
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

// Push state (PHP) onto the stack.
void Stack::pushState(const Instruction* instruction,
                      State state,
                      StateChange stateChange) {
  memory[pointer--] = {instruction,
                       pair<State, StateChange>(state, stateChange)};
}

// Pop an entry from the stack.
StackEntry Stack::popOne() {
  auto search = memory.find(++pointer);
  if (search != memory.end()) {
    return search->second;
  } else {
    return StackEntry();
  }
}

// Pop one or more entries from the stack.
vector<StackEntry> Stack::pop(size_t size) {
  vector<StackEntry> result;
  for (size_t i = 0; i < size; i++) {
    result.push_back(popOne());
  }
  return result;
}
