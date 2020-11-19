#include <catch2/catch.hpp>
#include <variant>

#include "instruction.hpp"
#include "stack.hpp"

using namespace std;

TEST_CASE("Stack can push and pop one byte", "[stack]") {
  Stack stack;
  Instruction pha(0x48);

  stack.pushOne(0xFF, &pha);
  auto entry = stack.popOne();

  REQUIRE(get<u24>(entry.data) == 0xFF);
  REQUIRE(entry.instruction == &pha);
}

TEST_CASE("Stack can push and pop values", "[stack]") {
  Stack stack;
  Instruction jsr(0x20);
  Instruction pha(0x48);

  stack.push(2, 0x1234, &jsr);
  stack.pushOne(0x56, &pha);
  auto entries = stack.pop(3);

  REQUIRE(get<u24>(entries[0].data) == 0x56);
  REQUIRE(entries[0].instruction == &pha);

  REQUIRE(get<u24>(entries[1].data) == 0x34);
  REQUIRE(entries[1].instruction == &jsr);

  REQUIRE(get<u24>(entries[2].data) == 0x12);
  REQUIRE(entries[2].instruction == &jsr);
}

TEST_CASE("Matching values on stack works correctly", "[stack]") {
  Stack stack;
  Instruction pha(0x48);
  stack.push(2, 0x1234, &pha);

  REQUIRE(stack.matchValue(2, 0x1234));
  REQUIRE(!stack.matchValue(2, 0x1235));
  REQUIRE(!stack.matchValue(3, 0x123456));
}
