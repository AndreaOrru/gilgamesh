class ROM:
    # TODO: don't assume it's a LoROM.

    def __init__(self, rom_file):
        self._rom = open(rom_file, 'rb').read()

    def read_byte(self, address):
        address = self._lorom_to_pc(address)
        return self._rom[address]

    def read_word(self, address):
        address = self._lorom_to_pc(address)
        return self._rom[address] + \
            (self._rom[address + 1] << 8)

    def read_triple(self, address):
        address = self._lorom_to_pc(address)
        return self._rom[address] + \
            (self._rom[address + 1] << 8) + \
            (self._rom[address + 2] << 16)

    @staticmethod
    def _lorom_to_pc(address):
        return (address & 0x7FFF) + ((address // 2) & 0xFF8000)
