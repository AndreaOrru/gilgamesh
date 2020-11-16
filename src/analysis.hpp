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
  u24 pc;             // Subroutine's PC.
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
  u24 target;
  u24 subroutinePC;

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
  Analysis(const std::string& romPath);  // Constructor.
  void run();                            // Analyze the ROM.

  // Add an instruction to the analysis.
  Instruction* addInstruction(u24 pc,
                              u24 subroutinePC,
                              u8 opcode,
                              u24 argument,
                              State state);

  // Add a reference from an instruction to another.
  void addReference(u24 source, u24 target, u24 subroutinePC);

  // Add a subroutine to the analysis.
  void addSubroutine(u24 pc, std::optional<std::string> label = std::nullopt);

  ROM rom;                                // The ROM being analyzed.
  std::map<u24, Subroutine> subroutines;  // All the analyzed subroutines.

 private:
  void clear();                // Clear the results of the analysis.
  void generateLocalLabels();  // Generate local label names.

  // ROM's entry points.
  EntryPointSet entryPoints;

  // Map from PC to the set of instructions at that address.
  std::unordered_map<u24, InstructionSet> instructions;

  // Instructions referenced by other instructions.
  std::unordered_map<u24, ReferenceSet> references;
};
