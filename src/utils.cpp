#include "utils.hpp"

using namespace std;

void readBinaryFile(const std::string& path, std::vector<u8>& buffer) {
  FILE* file = fopen(path.c_str(), "rb");

  fseek(file, 0, SEEK_END);
  size_t size = ftell(file);
  fseek(file, 0, SEEK_SET);

  buffer.resize(size);
  fread(buffer.data(), size, 1, file);

  fclose(file);
}
