#include "cpu.hpp"
#include "instruction.hpp"
#include "log.hpp"
#include <catch2/catch.hpp>

TEST_CASE("Code in RAM does not get emulated", "[cpu]") {
  State state = {.pc = 0x7E0000};
  auto log = Log(nullptr);
  auto cpu = CPU(&log, state);

  bool keep_going = cpu.step();
  REQUIRE(keep_going == false);
}

TEST_CASE("LDA immediate instruction is emulated correctly", "[cpu]") {
  // LDA #$1234

  State state = {.pc = 0x0000, .m = 0};
  auto log = Log(nullptr);
  auto cpu = CPU(&log, state);
  auto instruction = Instruction(state, 0xA9, 0x1234);

  bool keep_going = cpu.execute(instruction);

  REQUIRE(cpu.state.pc == 0x0003);
  REQUIRE(keep_going == true);
}

TEST_CASE("JMP instruction is emulated correctly", "[cpu]") {
  // JMP $8000

  State state = {.pc = 0x800000};
  auto log = Log(nullptr);
  auto cpu = CPU(&log, state);
  auto instruction = Instruction(state, 0x4C, 0x8000);

  bool keep_going = cpu.execute(instruction);

  REQUIRE(cpu.state.pc == 0x808000);
  REQUIRE(keep_going == true);
}

TEST_CASE("RTS instruction is emulated correctly", "[cpu]") {
  // RTS

  State state = {};
  auto log = Log(nullptr);
  auto cpu = CPU(&log, state);
  auto instruction = Instruction(state, 0x60, 0x1234);

  bool keep_going = cpu.execute(instruction);

  REQUIRE(keep_going == false);
}
