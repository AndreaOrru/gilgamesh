#include <catch2/catch.hpp>

#include "asar.hpp"

#include "rom.hpp"

TEST_CASE("ROM class can recognize areas of RAM", "[rom]") {
  SECTION("Bank $00") {
    REQUIRE(ROM::isRAM(0x000000));
    REQUIRE(ROM::isRAM(0x001FFF));
  }

  SECTION("Banks $7E-$7F") {
    REQUIRE(ROM::isRAM(0x7E0000));
    REQUIRE(ROM::isRAM(0x7FFFFF));
  }

  SECTION("Other banks (not RAM)") {
    REQUIRE(!ROM::isRAM(0x002000));
    REQUIRE(!ROM::isRAM(0x800000));
    REQUIRE(!ROM::isRAM(0xC00000));
  }
}

TEST_CASE("ROM types are correctly recognized", "[rom]") {
  SECTION("LoROM") {
    auto lorom = assemble("lorom");
    REQUIRE(lorom->romType == ROMType::LoROM);
  }

  SECTION("HiROM") {
    auto hirom = assemble("hirom");
    REQUIRE(hirom->romType == ROMType::HiROM);
  }
}

TEST_CASE("ROM size is correctly calculated", "[rom]") {
  auto roms = {assemble("lorom"), assemble("hirom")};
  for (auto rom : roms) {
    REQUIRE(rom->size() == 2048);
  }
}

TEST_CASE("ROM real size is correctly calculated", "[rom]") {
  SECTION("LoROM") {
    auto lorom = assemble("lorom");
    REQUIRE(lorom->realSize() == 0x8000);
  }

  SECTION("HiROM") {
    auto hirom = assemble("hirom");
    REQUIRE(hirom->realSize() == 0x10000);
  }
}

TEST_CASE("ROM title is extracted correctly", "[rom]") {
  auto roms = {assemble("lorom"), assemble("hirom")};
  for (auto rom : roms) {
    REQUIRE(rom->title() == "TEST");
  }
}

TEST_CASE("ROM address translation works correctly", "[rom]") {
  SECTION("LoROM") {
    auto lorom = assemble("lorom");
    REQUIRE(lorom->translate(0x008000) == 0x000000);
    REQUIRE(lorom->translate(0x808000) == 0x000000);
  }

  SECTION("HiROM") {
    auto hirom = assemble("hirom");
    REQUIRE(hirom->translate(0xC00000) == 0x000000);
    REQUIRE(hirom->translate(0xC08000) == 0x008000);
    REQUIRE(hirom->translate(0x400000) == 0x000000);
  }
}

TEST_CASE("ROM reads bytes correctly", "[rom]") {
  auto roms = {assemble("lorom"), assemble("hirom")};
  for (auto rom : roms) {
    REQUIRE(rom->readByte(Header::TITLE + 0) == 0x54);  // T
    REQUIRE(rom->readByte(Header::TITLE + 1) == 0x45);  // E
    REQUIRE(rom->readByte(Header::TITLE + 2) == 0x53);  // S
    REQUIRE(rom->readByte(Header::TITLE + 3) == 0x54);  // T
  }
}

TEST_CASE("ROM reads words correctly", "[rom]") {
  auto roms = {assemble("lorom"), assemble("hirom")};
  for (auto rom : roms) {
    REQUIRE(rom->readWord(Header::TITLE + 0) == 0x4554);
    REQUIRE(rom->readWord(Header::TITLE + 2) == 0x5453);
  }
}

TEST_CASE("ROM reads addresses (24-bits) correctly", "[rom]") {
  auto roms = {assemble("lorom"), assemble("hirom")};
  for (auto rom : roms) {
    REQUIRE(rom->readAddress(Header::TITLE + 0) == 0x534554);
    REQUIRE(rom->readAddress(Header::TITLE + 1) == 0x545345);
  }
}

TEST_CASE("ROM's RESET vector is extracted correctly", "[rom]") {
  auto roms = {assemble("lorom"), assemble("hirom")};
  for (auto rom : roms) {
    REQUIRE(rom->resetVector() == 0x8000);
  }
}

TEST_CASE("ROM's NMI vector is extracted correctly", "[rom]") {
  auto roms = {assemble("lorom"), assemble("hirom")};
  for (auto rom : roms) {
    REQUIRE(rom->nmiVector() == 0x0000);
  }
}
