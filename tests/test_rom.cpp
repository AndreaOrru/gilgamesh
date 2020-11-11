#include <catch2/catch.hpp>

#include "rom.hpp"

TEST_CASE("ROM object can recognize areas of RAM", "[rom]") {
  REQUIRE(ROM::isRAM(0x000000));
  REQUIRE(ROM::isRAM(0x001FFF));

  REQUIRE(ROM::isRAM(0x7E0000));
  REQUIRE(ROM::isRAM(0x7FFFFF));

  REQUIRE(!ROM::isRAM(0x002000));
  REQUIRE(!ROM::isRAM(0x800000));
  REQUIRE(!ROM::isRAM(0xC00000));
}
