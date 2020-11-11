#include "rom.hpp"
#include "utils.hpp"

using namespace std;

ROM::ROM(const string& path) : path{path} {
  data = readBinaryFile(path);
  romType = discoverType();
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

ROMType ROM::discoverType() {
  if (data.size() <= 0x8000) {
    return ROMType::LoROM;
  }

  int lorom = typeScore(ROMType::LoROM);
  int hirom = typeScore(ROMType::HiROM);

  return (hirom > lorom) ? ROMType::HiROM : ROMType::LoROM;
}

int ROM::typeScore(ROMType romType) {
  u24 titleAddress =
      (romType == ROMType::LoROM) ? (Header::TITLE - 0x8000) : Header::TITLE;

  int score = 0;
  for (int i = 0; i < Header::TITLE_LEN; i++) {
    char c = data[titleAddress + i];
    if (c == 0x00) {
      score += 1;
    } else if (isprint(c)) {
      score += 2;
    } else {
      return 0;
    }
  }
  return score;
}
