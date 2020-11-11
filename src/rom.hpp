#pragma once

#include <string>
#include <vector>

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
 private:
  std::string path;
  std::vector<uint8_t> data;
  ROMType romType;

 public:
  ROM(const std::string& path);
};
