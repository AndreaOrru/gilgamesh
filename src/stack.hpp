#pragma once

#include <optional>
#include <unordered_map>
#include <variant>
#include <vector>

#include "state.hpp"
#include "types.hpp"

class Instruction;

// Optional payload (value pushed onto the stack).
typedef std::variant<std::nullopt_t, u8, std::pair<State, StateChange>>
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
  void setPointer(u16 pointer, const Instruction* instruction);

  // Push a value onto the stack.
  void pushValue(size_t size,
                 std::optional<u24> data = std::nullopt,
                 const Instruction* instruction = nullptr);

  // Push state (PHP) onto the stack.
  void pushState(State state,
                 StateChange stateChange,
                 const Instruction* instruction = nullptr);

  // Push a byte onto the stack.
  void pushOne(std::optional<u8> data,
               const Instruction* instruction = nullptr);

  // Pop a value from the stack.
  std::optional<u24> popValue(size_t size);

  // Pop one or more entries from the stack.
  std::vector<StackEntry> pop(size_t size);

  // Pop an entry from the stack.
  StackEntry popOne();

  // Return values from the top of the stack without popping.
  std::vector<StackEntry> peek(size_t size) const;

  // Compare the value at the top of the stack with a given value.
  bool matchValue(size_t size, u24 value) const;

  u16 pointer = 0x100;  // Stack pointer.

 private:
  std::unordered_map<u16, StackEntry> memory;  // SNES's RAM.
  // The last instruction to explicitly change the stack pointer.
  const Instruction* lastManipulator = nullptr;
};
