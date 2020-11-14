#include <boost/container_hash/hash_fwd.hpp>

#include "analysis.hpp"
#include "cpu.hpp"
#include "instruction.hpp"

using namespace std;

bool EntryPoint::operator==(const EntryPoint& other) const {
  return pc == other.pc;
}

size_t hash_value(const EntryPoint& entryPoint) {
  size_t seed = 0;
  boost::hash_combine(seed, entryPoint.pc);
  return seed;
}

Analysis::Analysis(const ROM& rom) : rom{rom} {
  entryPoints = {
      {.label = "reset", .pc = rom.resetVector(), .state = State()},
      {.label = "nmi", .pc = rom.nmiVector(), .state = State()},
  };
}

void Analysis::clear() {
  instructions.clear();
  subroutines.clear();
}

void Analysis::run() {
  clear();

  for (auto& e : entryPoints) {
    addSubroutine(e.pc, e.label);
    CPU cpu(this, e.pc, e.pc, e.state);
    cpu.run();
  }
}

void Analysis::addInstruction(const Instruction& instruction) {
  auto& instructionSet = instructions.try_emplace(instruction.pc).first->second;
  auto instructionIter = instructionSet.insert(instruction).first;

  auto& subroutine = subroutines.at(instruction.subroutine);
  subroutine.addInstruction(&(*instructionIter));
}

void Analysis::addSubroutine(u24 pc, string label) {
  subroutines.try_emplace(pc, pc, label);
}

bool Analysis::hasVisited(const Instruction& instruction) const {
  auto search = instructions.find(instruction.pc);
  if (search != instructions.end()) {
    auto instructionSet = search->second;
    return instructionSet.count(instruction) > 0;
  }
  return false;
}
