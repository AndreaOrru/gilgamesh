use crate::snes::rom::ROM;

pub struct Analysis {
    rom: ROM,
}

impl Analysis {
    pub fn new(rom: ROM) -> Self {
        Self { rom }
    }
}
