class ROM:
    # TODO: don't assume it's a LoROM.

    def __init__(self, rom_file):
        self._rom = open(rom_file, 'rb').read()

    def __len__(self):
        return len(self._rom)

    @property
    def end_address(self):
        return self.pc_to_lorom(len(self))

    def read_byte(self, address, snes_address=True):
        if snes_address:
            address = self.lorom_to_pc(address)
        return self._rom[address]

    def read_bytes(self, start, end=None):
        start = self.lorom_to_pc(start)
        end = len(self) if (end is None) else self.lorom_to_pc(end)
        for i in range(start, end):
            yield self.read_byte(i, False)

    @staticmethod
    def lorom_to_pc(address):
        return (address & 0x7FFF) + ((address // 2) & 0xFF8000)

    @staticmethod
    def pc_to_lorom(address):
        return ((address * 2) & 0xFF0000) + (address & 0x7FFF) + 0x8000
