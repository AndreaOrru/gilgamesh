#include "rom.hpp"

#include "utils.hpp"

using namespace std;

// Construct an empty ROM (for test purposes).
ROM::ROM() {}

// Construct a ROM from a file path.
ROM::ROM(const string& path) : path{path} {
  data = readBinaryFile(path);
  romType = discoverType();
  romType = discoverSubtype();
};

// Read a byte.
u8 ROM::readByte(u24 address) const {
  return data[translate(address)];
}

// Read a word (16 bits).
u16 ROM::readWord(u24 address) const {
  u8 lo = readByte(address);
  u8 hi = readByte(address + 1);
  return (hi << 8) | lo;
}

// Read an address (24 bits).
u24 ROM::readAddress(u24 address) const {
  u16 lo = readWord(address);
  u8 hi = readByte(address + 2);
  return (hi << 16) | lo;
}

// Read a sequence of bytes.
vector<u8> ROM::read(u24 address, size_t bytes) const {
  vector<u8> buffer(bytes);
  for (size_t i = 0; i < bytes; i++) {
    buffer.push_back(readByte(address + i));
  }
  return buffer;
}

// Return true if the address is in RAM, false otherwise.
bool ROM::isRAM(u24 address) {
  return (address <= 0x001FFF) || (0x7E0000 <= address && address <= 0x7FFFFF);
}

// Size of the ROM, as indicated by the header.
size_t ROM::size() const {
  return 0x400 << readByte(translateHeader(Header::SIZE));
}

// Size of the ROM, as measured by the size of the file.
size_t ROM::realSize() const {
  return data.size();
}

// Return the ROM's title.
string ROM::title() const {
  string title;
  for (int i = 0; i < Header::TITLE_LEN; i++) {
    char c = readByte(translateHeader(Header::TITLE + i));
    if (c == 0x00) {
      break;
    }
    title.push_back(c);
  }
  return title;
}

// Return the reset vector (ROM's entry point).
SubroutinePC ROM::resetVector() const {
  return readWord(translateHeader(Header::RESET));
}

// Return the NMI vector (VBLANK handler).
SubroutinePC ROM::nmiVector() const {
  return readWord(translateHeader(Header::NMI));
}

// Translate an address from SNES to PC.
u24 ROM::translate(u24 address) const {
  switch (romType) {
    case ROMType::LoROM:
      return ((address & 0x7F0000) >> 1) | (address & 0x7FFF);

    case ROMType::HiROM:
      return address & 0x3FFFFF;

    case ROMType::ExLoROM:
      if (address & 0x800000) {
        return ((address & 0x7F0000) >> 1) | (address & 0x7FFF);
      } else {
        return (((address & 0x7F0000) >> 1) | (address & 0x7FFF)) + 0x400000;
      }

    case ROMType::ExHiROM:
      if ((address & 0xC00000) != 0xC00000) {
        return (address & 0x3FFFFF) | 0x400000;
      } else {
        return address & 0x3FFFFF;
      }

    case ROMType::SDD1:
      if (address >= 0xC00000) {
        return address & 0x3FFFFF;
      } else {
        return ((address & 0x7F0000) >> 1) | (address & 0x7FFF);
      }
  }

  __builtin_unreachable();
}

// Translate address inside the header.
u24 ROM::translateHeader(u24 address) const {
  if (romType == ROMType::ExLoROM || romType == ROMType::SDD1) {
    return 0x800000 + address;
  }
  return address;
}

// Discover the ROM type.
ROMType ROM::discoverType() const {
  if (data.size() <= 0x8000) {
    return ROMType::LoROM;
  }

  int lorom = typeScore(ROMType::LoROM);
  int hirom = typeScore(ROMType::HiROM);

  return (hirom > lorom) ? ROMType::HiROM : ROMType::LoROM;
}

// Discover the ROM subtype.
ROMType ROM::discoverSubtype() const {
  u8 markup = readByte(Header::MARKUP);

  switch (romType) {
    case ROMType::LoROM:
      if (markup == 0x32) {
        return ROMType::SDD1;
      } else if (markup & (1 << 1)) {
        return ROMType::ExLoROM;
      }
      break;

    case ROMType::HiROM:
      if (markup & (1 << 2)) {
        return ROMType::ExHiROM;
      }
      break;

    default:
      break;
  }

  return romType;
}

// Estimate the likelihood that the the ROM is of the given type.
int ROM::typeScore(ROMType romType) const {
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
