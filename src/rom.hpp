#pragma once

#include <string>
#include <vector>

#include "types.hpp"

// ROM classification.
enum class ROMType {
  LoROM,
  HiROM,
  ExLoROM,
  ExHiROM,
  SDD1,
};

// ROM's header.
enum Header {
  TITLE_LEN = 21,
  TITLE = 0xFFC0,
  MARKUP = 0xFFD5,
  TYPE = 0xFFD6,
  SIZE = 0xFFD7,
  NMI = 0xFFEA,
  RESET = 0xFFFC,
};

// Class representing a SNES ROM.
class ROM {
 public:
  ROM(const std::string& path);  // Constructor.

  u8 readByte(u24 address) const;      // Read a byte.
  u16 readWord(u24 address) const;     // Read a word (16 bits).
  u24 readAddress(u24 address) const;  // Read an address (24 bits).
  // Read a sequence of bytes.
  std::vector<u8> read(u24 address, size_t bytes) const;

  // Return true if the address is in RAM, false otherwise.
  static bool isRAM(u24 address);

  // Size of the ROM, as indicated by the header.
  size_t size() const;

  // Size of the ROM, as measured by the size of the file.
  size_t realSize() const;

  // Return the ROM's title.
  std::string title() const;

  // Return the reset vector (ROM's entry point).
  u24 resetVector() const;

  // Return the NMI vector (VBLANK handler).
  u24 nmiVector() const;

  // Translate an address from SNES to PC.
  u24 translate(u24 address) const;

  ROMType romType;  // ROM classification.

 private:
  // Translate address inside the header.
  u24 translateHeader(u24 address) const;

  // Discover the ROM type.
  ROMType discoverType() const;

  // Discover the ROM subtype.
  ROMType discoverSubtype() const;

  // Estimate the likelihood that the the ROM is of the given type.
  int typeScore(ROMType romType) const;

  std::string path;      // ROM's file path.
  std::vector<u8> data;  // ROM's data.
};
