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
  u8 readByte(const u24 address);
  u16 readWord(const u24 address);
  u24 readAddress(const u24 address);

  ROMType romType;

 private:
  ROMType discoverType();
  int typeScore(ROMType romType);

  std::string path;
  std::vector<u8> data;
};
