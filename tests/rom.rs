extern crate gilgamesh;

use gilgamesh::rom::ROM;

mod common;
use common::assemble;
use std::sync::Once;

static INIT: Once = Once::new();
static mut LOROM: String = String::new();

pub fn setup_lorom() -> ROM {
    unsafe {
        INIT.call_once(|| {
            LOROM = assemble("lorom.asm");
        });
        ROM::from(LOROM.to_owned()).unwrap()
    }
}

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
