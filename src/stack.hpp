#pragma once

#include <optional>
#include <unordered_map>
#include <variant>
#include <vector>

#include "state.hpp"
#include "types.hpp"

class Instruction;

typedef std::variant<std::nullopt_t, u24, std::pair<State, StateChange>>
    StackData;

struct StackEntry {
  const Instruction* instruction = nullptr;
  StackData data = std::nullopt;
};

class Stack {
 public:
  void setPointer(const Instruction* instruction, u16 pointer);
  void push(const Instruction* instruction, u24 data, size_t size);
  StackEntry popByte();
  std::vector<StackEntry> pop(size_t size);

 private:
  std::unordered_map<u16, StackEntry> memory;
  u16 pointer = 0x100;
  const Instruction* lastManipulator = nullptr;
};
