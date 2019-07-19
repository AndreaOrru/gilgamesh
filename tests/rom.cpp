#include "rom.hpp"
#include <catch2/catch.hpp>

TEST_CASE("ROM properties of a LoROM are correctly read", "[rom]") {
  auto rom = ROM("roms/lorom.sfc");

  REQUIRE(rom.type() == LOROM);
  REQUIRE(rom.title() == "TEST");
  REQUIRE(rom.resetVector() == 0x8000);
}

TEST_CASE("Reading values from the ROM works correctly", "[rom]") {
  auto rom = ROM("roms/infinite_loop.sfc");

  REQUIRE(rom.readByte(0x8000) == 0x4C);
  REQUIRE(rom.readWord(0x8001) == 0x8000);
  REQUIRE(rom.readAddress(0x8000) == 0x80004C);
}
