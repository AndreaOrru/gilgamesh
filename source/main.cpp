#include "log.hpp"
#include "rom.hpp"
#include <cassert>
#include <fmt/core.h>
#include <iostream>

int main(int argc, char *argv[]) {
  assert(argc >= 2);

  char *rom_path = argv[1];
  auto rom = ROM(rom_path);

  auto log = Log(&rom);
  log.analyze();
  std::cout << log.disassembly();

  for (auto subroutine : log.unknownSubroutines()) {
    fmt::print("{:06X}", subroutine);
  }

  return 0;
}
