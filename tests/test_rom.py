from abc import ABC
from os.path import dirname, join, splitext
from subprocess import call
from unittest import TestCase

from gilgamesh.rom import ROM, ROMType


def rom_path(filename: str) -> str:
    return join(dirname(__file__), "roms", filename)


def assemble(filename: str) -> str:
    asm = rom_path(filename)
    rom = splitext(asm)[0] + ".sfc"
    call(["asar", asm, rom])
    return rom


class ROMTestCase(ABC):
    def test_size(self):
        self.assertEqual(self.rom.size, 2048)

    def test_title(self):
        self.assertEqual(self.rom.title, "TEST")

    def test_reset_vector(self):
        self.assertEqual(self.rom.reset_vector, 0x8000)

    def test_nmi_vector(self):
        self.assertEqual(self.rom.nmi_vector, 0x9000)

    def test_read(self):
        byte = ord("T")
        word = ord("T") | (ord("E") << 8)
        addr = ord("T") | (ord("E") << 8) | (ord("S") << 16)
        self.assertEqual(self.rom.read_byte(0xFFC0), byte)
        self.assertEqual(self.rom.read_word(0xFFC0), word)
        self.assertEqual(self.rom.read_address(0xFFC0), addr)
        self.assertListEqual(self.rom.read(0xFFC0, 4), [ord(x) for x in "TEST"])


class LoROMTestCase(ROMTestCase, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("lorom.asm"))

    def test_type(self):
        self.assertEqual(self.rom.type, ROMType.LoROM)

    def test_translate(self):
        self.assertEqual(self.rom._translate(0x008000), 0x000000)
        self.assertEqual(self.rom._translate(0x108000), 0x080000)
        self.assertEqual(self.rom._translate(0x808000), 0x000000)


class HiROMTestCase(ROMTestCase, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM(assemble("hirom.asm"))

    def test_type(self):
        self.assertEqual(self.rom.type, ROMType.HiROM)

    def test_translate(self):
        self.assertEqual(self.rom._translate(0xC00000), 0x000000)
        self.assertEqual(self.rom._translate(0xC08000), 0x008000)
        self.assertEqual(self.rom._translate(0x400000), 0x000000)
