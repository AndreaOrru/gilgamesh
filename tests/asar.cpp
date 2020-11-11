#include <cstdio>
#include <cstdlib>
#include <unordered_map>

#include "asar.hpp"
#include "rom.hpp"

using namespace std;

const ROM* assemble(const string& name) {
  static unordered_map<string, const ROM*> cache;
  auto romSearch = cache.find(name);
  if (romSearch != cache.end()) {
    return romSearch->second;
  }

  string sfcPath = "roms/" + name + ".sfc";
  string asmPath = "roms/" + name + ".asm";
  string command = "asar " + asmPath;
  remove(sfcPath.c_str());
  system(command.c_str());

  cache[name] = new ROM(sfcPath);
  return cache[name];
}
