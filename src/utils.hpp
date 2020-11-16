#pragma once

#include <QString>
#include <string>
#include <vector>

#include "types.hpp"

// Read a whole file into memory.
std::vector<u8> readBinaryFile(const std::string& path);

// Format a string (like C++20's std::format).
template <typename... Args>
std::string format(const std::string& format, const Args&... args) {
  constexpr size_t STRING_BUFFER_SIZE = 256;
  char s[STRING_BUFFER_SIZE];
  snprintf(s, STRING_BUFFER_SIZE, format.c_str(), args...);
  return std::string(s);
}

// Format a string, returning a QString.
template <typename... Args>
QString qformat(const std::string& fmt, const Args&... args) {
  return QString::fromStdString(format(fmt, args...));
}
