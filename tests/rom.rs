#[macro_use]
mod common;

extern crate gilgamesh;
use gilgamesh::rom::{ROMType, ROM};

test_rom!(setup_lorom, "lorom.asm");
test_rom!(setup_hirom, "hirom.asm");

#[test]
fn test_discover_type() {
    let (lorom, hirom) = (setup_lorom(), setup_hirom());
    assert_eq!(lorom.rom_type(), ROMType::LoROM);
    assert_eq!(hirom.rom_type(), ROMType::HiROM);
}

#[test]
fn test_title() {
    let (lorom, hirom) = (setup_lorom(), setup_hirom());
    assert_eq!(lorom.title(), "TEST");
    assert_eq!(hirom.title(), "TEST");
}

#[test]
fn test_size() {
    let (lorom, hirom) = (setup_lorom(), setup_hirom());
    assert_eq!(lorom.size(), 2048);
    assert_eq!(hirom.size(), 2048);
}

#[test]
fn test_reset_vector() {
    let (lorom, hirom) = (setup_lorom(), setup_hirom());
    assert_eq!(lorom.reset_vector(), 0x8000);
    assert_eq!(hirom.reset_vector(), 0x8000);
}

#[test]
fn test_nmi_vector() {
    let (lorom, hirom) = (setup_lorom(), setup_hirom());
    assert_eq!(lorom.nmi_vector(), 0x0000);
    assert_eq!(hirom.nmi_vector(), 0x0000);
}
