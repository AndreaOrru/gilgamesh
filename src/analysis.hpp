#pragma once

#include <boost/container_hash/hash.hpp>
#include <boost/serialization/unordered_map.hpp>
#include <boost/serialization/unordered_set.hpp>
#include <map>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>

#include "assertion.hpp"
#include "instruction.hpp"
#include "jumptable.hpp"
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

  template <class Archive>
  void serialize(Archive& ar, const unsigned int) {
    ar& label;
    ar& pc;
    ar& state;
  }
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

  bool load();  // Try to load the analysis from a saved state.
  void save();  // Save the results of the analysis.

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
                     std::optional<std::string> label = std::nullopt,
                     bool isEntryPoint = false);

  // Define a jump table: caller spans a jumptable going from x to y (included).
  void defineJumpTable(InstructionPC callerPC,
                       std::pair<u16, u16> range,
                       JumpTableStatus status = JumpTableStatus::Partial);
  // Undefine a jump table.
  void undefineJumpTable(InstructionPC callerPC);

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
  std::optional<Label> getLabel(
      InstructionPC pc,
      std::optional<SubroutinePC> subroutinePC = std::nullopt) const;

  // Rename a subroutine or local label.
  void renameLabel(std::string newLabel,
                   InstructionPC pc,
                   std::optional<SubroutinePC> subroutinePC = std::nullopt);

  // The ROM being analyzed.
  const ROM rom;
  // Map from PC to the set of instructions at that address.
  std::unordered_map<InstructionPC, InstructionSet> instructions;
  // All the analyzed subroutines.
  std::map<SubroutinePC, Subroutine> subroutines;
  // Instructions referenced by other instructions.
  std::unordered_map<InstructionPC, ReferenceSet> references;

  // ROM's entry points.
  EntryPointSet entryPoints;

  // Instruction's comments.
  std::unordered_map<InstructionPC, std::string> comments;

  // Labels set by the user.
  std::unordered_map<PCPair, std::string, boost::hash<PCPair>> customLabels;

  // State change assertions.
  std::unordered_map<PCPair, Assertion, boost::hash<PCPair>> assertions;

  // Map from PC to jump tables.
  std::unordered_map<InstructionPC, JumpTable> jumpTables;

 private:
  void clear();                // Clear the results of the analysis.
  void reset();                // Reset the analysis (start from scratch).
  void generateLocalLabels();  // Generate local label names.

  friend class boost::serialization::access;
  template <class Archive>
  void serialize(Archive& ar, const unsigned int) {
    ar& entryPoints;
    ar& comments;
    ar& customLabels;
    ar& assertions;
    ar& jumpTables;
  }
};
