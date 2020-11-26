#pragma once

#include <boost/serialization/map.hpp>
#include <map>
#include <optional>

#include "boost_serialization_std_optional.hpp"
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

  template <class Archive>
  void serialize(Archive& ar, const unsigned int) {
    ar& status;
    ar& targets;
  }
};
