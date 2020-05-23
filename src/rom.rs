use std::fs::File;
use std::io;
use std::io::prelude::*;

/// Structure representing a SNES ROM.
pub struct ROM {
    path: String,
    data: Vec<u8>,
}

impl ROM {
    /// Create a new ROM.
    pub fn new(path: String) -> ROM {
        ROM {
            path,
            data: Vec::new(),
        }
    }

    /// Load ROM data from file.
    pub fn load(&mut self) -> io::Result<()> {
        let mut file = File::open(&self.path)?;
        file.read_to_end(&mut self.data)?;
        Ok(())
    }

    /// Read a byte from the ROM.
    pub fn read_byte(&self, address: usize) -> u8 {
        self.data[address]
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
}

#[cfg(test)]
mod tests {
    use super::*;

    // Programmatically generate a test ROM.
    fn setup_rom() -> ROM {
        let mut rom = ROM::new("".into());
        rom.data.resize(0x8000, 0);
        rom.data[0x1234] = 0x01;
        rom.data[0x1235] = 0x02;
        rom.data[0x1236] = 0x03;
        rom
    }

    #[test]
    fn test_read_byte() {
        // Test that we can read individual bytes.
        let rom = setup_rom();
        assert_eq!(rom.read_byte(0x1234), 0x01);
        assert_eq!(rom.read_byte(0x1235), 0x02);
        assert_eq!(rom.read_byte(0x1236), 0x03);
    }

    #[test]
    fn test_read_word() {
        // Test that we can read byte pairs.
        let rom = setup_rom();
        assert_eq!(rom.read_word(0x1234), 0x0201);
        assert_eq!(rom.read_word(0x1235), 0x0302);
    }

    #[test]
    fn test_read_address() {
        // Test that we can read byte triplets.
        let rom = setup_rom();
        assert_eq!(rom.read_address(0x1234), 0x030201);
    }
}
