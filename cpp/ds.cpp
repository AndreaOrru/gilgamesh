#include "ds.hpp"


uint32_t* convertTiles(uint8_t* src, int bytes)
{
    uint32_t* dest = new uint32_t[bytes / 4];

    while (bytes > 0)
    {
        for (int y = 0; y < 8; y++)
        {
            uint32_t line = 0;

            uint32_t line1 = src[0];       // Plane 1.
            uint32_t line2 = src[1];       // Plane 2.
            uint32_t line3 = src[16];      // Plane 3.
            uint32_t line4 = src[16 + 1];  // Plane 4.

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

            *dest++ = line;
            src += 2;
        }

        bytes -= 16;
    }

    return dest;
}
