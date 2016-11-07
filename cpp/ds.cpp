#include "ds.hpp"

MapEntry* convertMap(const MapEntry* src, int bytes)
{
    MapEntry* dest = new MapEntry[bytes / sizeof(MapEntry)];

    for (int y = 0; y < 16; y++)
        for (int x = 0; x < 16; x++)
        {
            MapEntry e = src[y*32 + x];

            dest[2 * (y*32 + x)]      = e;
            dest[2 * (y*32 + x) + 1]  = { .tile = (uint8_t)(e.tile + 1),  .attr = e.attr };
            dest[2 * (y*32 + x) + 32] = { .tile = (uint8_t)(e.tile + 16), .attr = e.attr };
            dest[2 * (y*32 + x) + 33] = { .tile = (uint8_t)(e.tile + 17), .attr = e.attr };
        }

    return dest;
}

uint32_t* convertTiles(const uint8_t* src, int bytes)
{
    uint32_t* dest = new uint32_t[bytes / 4];

    int i = 0;
    int j = 0;

    while (i < bytes)
    {
        for (int y = 0; y < 8; y++)
        {
            uint32_t line = 0;

            uint32_t line1 = src[i + 0];   // Plane 1.
            uint32_t line2 = src[i + 1];   // Plane 2.
            uint32_t line3 = src[i + 16];  // Plane 3.
            uint32_t line4 = src[i + 17];  // Plane 4.

            for (int x = 0; x < 8; x++)
            {
                int shift = (7 - x) * 4;

                line |= ((line1 & 1) <<  shift     ) |
                        ((line2 & 1) << (shift + 1)) |
                        ((line3 & 1) << (shift + 2)) |
                        ((line4 & 1) << (shift + 3));

                line1 >>= 1;
                line2 >>= 1;
                line3 >>= 1;
                line4 >>= 1;
            }

            dest[j++] = line;
            i += 2;
        }
        i += 16;
    }

    return dest;
}
