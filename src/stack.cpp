#include "stack.hpp"
#include <variant>

using namespace std;

// Set a new stack pointer.
void Stack::setPointer(u16 pointer, const Instruction* instruction) {
  this->pointer = pointer;
  lastManipulator = instruction;
}

// Push values onto the stack.
void Stack::push(size_t size,
                 optional<u24> data,
                 const Instruction* instruction) {
  for (int i = size - 1; i >= 0; i--) {
    StackData stackData = nullopt;
    if (data.has_value()) {
      stackData = (*data >> (i * 8)) & 0xFF;
    }
    memory[pointer--] = {instruction, stackData};
  }
}

// Push state (PHP) onto the stack.
void Stack::pushState(State state,
                      StateChange stateChange,
                      const Instruction* instruction) {
  memory[pointer--] = {instruction,
                       pair<State, StateChange>(state, stateChange)};
}

// Push a value onto the stack.
void Stack::pushOne(optional<u24> data, const Instruction* instruction) {
  push(1, data, instruction);
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

// Return values from the top of the stack without popping.
vector<StackEntry> Stack::peek(size_t size) const {
  vector<StackEntry> result;
  for (size_t i = 1; i <= size; i++) {
    auto search = memory.find(pointer + i);
    if (search != memory.end()) {
      result.push_back(search->second);
    } else {
      result.push_back(StackEntry());
    }
  }
  return result;
}

// Compare the value at the top of the stack with a given value.
bool Stack::matchValue(size_t size, u24 value) const {
  auto entries = peek(size);

  for (size_t i = 0; i < size; i++) {
    auto data = entries[i].data;
    if (!holds_alternative<u24>(data)) {
      return false;
    }
    if (get<u24>(data) != ((value >> (i * 8)) & 0xFF)) {
      return false;
    }
  }
  return true;
}
