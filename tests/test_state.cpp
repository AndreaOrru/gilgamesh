#include <catch2/catch.hpp>

#include "state.hpp"

using namespace std;

/***********
 *  State  *
 ***********/

TEST_CASE("State constructors work correctly", "[state]") {
  State defaultState;
  REQUIRE(defaultState.p == 0b00110000);

  State pState(0b00100000);
  REQUIRE(pState.p == 0b00100000);

  State mxState(true, true);
  REQUIRE(mxState.p == 0b00110000);
}

TEST_CASE("State calculation of register sizes are correct", "[state]") {
  State state(true, true);

  REQUIRE(state.sizeA() == 1);
  REQUIRE(state.sizeX() == 1);

  state.reset(0b00110000);
  REQUIRE(state.sizeA() == 2);
  REQUIRE(state.sizeX() == 2);
}

TEST_CASE("Setting flags in State via a mask works correctly", "[state]") {
  State state(0b00000000);

  state.set(0b00000000);
  REQUIRE(state.p == 0b00000000);

  state.set(0b11111111);
  REQUIRE(state.p == 0b11111111);
}

TEST_CASE("Resetting flags in State via a mask works correctly", "[state]") {
  State state(0b11111111);

  state.reset(0b00000000);
  REQUIRE(state.p == 0b11111111);

  state.reset(0b11111111);
  REQUIRE(state.p == 0b00000000);
}

/*****************
 *  StateChange  *
 *****************/

TEST_CASE("StateChange constructors work correctly", "[state]") {
  StateChange defaultStateChange;
  REQUIRE(!defaultStateChange.unknown());
  REQUIRE(defaultStateChange.m == nullopt);
  REQUIRE(defaultStateChange.x == nullopt);

  StateChange unknownStateChange(UnknownReason::MutableCode);
  REQUIRE(unknownStateChange.unknownReason == UnknownReason::MutableCode);

  StateChange mxStateChange(nullopt, true);
  REQUIRE(!mxStateChange.unknown());
  REQUIRE(mxStateChange.m == nullopt);
  REQUIRE(mxStateChange.x == true);
}

TEST_CASE("Setting flags in StateChange via a mask works correctly",
          "[state]") {
  StateChange stateChange;
  stateChange.set(0b00110000);

  REQUIRE(stateChange.m == true);
  REQUIRE(stateChange.x == true);
}

TEST_CASE("Resetting flags in StateChange via a mask works correctly",
          "[state]") {
  StateChange stateChange;
  stateChange.reset(0b00110000);

  REQUIRE(stateChange.m == false);
  REQUIRE(stateChange.x == false);
}

TEST_CASE("Applying a state inference to a StateChange works correctly",
          "[state]") {
  StateChange mx(true, false);
  StateChange inference(true, false);
  mx.applyInference(inference);

  REQUIRE(mx.m == nullopt);
  REQUIRE(mx.x == nullopt);
}
