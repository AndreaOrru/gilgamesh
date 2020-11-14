#pragma once

#include <boost/container_hash/hash.hpp>
#include <optional>
#include <string>
#include <unordered_set>

#include "opcodes.hpp"
#include "state.hpp"
#include "types.hpp"

class Analysis;
class Subroutine;

enum class InstructionType {
  Branch,
  Call,
  Interrupt,
  Other,
  Jump,
  Pop,
  Push,
  Return,
  SepRep,
};

class Instruction {
 public:
  Instruction(Analysis* analysis,
              u24 pc,
              u24 subroutine,
              u8 opcode,
              u24 argument,
              State state);

  bool operator==(const Instruction& other) const;
  friend std::size_t hash_value(const Instruction& instruction);

  std::string name() const;
  Op operation() const;
  AddressMode addressMode() const;
  InstructionType type() const;
  bool isControl() const;
  size_t size() const;
  size_t argumentSize() const;
  std::optional<u24> argument() const;
  std::optional<u24> absoluteArgument() const;
  std::string argumentString() const;
  std::string toString() const;

  u24 pc;
  u24 subroutine;
  std::optional<std::string> label = std::nullopt;

 private:
  Analysis* analysis;
  u8 opcode;
  u24 _argument;
  State state;
};

typedef std::unordered_set<Instruction, boost::hash<Instruction>>
    InstructionSet;
