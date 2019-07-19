#pragma once
#include "types.hpp"
#include <string>

enum ROMType {
  LOROM,
  HIROM,
};

class ROM {
public:
  ROM(const char *path);
  ~ROM();

  u8 readByte(u24 address) const;
  u16 readWord(u24 address) const;
  u24 readAddress(u24 address) const;

  ROMType type() const;
  std::string title() const;
  u16 resetVector() const;
  u16 nmiVector() const;

private:
  u8 *data;
  u24 size;
  bool hirom;

  u24 translateAddress(u24 address) const;
  bool checkHirom() const;
};
