#include <catch2/catch.hpp>

#include "analysis.hpp"
#include "cpu.hpp"

using namespace std;

pair<CPU, Analysis*> setupCPU(u8 p, bool stop = true) {
  auto analysis = new Analysis;
  analysis->addSubroutine(0x8000, nullopt);

  CPU cpu(analysis, 0x8000, 0x8000, State(p));
  cpu.stop = stop;

  return {cpu, analysis};
}

void runInstruction(CPU& cpu, u8 opcode, u24 argument) {
  Instruction instruction(cpu.analysis, cpu.pc, cpu.subroutinePC, opcode,
                          argument, cpu.state);
  cpu.execute(&instruction);
}

TEST_CASE("CPU emulates branches correctly", "[cpu]") {
  auto [cpu, analysis] = setupCPU(0b00000000);
  runInstruction(cpu, 0x90, 0x10);  // BCC.

  REQUIRE(cpu.pc == 0x8012);

  delete analysis;
}

TEST_CASE("CPU emulates calls correctly", "[cpu]") {
  auto [cpu, analysis] = setupCPU(0b00000000);
  runInstruction(cpu, 0x20, 0x9000);  // JSR.

  REQUIRE(cpu.pc == 0x8003);
  REQUIRE(analysis->subroutines.count(0x9000) > 0);

  delete analysis;
}

TEST_CASE("CPU emulates BRK correctly", "[cpu]") {
  auto [cpu, analysis] = setupCPU(0b00000000, false);
  runInstruction(cpu, 0x00, 0x00);  // BRK.

  REQUIRE(cpu.stop == true);

  delete analysis;
}

TEST_CASE("CPU emulates jumps correctly", "[cpu]") {
  auto [cpu, analysis] = setupCPU(0b00000000);
  runInstruction(cpu, 0x4C, 0x9000);  // JMP.

  REQUIRE(analysis->references.at(0x8000).count({0x9000, cpu.subroutinePC}) >
          0);

  delete analysis;
}

TEST_CASE("CPU emulates returns correctly", "[cpu]") {
  auto [cpu, analysis] = setupCPU(0b00000000);
  runInstruction(cpu, 0x60, 0x9000);  // RTS.

  REQUIRE(cpu.stop == true);
  delete analysis;
}

TEST_CASE("CPU emulates SEP/REP correctly", "[cpu]") {
  auto [cpu, analysis] = setupCPU(0b00000000);

  SECTION("SEP") {
    runInstruction(cpu, 0xE2, 0x30);  // SEP.
    REQUIRE(cpu.pc == 0x8002);
    REQUIRE(cpu.state.p == 0b00110000);
  }

  SECTION("REP") {
    runInstruction(cpu, 0xC2, 0x30);  // REP.
    REQUIRE(cpu.pc == 0x8002);
    REQUIRE(cpu.state.p == 0b00000000);
  }

  delete analysis;
}
