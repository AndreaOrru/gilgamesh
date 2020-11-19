#pragma once

#include <boost/container_hash/hash.hpp>
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

/**
 * ROM's entry point.
 */
struct EntryPoint {
  std::string label;  // Subroutine's label.
  SubroutinePC pc;    // Subroutine's PC.
  State state;        // CPU's state.

  // Hash table utils.
  bool operator==(const EntryPoint& other) const;
  friend std::size_t hash_value(const EntryPoint& entryPoint);
};
// Set of EntryPoints.
typedef std::unordered_set<EntryPoint, boost::hash<EntryPoint>> EntryPointSet;

/**
 * Code reference.
 */
struct Reference {
  InstructionPC target;
  SubroutinePC subroutinePC;

  // Hash table utils.
  bool operator==(const Reference& other) const;
  friend std::size_t hash_value(const Reference& reference);
};
// Set of References.
typedef std::unordered_set<Reference, boost::hash<Reference>> ReferenceSet;

/**
 * Type of state assertions.
 */
enum class AssertionType {
  Instruction,
  Subroutine,
};

/**
 * Structure representing a state assertion.
 */
struct Assertion {
  AssertionType type;
  StateChange stateChange;
};

/**
 * Class holding the state of the ROM's analysis.
 */
class Analysis {
 public:
  // Construct an empty analysis.
  Analysis();
  // Construct an analysis from a ROM path.
  Analysis(const std::string& romPath);

  // Analyze the ROM.
  void run();

  // Add an instruction to the analysis.
  Instruction* addInstruction(InstructionPC pc,
                              SubroutinePC subroutinePC,
                              u8 opcode,
                              u24 argument,
                              State state);

  // Add a reference from an instruction to another.
  void addReference(InstructionPC source,
                    InstructionPC target,
                    SubroutinePC subroutinePC);

  // Add a subroutine to the analysis.
  void addSubroutine(SubroutinePC pc,
                     std::optional<std::string> label = std::nullopt);

  // Get an assertion for the current instruction, if any.
  std::optional<Assertion> getAssertion(InstructionPC pc,
                                        SubroutinePC subroutinePC);

  // The ROM being analyzed.
  ROM rom;
  // ROM's entry points.
  EntryPointSet entryPoints;

  // Map from PC to the set of instructions at that address.
  std::unordered_map<InstructionPC, InstructionSet> instructions;
  // All the analyzed subroutines.
  std::map<SubroutinePC, Subroutine> subroutines;
  // Instructions referenced by other instructions.
  std::unordered_map<InstructionPC, ReferenceSet> references;

  // Assertions on instruction state changes.
  std::unordered_map<InstructionPC, StateChange> instructionAssertions;
  // Assertions on subroutine state changes.
  std::unordered_map<std::pair<InstructionPC, SubroutinePC>,
                     StateChange,
                     boost::hash<std::pair<InstructionPC, SubroutinePC>>>
      subroutineAssertions;

 private:
  void clear();                // Clear the results of the analysis.
  void generateLocalLabels();  // Generate local label names.
};
