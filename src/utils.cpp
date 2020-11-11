#include "utils.hpp"

using namespace std;

vector<u8> readBinaryFile(const string& path) {
  FILE* file = fopen(path.c_str(), "rb");

  fseek(file, 0, SEEK_END);
  size_t size = ftell(file);
  fseek(file, 0, SEEK_SET);

  vector<u8> buffer(size);
  fread(buffer.data(), size, 1, file);

  fclose(file);
  return buffer;
}
