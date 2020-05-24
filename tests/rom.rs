#[macro_use]
mod common;

extern crate gilgamesh;
use gilgamesh::rom::ROM;

test_rom!(setup_lorom, "lorom.asm");

#[test]
fn test_title() {
    let lorom = setup_lorom();
    assert_eq!(lorom.title(), "TEST");
}

#[test]
fn test_reset_vector() {
    let lorom = setup_lorom();
    assert_eq!(lorom.reset_vector(), 0x8000);
}
