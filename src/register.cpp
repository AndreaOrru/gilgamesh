#include "register.hpp"

#include "cpu.hpp"

using namespace std;

// Constructor.
Register::Register(CPU* cpu, bool isAccumulator)
    : cpu{cpu}, isAccumulator{isAccumulator} {}

// Size of the register (8/16 bits).
size_t Register::size() {
  return isAccumulator ? cpu->state.sizeA() : cpu->state.sizeX();
}

// Get the value of the register (8 or 16 bits).
optional<u16> Register::get() {
  return size() == 1 ? optional<u16>(lo) : getWhole();
}

// Get the full value of the register (16 bits).
optional<u16> Register::getWhole() {
  if (lo.has_value() && hi.has_value()) {
    return (*hi << 8) | *lo;
  } else {
    return nullopt;
  }
}

// Set the value of the register.
void Register::set(optional<u16> value) {
  if (value.has_value()) {
    lo = *value & 0xFF;
    if (size() > 1) {
      hi = (*value >> 8) & 0xFF;
    }
  } else {
    lo = nullopt;
    if (size() > 1) {
      hi = nullopt;
    }
  }
}

// Set the full value of the register (16 bits).
void Register::setWhole(optional<u16> value) {
  if (value.has_value()) {
    lo = *value & 0xFF;
    hi = (*value >> 8) & 0xFF;
  } else {
    lo = nullopt;
    hi = nullopt;
  }
}
