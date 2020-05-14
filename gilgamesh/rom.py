from array import array
from enum import Enum, auto
from hashlib import sha1
from os.path import basename, splitext
from typing import List

from gilgamesh.errors import GilgameshError


class ROMType(Enum):
    LoROM = auto()
    ExLoROM = auto()
    HiROM = auto()
    ExHiROM = auto()
    # TODO: support other types.


class Header:
    TITLE = 0xFFC0
    MARKUP = 0xFFD5
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
        self.type = self._discover_subtype()

    @property
    def size(self) -> int:
        return 0x400 << self.read_byte(Header.SIZE)

    @property
    def real_size(self) -> int:
        return len(self.data)

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

    @property
    def glm_path(self) -> str:
        return splitext(self.path)[0] + ".glm"

    @property
    def glm_name(self) -> str:
        return basename(self.glm_path)

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
        if self.type == ROMType.LoROM:
            pc = ((address & 0x7F0000) >> 1) | (address & 0x7FFF)

        elif self.type == ROMType.ExLoROM:
            if address & 0x800000:
                pc = ((address & 0x7F0000) >> 1) | (address & 0x7FFF)
            else:
                pc = (((address & 0x7F0000) >> 1) | (address & 0x7FFF)) + 0x400000

        elif self.type == ROMType.HiROM:
            pc = address & 0x3FFFFF

        elif self.type == ROMType.ExHiROM:
            if (address & 0xC00000) != 0xC00000:
                pc = (address & 0x3FFFFF) | 0x400000
            pc = address & 0x3FFFFF

        if address > 0xFFFFFF or pc >= self.real_size:
            raise GilgameshError(f"Invalid address: ${address:X}.")
        return pc

    def _discover_subtype(self) -> ROMType:
        markup = self.read_byte(Header.MARKUP)
        if (self.type == ROMType.LoROM) and (markup & 0b10):
            return ROMType.ExLoROM
        elif (self.type == ROMType.HiROM) and (markup & 0b100):
            return ROMType.ExHiROM
        return self.type

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
