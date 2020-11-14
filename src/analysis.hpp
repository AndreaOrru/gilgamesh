#pragma once

#include <map>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>

#include "instruction.hpp"
#include "rom.hpp"
#include "state.hpp"
#include "subroutine.hpp"
#include "types.hpp"

struct EntryPoint {
  std::string label;
  u24 pc;
  State state;

  bool operator==(const EntryPoint& other) const;
  friend std::size_t hash_value(const EntryPoint& entryPoint);
};
typedef std::unordered_set<EntryPoint, boost::hash<EntryPoint>> EntryPointSet;

class Analysis {
 public:
  Analysis(const std::string& romPath);

  void run();
  void addInstruction(const Instruction& instruction);
  void addSubroutine(u24 pc, std::optional<std::string> label = std::nullopt);
  bool hasVisited(const Instruction& instruction) const;

  ROM rom;
  std::map<u24, Subroutine> subroutines;

 private:
  void clear();

  EntryPointSet entryPoints;
  std::unordered_map<u24, InstructionSet> instructions;
};
