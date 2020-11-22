#include <catch2/catch.hpp>

#include "asar.hpp"

#include "analysis.hpp"
#include "assertion.hpp"

using namespace std;

TEST_CASE("Assertions work correctly", "[analysis]") {
  Analysis analysis(*assemble("assertions"));
  analysis.run();

  REQUIRE(analysis.subroutines.size() - 1 == 2);

  auto& resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 1);
  REQUIRE(resetSubroutine.isUnknownBecauseOf(UnknownReason::Unknown));

  auto& unknownSubroutine = analysis.subroutines.at(0x8005);
  REQUIRE(unknownSubroutine.instructions.size() == 1);
  REQUIRE(unknownSubroutine.isUnknownBecauseOf(UnknownReason::IndirectJump));

  analysis.setAssertion(Assertion(AssertionType::Instruction), 0x8000, 0x8000);
  analysis.run();

  resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.instructions.size() == 2);
  REQUIRE(resetSubroutine.unknownStateChanges.empty());

  analysis.setAssertion(Assertion(AssertionType::Subroutine), 0x8005, 0x8005);
  analysis.run();

  unknownSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(unknownSubroutine.unknownStateChanges.empty());
}

TEST_CASE("State inference correctly simplifies state changes", "[analysis]") {
  Analysis analysis(*assemble("elidable_state_change"));
  analysis.run();

  // Test there are two subroutines (+ NMI).
  REQUIRE(analysis.subroutines.size() - 1 == 2);

  // Test there's a `reset` subroutine with the correct number of instructions.
  auto& resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 4);

  // Test there's a subroutine with the correct number of instructions.
  auto& elidableChangeSubroutine = analysis.subroutines.at(0x800A);
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
  auto& instructions = analysis.instructions;
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

TEST_CASE("Jump tables are handled correctly", "[analysis]") {
  Analysis analysis(*assemble("jump_tables"));
  analysis.run();

  // Test that there's a single subroutine, which is unknown
  // because of an unexplored indirect jump instruction.
  auto& resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 1);
  REQUIRE(resetSubroutine.isUnknownBecauseOf(UnknownReason::IndirectJump));

  // Specify the limits of the jump table.
  analysis.defineJumpTable(0x8000, {0, 2});
  analysis.run();

  // Verify that the subroutines pointed by
  // the jumptable have been explored.
  {
    REQUIRE(analysis.subroutines.size() - 1 == 3);
    REQUIRE(analysis.subroutines.count(0x8100) == 1);
    REQUIRE(analysis.subroutines.count(0x8200) == 1);
  }
}

TEST_CASE("PHP and PLP correctly preserve state", "[analysis]") {
  Analysis analysis(*assemble("php_plp"));
  analysis.run();

  // Test there are two subroutines (+ NMI).
  REQUIRE(analysis.subroutines.size() - 1 == 2);

  // Test there's a `reset` subroutine with the correct number of instructions.
  auto& resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 4);
  REQUIRE(!resetSubroutine.savesStateInIncipit());

  // Test there's a PHP/PLP subroutine with the correct number of instructions.
  auto& phpPlpSubroutine = analysis.subroutines.at(0x800A);
  REQUIRE(phpPlpSubroutine.instructions.size() == 5);
  REQUIRE(phpPlpSubroutine.savesStateInIncipit());

  // Test that the state is preserved.
  auto stateChanges = phpPlpSubroutine.knownStateChanges;
  REQUIRE(stateChanges.size() == 1);
  auto stateChange = stateChanges.begin()->second;
  REQUIRE(stateChange.isEmpty());
}

TEST_CASE("Overlapping StateChanges are simplified when propagating",
          "[analysis]") {
  Analysis analysis(*assemble("simplified_state_changes"));
  analysis.run();

  // Test there are two subroutines (+ NMI).
  REQUIRE(analysis.subroutines.size() - 1 == 2);

  // Test there's a `reset` subroutine with the correct number of instructions.
  auto& resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 5);

  // Test there's a `double_state_change` subroutine
  // with the correct number of instructions.
  auto& doubleStateSubroutine = analysis.subroutines.at(0x800E);
  REQUIRE(doubleStateSubroutine.instructions.size() == 5);

  // Test that the state is simplified.
  REQUIRE(doubleStateSubroutine.knownStateChanges.size() == 2);
  REQUIRE(doubleStateSubroutine.unknownStateChanges.empty());
}

TEST_CASE("StateChange is propagated correctly between subroutines",
          "[analysis]") {
  Analysis analysis(*assemble("state_change"));
  analysis.run();

  // Test there are two subroutines (+ NMI).
  REQUIRE(analysis.subroutines.size() - 1 == 2);

  // Check the subroutines have the right name and number of instructions.
  auto& resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 5);
  auto& stateChangeSubroutine = analysis.subroutines.at(0x800E);
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

TEST_CASE("Entry points can be added and analyzed", "[analysis]") {
  Analysis analysis(*assemble("unknown_call_jump"));
  analysis.run();

  // Test there are two subroutines (including NMI).
  REQUIRE(analysis.subroutines.size() == 2);

  // Check the subroutines have the right name and number of instructions.
  auto& resetSubroutine = analysis.subroutines.at(0x8000);
  REQUIRE(resetSubroutine.label == "reset");
  REQUIRE(resetSubroutine.instructions.size() == 1);
  REQUIRE(resetSubroutine.unknownStateChanges.size() == 1);

  auto& nmiSubroutine = analysis.subroutines.at(0x8003);
  REQUIRE(nmiSubroutine.label == "nmi");
  REQUIRE(nmiSubroutine.instructions.size() == 2);
  REQUIRE(nmiSubroutine.unknownStateChanges.size() == 1);

  // Test adding a custom entry point.
  analysis.addEntryPoint("loop", 0x9002);
  analysis.run();

  auto& loopSubroutine = analysis.subroutines.at(0x9002);
  REQUIRE(loopSubroutine.label == "loop");
  REQUIRE(loopSubroutine.instructions.size() == 1);
}
