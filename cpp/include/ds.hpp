#ifndef __DS_HPP
#define __DS_HPP

#include <cstdint>


struct MapEntry
{
    uint8_t tile;
    uint8_t attr;
} __attribute__((packed));

uint32_t* convertTiles(const uint8_t* src, int bytes);
MapEntry* convertMap(const MapEntry* src, int bytes);


#endif
