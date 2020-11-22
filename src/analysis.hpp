#pragma once

#include <boost/container_hash/hash.hpp>
#include <map>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>

#include "assertion.hpp"
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

// Set of possible jump table statuses.
enum JumpTableStatus {
  Unknown,
  Empty,
  Partial,
  Complete,
};

// Structure representing a jump table.
struct JumpTable {
  JumpTableStatus status;
  std::map<std::optional<u16>, InstructionPC> targets;
};

/**
 * Class holding the state of the ROM's analysis.
 */
class Analysis {
 public:
  // Construct an empty analysis.
  Analysis();
  // Construct an analysis from a ROM object.
  Analysis(const ROM& rom);
  // Construct an analysis from a ROM path.
  Analysis(const std::string& romPath);

  // Analyze the ROM.
  void run();

  // Add an entry point to the analysis.
  void addEntryPoint(std::string label, SubroutinePC pc, State state = State());

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

  // Define a jump table: caller spans a jumptable going from x to y (included).
  void defineJumpTable(InstructionPC callerPC,
                       std::pair<u16, u16> range,
                       JumpTableStatus status = JumpTableStatus::Partial);

  // Return any of the instructions at address PC.
  const Instruction* anyInstruction(InstructionPC pc);

  // Get an assertion for the current instruction, if any.
  std::optional<Assertion> getAssertion(InstructionPC pc,
                                        SubroutinePC subroutinePC) const;
  // Add a state change assertion to the analysis.
  void addAssertion(Assertion assertion,
                    InstructionPC pc,
                    SubroutinePC subroutinePC);
  // Remove a state change assertion from the analysis.
  void removeAssertion(InstructionPC pc, SubroutinePC subroutinePC);

  // Return the label associated with an address, if any.
  std::optional<std::string> getLabel(
      InstructionPC pc,
      std::optional<SubroutinePC> subroutinePC = std::nullopt) const;

  // The ROM being analyzed.
  const ROM rom;
  // ROM's entry points.
  EntryPointSet entryPoints;

  // Map from PC to the set of instructions at that address.
  std::unordered_map<InstructionPC, InstructionSet> instructions;
  // All the analyzed subroutines.
  std::map<SubroutinePC, Subroutine> subroutines;
  // Instructions referenced by other instructions.
  std::unordered_map<InstructionPC, ReferenceSet> references;
  // Instruction's comments.
  std::unordered_map<InstructionPC, std::string> comments;

  // State change assertions.
  std::unordered_map<std::pair<InstructionPC, SubroutinePC>,
                     Assertion,
                     boost::hash<std::pair<InstructionPC, SubroutinePC>>>
      assertions;

  // Map from PC to jump tables.
  std::unordered_map<InstructionPC, JumpTable> jumpTables;

 private:
  void clear();                // Clear the results of the analysis.
  void generateLocalLabels();  // Generate local label names.
};
