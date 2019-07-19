#include "instruction.hpp"
#include <catch2/catch.hpp>

TEST_CASE("Instructions with 8-bit accumulator are correctly parsed",
          "[instruction]") {
  // LDA #$33

  State state = {.m = 1};
  auto instruction = Instruction(state, 0xA9, 0x112233);

  REQUIRE(instruction.name() == "lda");
  REQUIRE(instruction.operation() == LDA);
  REQUIRE(instruction.addressMode() == IMMEDIATE_M);
  REQUIRE(instruction.size() == 2);
  REQUIRE(instruction.argumentSize() == 1);
  REQUIRE(instruction.argument() == 0x33);
  REQUIRE(instruction.absoluteArgument() == 0x33);
  REQUIRE(instruction.isControl() == false);
  REQUIRE(instruction.toString() == "lda #$33");
}

TEST_CASE("Instructions with 16-bit accumulator are correctly parsed",
          "[instruction]") {
  // LDA #$2233

  State state = {.m = 0};
  auto instruction = Instruction(state, 0xA9, 0x112233);

  REQUIRE(instruction.name() == "lda");
  REQUIRE(instruction.operation() == LDA);
  REQUIRE(instruction.addressMode() == IMMEDIATE_M);
  REQUIRE(instruction.size() == 3);
  REQUIRE(instruction.argumentSize() == 2);
  REQUIRE(instruction.argument() == 0x2233);
  REQUIRE(instruction.absoluteArgument() == 0x2233);
  REQUIRE(instruction.isControl() == false);
  REQUIRE(instruction.toString() == "lda #$2233");
}

TEST_CASE("Instructions with 8-bit indexes are correctly parsed",
          "[instruction]") {
  // LDX #$33

  State state = {.x = 1};
  auto instruction = Instruction(state, 0xA2, 0x112233);

  REQUIRE(instruction.name() == "ldx");
  REQUIRE(instruction.operation() == LDX);
  REQUIRE(instruction.addressMode() == IMMEDIATE_X);
  REQUIRE(instruction.size() == 2);
  REQUIRE(instruction.argumentSize() == 1);
  REQUIRE(instruction.argument() == 0x33);
  REQUIRE(instruction.absoluteArgument() == 0x33);
  REQUIRE(instruction.isControl() == false);
  REQUIRE(instruction.toString() == "ldx #$33");
}

TEST_CASE("Instructions with 16-bit indexes are correctly parsed",
          "[instruction]") {
  // LDX #$2233

  State state = {.x = 0};
  auto instruction = Instruction(state, 0xA2, 0x112233);

  REQUIRE(instruction.name() == "ldx");
  REQUIRE(instruction.operation() == LDX);
  REQUIRE(instruction.addressMode() == IMMEDIATE_X);
  REQUIRE(instruction.size() == 3);
  REQUIRE(instruction.argumentSize() == 2);
  REQUIRE(instruction.argument() == 0x2233);
  REQUIRE(instruction.absoluteArgument() == 0x2233);
  REQUIRE(instruction.isControl() == false);
  REQUIRE(instruction.toString() == "ldx #$2233");
}

TEST_CASE("Branch instructions are correctly parsed", "[instruction]") {
  // BNE $(-08)

  State state = {.pc = 0x0006};
  auto instruction = Instruction(state, 0xD0, 0xF8);

  REQUIRE(instruction.name() == "bne");
  REQUIRE(instruction.operation() == BNE);
  REQUIRE(instruction.addressMode() == RELATIVE);
  REQUIRE(instruction.size() == 2);
  REQUIRE(instruction.argumentSize() == 1);
  REQUIRE(instruction.argument() == 0xF8);
  REQUIRE(instruction.absoluteArgument() == 0x0000);
  REQUIRE(instruction.isControl() == true);
  REQUIRE(instruction.isBranch() == true);
  REQUIRE(instruction.toString() == "bne $F8");
}
