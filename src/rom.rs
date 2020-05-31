use getset::{CopyGetters, Getters};

use std::fs::File;
use std::io;
use std::io::prelude::*;

/// ROM classification.
#[derive(Copy, Clone, Debug, PartialEq)]
pub enum ROMType {
    Unknown,
    LoROM,
    HiROM,
}

/// ROM's header.
#[allow(dead_code)]
mod header {
    /// ROM's title max length.
    pub const TITLE_LEN: usize = 21;

    /// ROM's title.
    pub const TITLE: usize = 0xFFC0;
    /// Markup byte.
    pub const MARKUP: usize = 0xFFD5;
    /// ROM's type byte.
    pub const TYPE: usize = 0xFFD6;
    /// ROM's type byte.
    pub const SIZE: usize = 0xFFD7;
    /// NMI vector.
    pub const NMI: usize = 0xFFEA;
    /// RESET vector.
    pub const RESET: usize = 0xFFFC;
}

/// Structure representing a SNES ROM.
#[derive(Getters, CopyGetters)]
pub struct ROM {
    #[getset(get = "pub")]
    path: String,
    data: Vec<u8>,

    #[getset(get_copy = "pub")]
    rom_type: ROMType,
}

impl ROM {
    /// Instantiate a new empty ROM object.
    #[allow(clippy::new_without_default)]
    pub fn new() -> ROM {
        ROM {
            path: String::new(),
            data: Vec::new(),
            rom_type: ROMType::Unknown,
        }
    }

    /// Instantiate a ROM from a file.
    pub fn from(path: String) -> io::Result<ROM> {
        let mut rom = ROM::new();
        rom.load(path)?;
        Ok(rom)
    }

    /// Load ROM data from file.
    pub fn load(&mut self, path: String) -> io::Result<()> {
        self.path = path.to_owned();
        let mut file = File::open(path)?;
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
    pub fn read_address(&self, address: usize) -> usize {
        let lo = self.read_word(address) as usize;
        let hi = self.read_byte(address + 2) as usize;
        (hi << 16) | lo
    }

    /// Size of the ROM, as indicated by the header.
    pub fn size(&self) -> usize {
        0x400 << self.read_byte(header::SIZE)
    }

    /// Size of the ROM, as measured by the size of the file.
    pub fn actual_size(&self) -> usize {
        self.data.len()
    }

    /// Return the ROM's title.
    pub fn title(&self) -> String {
        let mut title = String::new();
        for i in 0..header::TITLE_LEN {
            match self.read_byte(header::TITLE + i) {
                0x00 => break,
                c => title.push(char::from(c)),
            }
        }
        title
    }

    /// Return the reset vector (ROM's entry point).
    pub fn reset_vector(&self) -> usize {
        self.read_word(header::RESET) as usize
    }

    /// Return the NMI vector (VBLANK handler).
    pub fn nmi_vector(&self) -> usize {
        self.read_word(header::NMI) as usize
    }

    /// Translate an address from SNES to PC.
    pub fn translate(&self, address: usize) -> usize {
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
        for i in 0..header::TITLE_LEN {
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
        let mut rom = ROM::new();
        let title = header::TITLE - 0x8000;
        rom.data.resize(0x10000, 0);

        rom.data[title + 0] = 0x54; // T
        rom.data[title + 1] = 0x45; // E
        rom.data[title + 2] = 0x53; // S
        rom.data[title + 3] = 0x54; // T

        rom.rom_type = rom.discover_type();
        rom
    }

    fn setup_hirom() -> ROM {
        let mut rom = ROM::new();
        rom.data.resize(0x10000, 0);

        rom.data[header::TITLE + 0] = 0x54; // T
        rom.data[header::TITLE + 1] = 0x45; // E
        rom.data[header::TITLE + 2] = 0x53; // S
        rom.data[header::TITLE + 3] = 0x54; // T

        rom.rom_type = rom.discover_type();
        rom
    }

    #[test]
    fn test_actual_size() {
        let (lorom, hirom) = (setup_lorom(), setup_hirom());
        assert_eq!(lorom.actual_size(), 0x10000);
        assert_eq!(hirom.actual_size(), 0x10000);
    }

    #[test]
    fn test_discover_type() {
        let (lorom, hirom) = (setup_lorom(), setup_hirom());
        assert_eq!(lorom.rom_type, ROMType::LoROM);
        assert_eq!(hirom.rom_type, ROMType::HiROM);
    }

    #[test]
    fn test_translate() {
        let lorom = setup_lorom();
        assert_eq!(lorom.translate(0x008000), 0x000000);
        assert_eq!(lorom.translate(0x808000), 0x000000);

        let hirom = setup_hirom();
        assert_eq!(hirom.translate(0xC00000), 0x000000);
        assert_eq!(hirom.translate(0xC08000), 0x008000);
        assert_eq!(hirom.translate(0x400000), 0x000000);
    }

    #[test]
    fn test_read_byte() {
        let roms = [setup_lorom(), setup_hirom()];
        for rom in roms.iter() {
            assert_eq!(rom.read_byte(header::TITLE + 0), 0x54);
            assert_eq!(rom.read_byte(header::TITLE + 1), 0x45);
            assert_eq!(rom.read_byte(header::TITLE + 2), 0x53);
            assert_eq!(rom.read_byte(header::TITLE + 3), 0x54);
        }
    }

    #[test]
    fn test_read_word() {
        let roms = [setup_lorom(), setup_hirom()];
        for rom in roms.iter() {
            assert_eq!(rom.read_word(header::TITLE + 0), 0x4554);
            assert_eq!(rom.read_word(header::TITLE + 2), 0x5453);
        }
    }

    #[test]
    fn test_read_address() {
        let roms = [setup_lorom(), setup_hirom()];
        for rom in roms.iter() {
            assert_eq!(rom.read_address(header::TITLE + 0), 0x534554);
            assert_eq!(rom.read_address(header::TITLE + 1), 0x545345);
        }
    }

    #[test]
    fn test_title() {
        let roms = [setup_lorom(), setup_hirom()];
        for rom in roms.iter() {
            assert_eq!(rom.title(), "TEST");
        }
    }
}
