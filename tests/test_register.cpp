#include <catch2/catch.hpp>

#include "analysis.hpp"
#include "cpu.hpp"
#include "register.hpp"

using namespace std;

pair<CPU, Analysis*> setupCPU(bool m, bool x) {
  auto analysis = new Analysis;
  CPU cpu(analysis, 0x8000, 0x8000, State(m, x));
  return {cpu, analysis};
}

TEST_CASE("Registers report the correct size", "[register]") {
  auto [cpu, analysis] = setupCPU(true, false);
  Register A(&cpu, true);
  Register X(&cpu, false);

  REQUIRE(A.size() == 1);
  REQUIRE(X.size() == 2);

  cpu.state.m = false;
  cpu.state.x = true;

  REQUIRE(A.size() == 2);
  REQUIRE(X.size() == 1);

  delete analysis;
}

TEST_CASE("Register values are set correctly according to state",
          "[register]") {
  auto [cpu, analysis] = setupCPU(true, true);
  Register A(&cpu, true);

  // Only lower 8-bits known.
  A.set(0xFF);
  REQUIRE(A.get() == 0xFF);
  // 16-bits unknown.
  cpu.state.m = false;
  REQUIRE(A.get() == nullopt);

  // 16-bits known.
  A.set(0xFFFF);
  REQUIRE(A.get() == 0xFFFF);
  // 8-bits known.
  cpu.state.m = true;
  REQUIRE(A.get() == 0xFF);

  // 16-bits unknown.
  cpu.state.m = false;
  A.set(nullopt);
  REQUIRE(A.get() == nullopt);
  // 8-bits unknown.
  cpu.state.m = true;
  REQUIRE(A.get() == nullopt);
}

TEST_CASE("Whole register values can be set correctly", "[register]") {
  auto [cpu, analysis] = setupCPU(true, true);
  Register A(&cpu, true);

  A.setWhole(0xFFFF);
  REQUIRE(A.get() == 0xFF);
  REQUIRE(A.getWhole() == 0xFFFF);

  cpu.state.m = false;
  REQUIRE(A.get() == 0xFFFF);
}
