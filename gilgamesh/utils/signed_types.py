from ctypes import c_byte, c_short


def s8(byte: int) -> int:
    return c_byte(byte).value


def s16(word: int) -> int:
    return c_short(word).value
