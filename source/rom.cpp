#include "rom.hpp"
#include <cctype>
#include <cstdio>

ROM::ROM(const char *path) {
  FILE *file = fopen(path, "rb");

  fseek(file, 0, SEEK_END);
  size = ftell(file);
  fseek(file, 0, SEEK_SET);

  data = new u8[size];
  fread(data, size, 1, file);
  fclose(file);

  hirom = checkHirom();
}

ROM::~ROM() { delete data; }

u8 ROM::readByte(u24 address) const { return data[translateAddress(address)]; }

u16 ROM::readWord(u24 address) const {
  u8 lo = readByte(address);
  u8 hi = readByte(address + 1);
  return (hi << 8) | lo;
}

u24 ROM::readAddress(u24 address) const {
  u16 lo = readWord(address);
  u8 hi = readByte(address + 2);
  return (hi << 16) | lo;
}

ROMType ROM::type() const { return hirom ? HIROM : LOROM; }

std::string ROM::title() const {
  std::string s;
  for (int i = 0; i < 21; i++) {
    char c = readByte(0xFFC0 + i);
    if (c == 0) {
      break;
    }
    s += c;
  }
  return s;
}

u16 ROM::resetVector() const { return readWord(0xFFFC); }

u16 ROM::nmiVector() const { return readWord(0xFFEA); }

u24 ROM::translateAddress(u24 address) const {
  if (hirom) {
    return address & ~0xC00000;
  } else {
    return (address & 0x7FFF) + ((address / 2) & 0xFF8000);
  }
}

bool ROM::checkHirom() const {
  for (int i = 0; i < 21; i++) {
    char c = data[0x7FC0 + i];
    if (c != 0 && !isprint(c)) {
      return true;
    }
  }
  return false;
}
