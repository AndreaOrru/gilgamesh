#include <boost/container_hash/hash_fwd.hpp>

#include "analysis.hpp"

#include "cpu.hpp"
#include "instruction.hpp"
#include "utils.hpp"

using namespace std;

bool EntryPoint::operator==(const EntryPoint& other) const {
  return pc == other.pc;
}

size_t hash_value(const EntryPoint& entryPoint) {
  size_t seed = 0;
  boost::hash_combine(seed, entryPoint.pc);
  return seed;
}

bool Reference::operator==(const Reference& other) const {
  return target == other.target && subroutinePC == other.subroutinePC;
}

size_t hash_value(const Reference& reference) {
  size_t seed = 0;
  boost::hash_combine(seed, reference.target);
  boost::hash_combine(seed, reference.subroutinePC);
  return seed;
}

Analysis::Analysis(const std::string& romPath) : rom(romPath) {
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

  generateLocalLabels();
}

Instruction* Analysis::addInstruction(u24 pc,
                                      u24 subroutinePC,
                                      u8 opcode,
                                      u24 argument,
                                      State state) {
  auto& instructionSet = instructions.try_emplace(pc).first->second;
  auto [instructionIter, inserted] =
      instructionSet.emplace(this, pc, subroutinePC, opcode, argument, state);
  if (!inserted) {
    return nullptr;
  }

  auto& subroutine = subroutines.at(subroutinePC);
  auto instructionPtr = (Instruction*)&(*instructionIter);
  subroutine.addInstruction(instructionPtr);
  return instructionPtr;
}

void Analysis::addReference(u24 source, u24 target, u24 subroutinePC) {
  auto& referenceSet = references.try_emplace(source).first->second;
  referenceSet.insert({target, subroutinePC});
}

void Analysis::addSubroutine(u24 pc, optional<string> label) {
  auto labelValue = label.value_or(format("sub_%06X", pc));
  subroutines.try_emplace(pc, pc, labelValue);
}

bool Analysis::hasVisited(const Instruction& instruction) const {
  auto search = instructions.find(instruction.pc);
  if (search != instructions.end()) {
    auto instructionSet = search->second;
    return instructionSet.count(instruction) > 0;
  }
  return false;
}

void Analysis::generateLocalLabels() {
  for (auto& [source, referenceSet] : references) {
    for (auto& [target, subroutinePC] : referenceSet) {
      if (subroutines.count(target) == 0) {
        auto& subroutine = subroutines.at(subroutinePC);
        auto& instruction = subroutine.instructions.at(target);
        instruction->label = format("loc_%06X", target);
      }
    }
  }
}
