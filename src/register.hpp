#pragma once

#include <optional>

#include "types.hpp"

class CPU;

struct Register {
  // Constructor.
  Register(CPU* cpu, bool isAccumulator = true);

  size_t size();             // Size of the register (8/16 bits).
  std::optional<u16> get();  // Get the value of the register (8 or 16 bits).
  // Get the full value of the register (16 bits).
  std::optional<u16> getWhole();
  // Set the value of the register.
  void set(std::optional<u16> value);
  // Set the full value of the register (16 bits).
  void setWhole(std::optional<u16> value);

  CPU* cpu;              // Pointer to the CPU object.
  bool isAccumulator;    // True if A, false if X.
  std::optional<u8> lo;  // Lower 8 bits of the register.
  std::optional<u8> hi;  // Higher 8 bits of the register.
};
