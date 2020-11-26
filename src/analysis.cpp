#include <boost/archive/text_iarchive.hpp>
#include <boost/archive/text_oarchive.hpp>
#include <fstream>

#include "analysis.hpp"

#include "cpu.hpp"
#include "utils.hpp"

using namespace std;

/****************
 *  EntryPoint  *
 ****************/

// Hash table utils.
bool EntryPoint::operator==(const EntryPoint& other) const {
  return pc == other.pc;
}
size_t hash_value(const EntryPoint& entryPoint) {
  return entryPoint.pc;
}

/***************
 *  Reference  *
 ***************/

// Hash table utils.
bool Reference::operator==(const Reference& other) const {
  return target == other.target && subroutinePC == other.subroutinePC;
}
size_t hash_value(const Reference& reference) {
  size_t seed = 0;
  boost::hash_combine(seed, reference.target);
  boost::hash_combine(seed, reference.subroutinePC);
  return seed;
}

/**************
 *  Analysis  *
 **************/

// Construct an empty analysis.
Analysis::Analysis() {}

// Construct an analysis from a ROM object.
Analysis::Analysis(const ROM& rom) : rom{rom} {
  reset();
}

// Construct an analysis from a ROM path.
Analysis::Analysis(const std::string& romPath) : Analysis(ROM(romPath)) {}

// Clear the results of the analysis.
void Analysis::clear() {
  instructions.clear();
  subroutines.clear();
  references.clear();
}

// Reset the analysis (start from scratch).
void Analysis::reset() {
  clear();

  comments.clear();
  assertions.clear();
  jumpTables.clear();

  entryPoints = {
      {"reset", rom.resetVector(), State()},
      {"nmi", rom.nmiVector(), State()},
  };
}

// Try to load the analysis from a saved state.
bool Analysis::load() {
  try {
    ifstream file(rom.savePath());
    boost::archive::text_iarchive archive(file);
    clear();
    archive >> *this;
    return true;
  } catch (...) {
    return false;
  }
}

// Save the results of the analysis.
void Analysis::save() {
  ofstream file(rom.savePath());
  boost::archive::text_oarchive archive(file);
  archive << *this;
}

// Analyze the ROM.
void Analysis::run() {
  clear();

  for (auto& e : entryPoints) {
    addSubroutine(e.pc, e.label, true);
    CPU cpu(this, e.pc, e.pc, e.state);
    cpu.run();
  }

  generateLocalLabels();
}

// Add an entry point to the analysis.
void Analysis::addEntryPoint(string label, SubroutinePC pc, State state) {
  entryPoints.emplace(EntryPoint{label, pc, state});
}

// Add an instruction to the analysis.
Instruction* Analysis::addInstruction(InstructionPC pc,
                                      SubroutinePC subroutinePC,
                                      u8 opcode,
                                      u24 argument,
                                      State state) {
  // Retrieve the set of instructions for the given PC, or create a new one.
  auto& instructionSet = instructions.try_emplace(pc).first->second;
  // Insert the given instruction into the set.
  auto [instructionIter, inserted] =
      instructionSet.emplace(pc, subroutinePC, opcode, argument, state, this);
  // If the instruction was already present, return NULL.
  if (!inserted) {
    return nullptr;
  }

  // Add the instruction to its subroutine.
  auto& subroutine = subroutines.at(subroutinePC);
  auto instructionPtr = (Instruction*)&(*instructionIter);
  subroutine.addInstruction(instructionPtr);
  // Return a pointer to the new instruction.
  return instructionPtr;
}

// Add a reference from an instruction to another.
void Analysis::addReference(InstructionPC source,
                            InstructionPC target,
                            SubroutinePC subroutinePC) {
  auto& referenceSet = references.try_emplace(source).first->second;
  referenceSet.insert({target, subroutinePC});
}

// Add a subroutine to the analysis.
void Analysis::addSubroutine(SubroutinePC pc,
                             optional<string> label,
                             bool isEntryPoint) {
  auto labelValue = label.value_or(format("sub_%06X", pc));
  subroutines.try_emplace(pc, pc, labelValue, isEntryPoint);
}

// Get an assertion for an instruction, if any.
optional<Assertion> Analysis::getAssertion(InstructionPC pc,
                                           SubroutinePC subroutinePC) const {
  auto search = assertions.find({pc, subroutinePC});
  if (search != assertions.end()) {
    return search->second;
  } else {
    return nullopt;
  }
}

// Add a state change assertion to the analysis.
void Analysis::addAssertion(Assertion assertion,
                            InstructionPC pc,
                            SubroutinePC subroutinePC) {
  assertions.insert_or_assign({pc, subroutinePC}, assertion);
}

// Remove a state change assertion from the analysis.
void Analysis::removeAssertion(InstructionPC pc, SubroutinePC subroutinePC) {
  assertions.erase({pc, subroutinePC});
}

// Define a jump table: caller spans a jumptable going from x to y (included).
void Analysis::defineJumpTable(InstructionPC callerPC,
                               pair<u16, u16> range,
                               JumpTableStatus status) {
  auto& jumpTable = jumpTables.at(callerPC);
  auto caller = anyInstruction(callerPC);

  // TODO: support stepping by 3 for long addresses.
  // TODO: should we really clear at the beginning?
  jumpTable.targets.clear();
  for (int x = range.first; x <= range.second; x += 2) {
    auto offset = *caller->argument() + x;
    auto bank = caller->pc & 0xFF0000;
    auto target = bank | rom.readWord(bank | offset);
    jumpTable.targets.insert_or_assign(x, target);
  }
  jumpTable.status = status;
}

// Undefine a jump table.
void Analysis::undefineJumpTable(InstructionPC callerPC) {
  auto& jumpTable = jumpTables.at(callerPC);
  jumpTable.targets.clear();
  jumpTable.status = JumpTableStatus::Unknown;
}

// Return any of the instructions at address PC.
const Instruction* Analysis::anyInstruction(InstructionPC pc) {
  auto search = instructions.find(pc);
  if (search == instructions.end()) {
    return nullptr;
  } else {
    return &(*search->second.begin());
  }
}

// Return the label associated with an address, if any.
optional<string> Analysis::getLabel(InstructionPC pc,
                                    optional<SubroutinePC> subroutinePC) const {
  // Try to find a subroutine label first.
  auto subroutineSearch = subroutines.find(pc);
  if (subroutineSearch != subroutines.end()) {
    return subroutineSearch->second.label;
  }

  // Try to find an instruction label.
  if (!subroutinePC.has_value()) {
    return nullopt;
  }
  auto& subroutine = subroutines.at(*subroutinePC);
  auto* instruction = subroutine.instructions.at(pc);
  return instruction->label.has_value()
             ? optional(string(".") + *instruction->label)
             : nullopt;
}

// Generate local label names.
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
