#include <cstdio>
#include <cstdlib>

#include "asar.hpp"

using namespace std;

ROM assemble(const string& name) {
  string sfcPath = "roms/" + name + ".sfc";
  remove(sfcPath.c_str());

  string asmPath = "roms/" + name + ".asm";
  string command = "asar " + asmPath;
  system(command.c_str());

  return ROM(sfcPath);
}
