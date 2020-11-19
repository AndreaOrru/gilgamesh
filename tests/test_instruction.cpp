#include <catch2/catch.hpp>

#include "instruction.hpp"

TEST_CASE("LDA instruction is parsed correctly", "[instruction]") {
  Instruction instruction(nullptr, 0x8000, 0x8000, 0xA9, 0x1234,
                          State(false, false));

  REQUIRE(instruction.name() == "lda");
  REQUIRE(instruction.operation() == Op::LDA);
  REQUIRE(instruction.addressMode() == AddressMode::ImmediateM);
  REQUIRE(instruction.type() == InstructionType::Other);
  REQUIRE(instruction.argumentSize() == 2);
  REQUIRE(instruction.size() == 3);
  REQUIRE(instruction.argument() == 0x1234);
  REQUIRE(instruction.absoluteArgument() == 0x1234);
  REQUIRE(instruction.argumentString() == "#$1234");
  REQUIRE(!instruction.isControl());
}

TEST_CASE("BRL instruction is parsed correctly", "[instruction]") {
  Instruction instruction(nullptr, 0x8000, 0x8000, 0x82, 0xFFFD,
                          State(false, false));

  REQUIRE(instruction.name() == "brl");
  REQUIRE(instruction.operation() == Op::BRL);
  REQUIRE(instruction.addressMode() == AddressMode::RelativeLong);
  REQUIRE(instruction.type() == InstructionType::Jump);
  REQUIRE(instruction.argumentSize() == 2);
  REQUIRE(instruction.size() == 3);
  REQUIRE(instruction.argument() == 0xFFFD);
  REQUIRE(instruction.absoluteArgument() == 0x8000);
  REQUIRE(instruction.argumentString() == "$FFFD");
  REQUIRE(instruction.isControl());
}
