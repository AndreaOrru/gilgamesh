#pragma once

#include <optional>
#include <unordered_map>
#include <variant>
#include <vector>

#include "state.hpp"
#include "types.hpp"

class Instruction;

// Optional payload (value pushed onto the stack).
typedef std::variant<std::nullopt_t, u24, std::pair<State, StateChange>>
    StackData;

// Stack entry.
struct StackEntry {
  const Instruction* instruction = nullptr;
  StackData data = std::nullopt;
};

// SNES stack.
class Stack {
 public:
  // Set a new stack pointer.
  void setPointer(const Instruction* instruction, u16 pointer);

  // Push values onto the stack.
  void push(const Instruction* instruction,
            std::optional<u24> data,
            size_t size);

  // Push state (PHP) onto the stack.
  void pushState(const Instruction* instruction,
                 State state,
                 StateChange stateChange);

  // Pop an entry from the stack.
  StackEntry popOne();

  // Pop one or more entries from the stack.
  std::vector<StackEntry> pop(size_t size);

 private:
  std::unordered_map<u16, StackEntry> memory;  // SNES's RAM.
  u16 pointer = 0x100;                         // Stack pointer.
  // The last instruction to explicitly change the stack pointer.
  const Instruction* lastManipulator = nullptr;
};
