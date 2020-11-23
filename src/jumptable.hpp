#pragma once

#include <map>
#include <optional>

#include "types.hpp"

// Set of possible jump table statuses.
enum class JumpTableStatus {
  Unknown,
  Partial,
  Complete,
};

// Structure representing a jump table.
struct JumpTable {
  // FIXME: temporary, doesn't work in the general case.
  std::optional<std::pair<u16, u16>> range() const {
    if (targets.empty() || !targets.begin()->first.has_value()) {
      return std::nullopt;
    } else {
      return std::optional(
          std::pair{*targets.begin()->first, *targets.rbegin()->first});
    }
  };

  JumpTableStatus status;
  std::map<std::optional<u16>, InstructionPC> targets;
};
