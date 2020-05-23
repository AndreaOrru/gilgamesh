use std::fs::File;
use std::io;
use std::io::prelude::*;

/// ROM classification.
#[derive(Debug, PartialEq)]
enum ROMType {
    Unknown,
    LoROM,
    HiROM,
}

/// ROM's header.
mod header {
    /// ROM's title.
    pub const TITLE: usize = 0xFFC0;
}

/// Structure representing a SNES ROM.
pub struct ROM {
    path: String,
    data: Vec<u8>,
    rom_type: ROMType,
}

impl ROM {
    /// Instantiate a new ROM.
    pub fn new(path: String) -> ROM {
        ROM {
            path,
            data: Vec::new(),
            rom_type: ROMType::Unknown,
        }
    }

    /// Load ROM data from file.
    pub fn load(&mut self) -> io::Result<()> {
        let mut file = File::open(&self.path)?;
        file.read_to_end(&mut self.data)?;
        self.rom_type = self.discover_type();
        Ok(())
    }

    /// Read a byte from the ROM.
    pub fn read_byte(&self, address: usize) -> u8 {
        self.data[self.translate(address)]
    }

    /// Read a word (16 bits) from the ROM.
    pub fn read_word(&self, address: usize) -> u16 {
        let lo = self.read_byte(address) as u16;
        let hi = self.read_byte(address + 1) as u16;
        (hi << 8) | lo
    }

    /// Read an address (24 bits) from the ROM.
    pub fn read_address(&self, address: usize) -> u32 {
        let lo = self.read_word(address) as u32;
        let hi = self.read_byte(address + 2) as u32;
        (hi << 16) | lo
    }

    /// Translate an address from SNES to PC.
    fn translate(&self, address: usize) -> usize {
        match self.rom_type {
            ROMType::LoROM => ((address & 0x7F0000) >> 1) | (address & 0x7FFF),
            ROMType::HiROM => address & 0x3FFFFF,
            _ => unreachable!(),
        }
    }

    /// Discover the ROM type.
    fn discover_type(&self) -> ROMType {
        if self.data.len() <= 0x8000 {
            return ROMType::LoROM;
        }
        let lorom = self.type_score(ROMType::LoROM);
        let hirom = self.type_score(ROMType::HiROM);
        if hirom > lorom {
            ROMType::HiROM
        } else {
            ROMType::LoROM
        }
    }

    /// Estimate the likelihood that the the ROM is of the given type.
    fn type_score(&self, rom_type: ROMType) -> u8 {
        let title = match rom_type {
            ROMType::LoROM => header::TITLE - 0x8000,
            ROMType::HiROM => header::TITLE,
            _ => unreachable!(),
        };

        let mut score = 0;
        for i in 0..21 {
            let c = self.data[title + i];
            if c == 0x00 {
                score += 1;
            } else if c.is_ascii_graphic() || c.is_ascii_whitespace() {
                score += 2;
            } else {
                return 0;
            }
        }
        score
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_lorom() -> ROM {
        let mut rom = ROM::new("".into());
        let title = header::TITLE - 0x8000;
        rom.data.resize(0x10000, 0);

        rom.data[title + 0] = 0x54; // T
        rom.data[title + 1] = 0x45; // E
        rom.data[title + 2] = 0x53; // S
        rom.data[title + 3] = 0x54; // T

        rom.rom_type = rom.discover_type();
        rom
    }

    #[test]
    fn test_discover_type() {
        let lorom = setup_lorom();
        assert_eq!(lorom.rom_type, ROMType::LoROM);
    }

    #[test]
    fn test_translate() {
        let lorom = setup_lorom();
        assert_eq!(lorom.translate(0x008000), 0x000000);
        assert_eq!(lorom.translate(0x808000), 0x000000);
    }

    #[test]
    fn test_read_byte() {
        let lorom = setup_lorom();
        assert_eq!(lorom.read_byte(header::TITLE + 0), 0x54);
        assert_eq!(lorom.read_byte(header::TITLE + 1), 0x45);
        assert_eq!(lorom.read_byte(header::TITLE + 2), 0x53);
        assert_eq!(lorom.read_byte(header::TITLE + 3), 0x54);
    }

    #[test]
    fn test_read_word() {
        let lorom = setup_lorom();
        assert_eq!(lorom.read_word(header::TITLE + 0), 0x4554);
        assert_eq!(lorom.read_word(header::TITLE + 2), 0x5453);
    }

    #[test]
    fn test_read_address() {
        let lorom = setup_lorom();
        assert_eq!(lorom.read_address(header::TITLE + 0), 0x534554);
        assert_eq!(lorom.read_address(header::TITLE + 1), 0x545345);
    }
}
