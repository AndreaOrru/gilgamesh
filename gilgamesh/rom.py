class ROM:
    """Super Nintendo ROM abstraction."""

    # TODO: don't assume it's a LoROM.

    def __init__(self, rom_file):
        self._rom = open(rom_file, 'rb').read()

    def __len__(self):
        """The number of bytes in the ROM."""
        return len(self._rom)

    @property
    def end_address(self):
        """Final address of the ROM in SNES format."""
        return self.pc_to_lorom(len(self))

    def read_byte(self, address, snes_address=True):
        """Read a byte from the ROM at the specified address.

        Args:
            address: The address of the byte.
            snes_address: True if the address is given in SNES format.

        Returns:
            The requested byte.
        """
        if snes_address:
            address = self.lorom_to_pc(address)
        return self._rom[address]

    def read_bytes(self, start, count=None, end=None):
        """Read a sequence of bytes from the ROM.

        If count is not given, read till end (not included).
        If end is also not given, read till the very end of the ROM.

        Args:
            start: The address of the first byte, in SNES format.
            count: The number of bytes to read.
            end: The address of the final byte to read (not included).

        Returns:
            The sequence of requested bytes.
        """
        start = self.lorom_to_pc(start)

        if count is None:
            end = len(self) if (end is None) else self.lorom_to_pc(end)
        else:
            end = start + count

        for i in range(start, end):
            yield self.read_byte(i, False)

    def read_value(self, start, byte_count):
        """Read a single value from the ROM with length byte_count.

        Args:
            start: The address of the first byte of the value, in SNES format.
            byte_count: The number of bytes that compose the value.

        Returns:
            The requested value.
        """
        data = self.read_bytes(start, count=byte_count)
        value = 0
        for i, byte in enumerate(data):
            value += byte << (i * 8)
        return value

    @staticmethod
    def lorom_to_pc(address):
        """Convert from LoROM address to PC address.

        Args:
            address: The LoROM address to convert.

        Returns:
            The address converted in PC format.
        """
        return (address & 0x7FFF) + ((address // 2) & 0xFF8000)

    @staticmethod
    def pc_to_lorom(address):
        """Convert from LoROM address to PC address.

        Args:
            address: The LoROM address to convert.

        Returns:
            The address converted in PC format.
        """
        return ((address * 2) & 0xFF0000) + (address & 0x7FFF) + 0x8000
