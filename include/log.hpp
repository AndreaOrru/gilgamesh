#pragma once
#include "instruction.hpp"
#include "state.hpp"
#include <boost/container_hash/hash.hpp>
#include <map>
#include <unordered_map>
#include <unordered_set>

class ROM;

typedef std::unordered_set<StateChange, boost::hash<StateChange>>
    StateChangeSet;

class Log {
public:
  const ROM *rom;
  std::map<u24, Instruction> instructions;

  Log(const ROM *rom);
  void analyze();
  std::string disassembly() const;
  std::vector<u24> unknownSubroutines() const;

  void logSubroutine(u24 subroutine,
                     std::optional<StateChange> state_change = {});
  StateChangeSet subroutineStateChanges(u24 subroutine);

  std::pair<const Instruction &, bool>
  logInstruction(u24 subroutine, State state, u8 opcode, u24 argument);

private:
  std::map<std::pair<u24, u24>, Instruction &> log;
  std::unordered_map<u24, StateChangeSet> subroutine_state_changes;
};
