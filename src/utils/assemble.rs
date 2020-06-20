use std::collections::HashMap;
use std::fs::remove_file;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;

use lazy_static::lazy_static;

/// Assemble a test ROM.
pub fn assemble(filename: &'static str) -> String {
    // Find the test ROMs' directory.
    let mut base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    base.push("tests");

    // Find the .asm file inside it.
    let mut asm = base.clone();
    asm.push(filename);

    // Find the corresponding .sfc path.
    let mut sfc = base;
    let basename = asm.file_stem().unwrap().to_str().unwrap();
    sfc.push(format!("{}.sfc", basename));
    // Remove an already assembled ROM if it exists.
    remove_file(&sfc).ok();

    // Run the assembler.
    let status = Command::new("asar").arg(&asm).arg(&sfc).status().unwrap();
    assert!(status.success());

    sfc.to_str().unwrap().into()
}

lazy_static! {
    /// A map of (asm filename) -> (corresponding assembled ROM file).
    pub static ref ASSEMBLED_ROMS: Mutex<HashMap<&'static str, String>> =
        Mutex::new(HashMap::new());
}

/// Generate a function that returns the required assembled ROM.
#[macro_export]
macro_rules! test_rom {
    ($setup_fn:ident, $filename:literal) => {
        fn $setup_fn() -> ROM {
            let mut roms = gilgamesh::utils::assemble::ASSEMBLED_ROMS.lock().unwrap();
            let rom_path = roms
                .entry($filename)
                .or_insert_with(|| gilgamesh::utils::assemble::assemble($filename))
                .to_string();
            ROM::from(rom_path).unwrap()
        }
    };
}
