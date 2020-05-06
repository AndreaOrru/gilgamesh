from array import array
from enum import Enum, auto
from hashlib import sha1
from typing import List


class ROMType(Enum):
    LoROM = auto()
    HiROM = auto()


class Header:
    TITLE = 0xFFC0
    TYPE = 0xFFD6
    SIZE = 0xFFD7
    NMI = 0xFFEA
    RESET = 0xFFFC


class ROM:
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.data = array("B", f.read())
        self.type = self._discover_type()

    @property
    def size(self) -> int:
        return 0x400 << self.read_byte(Header.SIZE)

    @property
    def title(self) -> str:
        title = ""
        for i in range(21):
            c = self.read_byte(Header.TITLE + i)
            if c == 0:
                break
            title += chr(c)
        return title

    @property
    def reset_vector(self) -> int:
        return self.read_word(Header.RESET)

    @property
    def nmi_vector(self) -> int:
        return self.read_word(Header.NMI)

    def read_byte(self, address: int) -> int:
        return self.data[self._translate(address)]

    def read_word(self, address: int) -> int:
        lo = self.read_byte(address)
        hi = self.read_byte(address + 1)
        return (hi << 8) | lo

    def read_address(self, address: int) -> int:
        lo = self.read_word(address)
        hi = self.read_byte(address + 2)
        return (hi << 16) | lo

    def read(self, address: int, n_bytes: int) -> List[int]:
        data = []
        for i in range(n_bytes):
            data.append(self.read_byte(address + i))
        return data

    def sha1(self):
        return sha1(self.data).hexdigest()

    def _translate(self, address: int) -> int:
        # Translate address from SNES to PC format.
        if self.type == ROMType.HiROM:
            return address & 0x3FFFFF
        else:
            return ((address & 0x7F0000) >> 1) | (address & 0x7FFF)

    def _discover_type(self) -> ROMType:
        if len(self.data) <= 0x8000:
            return ROMType.LoROM
        lorom_score = self._type_score(ROMType.LoROM)
        hirom_score = self._type_score(ROMType.HiROM)
        if hirom_score > lorom_score:
            return ROMType.HiROM
        else:
            return ROMType.LoROM

    def _type_score(self, rom_type: ROMType) -> int:
        title = Header.TITLE
        if rom_type == ROMType.LoROM:
            title -= 0x8000

        score = 0
        for i in range(21):
            c = self.data[title + i]
            if c == 0x00:
                score += 1
            elif chr(c).isprintable():
                score += 2
            else:
                return 0
        return score
