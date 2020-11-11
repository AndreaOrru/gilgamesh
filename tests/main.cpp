#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>

TEST_CASE("Test test", "[test]") {
  REQUIRE(1 == 1);
}
