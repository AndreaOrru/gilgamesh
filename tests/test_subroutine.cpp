#include <catch2/catch.hpp>

#include "subroutine.hpp"

TEST_CASE("Adding state changes to subroutines works correctly",
          "[subroutine]") {
  Subroutine subroutine(0x8000, "reset");

  subroutine.addStateChange(0x8000, StateChange());
  REQUIRE(subroutine.knownStateChanges.size() == 1);
  REQUIRE(subroutine.unknownStateChanges.size() == 0);

  subroutine.addStateChange(0x8000, StateChange(UnknownReason::Unknown));
  REQUIRE(subroutine.knownStateChanges.size() == 1);
  REQUIRE(subroutine.unknownStateChanges.size() == 1);
}
