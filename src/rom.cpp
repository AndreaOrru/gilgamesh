#include "rom.hpp"
#include "utils.hpp"

using namespace std;

ROM::ROM(const string& path) : path{path} {
  data = readBinaryFile(path);
};

u8 ROM::readByte(const u24 address) {
  return data[address];
}

u16 ROM::readWord(const u24 address) {
  u8 lo = readByte(address);
  u8 hi = readByte(address + 1);
  return (hi << 8) | lo;
}

u24 ROM::readAddress(const u24 address) {
  u16 lo = readWord(address);
  u8 hi = readByte(address + 2);
  return (hi << 16) | lo;
}
