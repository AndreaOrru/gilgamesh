#include "log.hpp"
#include "rom.hpp"
#include <catch2/catch.hpp>

TEST_CASE("Infinite loops are handled correctly", "[log]") {
  auto rom = ROM("roms/infinite_loop.sfc");
  auto log = Log(&rom);
  log.analyze();
}

TEST_CASE("State change in subroutines is propagated", "[log]") {
  auto rom = ROM("roms/state_change.sfc");
  auto log = Log(&rom);
  log.analyze();

  auto &lda = log.instructions.at(0x8005);
  REQUIRE(lda.argumentSize() == 2);
}

TEST_CASE("Elidable state changes in subroutines is not propagated", "[log]") {
  auto rom = ROM("roms/elidable_state_change.sfc");
  auto log = Log(&rom);
  log.analyze();

  auto state_changes = log.subroutineStateChanges(0x800A);
  REQUIRE(state_changes.size() == 1);

  auto &state_change = *state_changes.begin();
  REQUIRE(state_change.m.has_value() == false);
  REQUIRE(state_change.x.has_value() == false);
}

TEST_CASE("PHP and PLP prevent state changes from being propagated", "[log]") {
  auto rom = ROM("roms/php_plp.sfc");
  auto log = Log(&rom);
  log.analyze();

  auto state_changes = log.subroutineStateChanges(0x800A);
  REQUIRE(state_changes.size() == 1);

  auto &state_change = *state_changes.begin();
  REQUIRE(state_change.m.has_value() == false);
  REQUIRE(state_change.x.has_value() == false);
}

TEST_CASE(
    "Jumping to a previously visited subroutine propagates state correctly",
    "[log]") {
  auto rom = ROM("roms/jump_inside_subroutine.sfc");
  auto log = Log(&rom);
  log.analyze();

  auto state_changes = log.subroutineStateChanges(0x8016);
  REQUIRE(state_changes.size() == 1);
}
