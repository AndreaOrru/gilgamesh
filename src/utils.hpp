#pragma once

#include <string>
#include <vector>

#include "types.hpp"

std::vector<u8> readBinaryFile(const std::string& path);

template <typename... Args>
std::string format(const std::string& format, Args... args) {
  char s[256];
  snprintf(s, 256, format.c_str(), args...);
  return std::string(s);
}
