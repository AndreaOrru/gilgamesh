#pragma once

#include <optional>
#include <unordered_map>
#include <variant>
#include <vector>

#include "state.hpp"
#include "types.hpp"

// typedef std::variant<u24, std::pair<State, StateChange>> StackEntry;

class Stack {
 public:
  void setPointer(u16 pointer);
  void push(u24 data, size_t size);
  std::optional<u8> popByte();
  std::vector<std::optional<u8>> pop(size_t size);

 private:
  std::unordered_map<u16, u8> memory;
  u16 pointer = 0x100;
};
