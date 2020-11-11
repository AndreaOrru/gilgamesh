#pragma once

#include <string>
#include <vector>

#include "types.hpp"

enum class ROMType {
  LoROM,
  HiROM,
  ExLoROM,
  ExHiROM,
  SDD1,
};

enum Header {
  TITLE_LEN = 21,
  TITLE = 0xFFC0,
  MARKUP = 0xFFD5,
  TYPE = 0xFFD6,
  SIZE = 0xFFD7,
  NMI = 0xFFEA,
  RESET = 0xFFFC,
};

class ROM {
 public:
  ROM(const std::string& path);
  u8 readByte(u24 address) const;
  u16 readWord(u24 address) const;
  u24 readAddress(u24 address) const;
  std::vector<u8> read(u24 address, size_t bytes) const;
  static bool isRAM(u24 address);
  size_t size() const;
  size_t realSize() const;
  u24 resetVector() const;
  u24 nmiVector() const;

  ROMType romType;

 private:
  u24 translate(u24 address) const;
  u24 translateHeader(u24 address) const;
  ROMType discoverType() const;
  ROMType discoverSubtype() const;
  int typeScore(ROMType romType) const;

  std::string path;
  std::vector<u8> data;
};
