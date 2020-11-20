#include <catch2/catch.hpp>

#include "analysis.hpp"
#include "asar.hpp"

using namespace std;

TEST_CASE("State inference correctly simplifies state changes", "[analysis]") {
  Analysis analysis(*assemble("elidable_state_change"));
  analysis.run();

  // Test there are two subroutines (+ NMI).
  REQUIRE(analysis.subroutines.size() - 1 == 2);

  // Test there's a `reset` subroutine with the correct number of instructions.
  auto resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 4);

  // Test there's a subroutine with the correct number of instructions.
  auto elidableChangeSubroutine = analysis.subroutines.at(0x800A);
  REQUIRE(elidableChangeSubroutine.instructions.size() == 6);

  // Test that the state is preserved.
  auto stateChanges = elidableChangeSubroutine.knownStateChanges;
  REQUIRE(stateChanges.size() == 1);
  auto stateChange = stateChanges.begin()->second;
  REQUIRE(stateChange.isEmpty());
}

TEST_CASE("Loops do not cause the analysis to hang", "[analysis]") {
  Analysis analysis(*assemble("infinite_loop"));
  analysis.run();

  // Check there is a single subroutine (+ NMI) with one instruction.
  REQUIRE(analysis.subroutines.size() - 1 == 1);
  REQUIRE(analysis.subroutines.at(0x8000).pc == 0x8000);
  REQUIRE(analysis.subroutines.at(0x8000).instructions.size() == 1);

  // Check there is a single instruction in the analysis.
  auto instructions = analysis.instructions;
  REQUIRE(instructions.size() == 1);
  REQUIRE(instructions.at(0x8000).size() == 1);

  // Check the instruction is a jump.
  auto jmp = instructions.at(0x8000).begin();
  REQUIRE(jmp->pc == 0x8000);
  REQUIRE(jmp->subroutinePC == 0x8000);
  REQUIRE(jmp->operation() == Op::JMP);

  // Check the instruction points to itself.
  REQUIRE(analysis.references.size() == 1);
  REQUIRE(analysis.references.at(0x8000).count({0x8000, 0x8000}));
}

TEST_CASE("PHP and PLP correctly preserve state", "[analysis]") {
  Analysis analysis(*assemble("php_plp"));
  analysis.run();

  // Test there are two subroutines (+ NMI).
  REQUIRE(analysis.subroutines.size() - 1 == 2);

  // Test there's a `reset` subroutine with the correct number of instructions.
  auto resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 4);
  REQUIRE(!resetSubroutine.savesStateInIncipit());

  // Test there's a PHP/PLP subroutine with the correct number of instructions.
  auto phpPlpSubroutine = analysis.subroutines.at(0x800A);
  REQUIRE(phpPlpSubroutine.instructions.size() == 5);
  REQUIRE(phpPlpSubroutine.savesStateInIncipit());

  // Test that the state is preserved.
  auto stateChanges = phpPlpSubroutine.knownStateChanges;
  REQUIRE(stateChanges.size() == 1);
  auto stateChange = stateChanges.begin()->second;
  REQUIRE(stateChange.isEmpty());
}

TEST_CASE("StateChange is propagated correctly between subroutines",
          "[analysis]") {
  Analysis analysis(*assemble("state_change"));
  analysis.run();

  // Test there are two subroutines (+ NMI).
  REQUIRE(analysis.subroutines.size() - 1 == 2);

  // Check the subroutines have the right name and number of instructions.
  auto resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 5);
  auto stateChangeSubroutine = analysis.subroutines.at(0x800E);
  REQUIRE(stateChangeSubroutine.label == "sub_00800E");
  REQUIRE(stateChangeSubroutine.instructions.size() == 2);

  // Check the `state_change` subroutine sets M/X to 0.
  auto stateChange = stateChangeSubroutine.knownStateChanges.begin()->second;
  REQUIRE(stateChangeSubroutine.knownStateChanges.size() == 1);
  REQUIRE(stateChange.m == false);
  REQUIRE(stateChange.x == false);

  // Check LDA and LDX have the right operand size.
  auto lda = analysis.instructions.at(0x8005).begin();
  REQUIRE(lda->operation() == Op::LDA);
  REQUIRE(lda->argument() == 0x1234);
  auto ldx = analysis.instructions.at(0x8008).begin();
  REQUIRE(ldx->operation() == Op::LDX);
  REQUIRE(ldx->argument() == 0x1234);
}
