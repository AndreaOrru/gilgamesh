#include "log.hpp"
#include "cpu.hpp"
#include "rom.hpp"
#include <fmt/core.h>

Log::Log(const ROM *rom) : rom(rom) {}

void Log::analyze() {
  auto entry_points = {rom->resetVector(), rom->nmiVector()};

  for (auto pc : entry_points) {
    auto cpu = CPU(this, {.pc = pc});
    cpu.run();
  }
}

std::string Log::disassembly() const {
  std::string result;
  for (auto &[pc, instruction] : instructions) {
    result += fmt::format("{:<20}; ${:06X}\n", instruction.toString(), pc);
  }
  return result;
}

std::pair<const Instruction &, bool>
Log::logInstruction(u24 subroutine, State state, u8 opcode, u24 argument) {
  auto insertion = instructions.try_emplace(state.pc, state, opcode, argument);
  Instruction &instruction = insertion.first->second;
  bool inserted = insertion.second;

  inserted = log.insert({{subroutine, state.pc}, instruction}).second;

  return {instruction, inserted};
}

void Log::logSubroutine(u24 subroutine,
                        std::optional<StateChange> state_change) {
  auto &state_changes =
      subroutine_state_changes.try_emplace(subroutine).first->second;

  if (state_change.has_value()) {
    state_changes.insert(*state_change);
  }
}

StateChangeSet Log::subroutineStateChanges(u24 subroutine) {
  return subroutine_state_changes.at(subroutine);
}

std::vector<u24> Log::unknownSubroutines() const {
  std::vector<u24> result;
  for (auto &[subroutine, state_changes] : subroutine_state_changes) {
    if (state_changes.size() != 1) {
      result.push_back(subroutine);
    }
  }
  return result;
}
