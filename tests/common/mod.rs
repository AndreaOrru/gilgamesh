#![allow(dead_code)]

use std::collections::HashMap;
use std::fs::remove_file;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;

use lazy_static::lazy_static;
use rexpect::session::{spawn_command, PtyReplSession};

use gilgamesh::snes::rom::ROM;

/// Assemble a test ROM.
pub fn assemble(filename: &'static str) -> String {
    // Find the test ROMs' directory.
    let mut base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    base.push("tests/roms");

    // Find the .asm file inside it.
    let mut asm = base.clone();
    asm.push(filename);

    // Find the corresponding .sfc path.
    let mut sfc = base.clone();
    let basename = asm.file_stem().unwrap().to_str().unwrap();
    sfc.push(format!("{}.sfc", basename));
    // Remove an already assembled ROM if it exists.
    remove_file(&sfc).ok();

    // Run the assembler.
    let status = Command::new("asar").arg(&asm).arg(&sfc).status().unwrap();
    assert!(status.success());

    sfc.to_str().unwrap().into()
}

/// Return a rexpect session to test the command prompt on a ROM.
pub fn session(rom: &ROM) -> PtyReplSession {
    // Find the Gilgamesh binary.
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.push("target/debug/gilgamesh");

    // Run Gilgamesh on the given ROM, disabling colors.
    let mut command = Command::new(path);
    command.arg(rom.path()).env("NO_COLOR", "1");

    // Build the session.
    let mut s = PtyReplSession {
        echo_on: true,
        prompt: "> ".to_string(),
        pty_session: spawn_command(command, Some(2_000)).unwrap(),
        quit_command: Some("quit".to_string()),
    };

    // Wait for the prompt to be ready.
    s.wait_for_prompt().unwrap();
    s
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
        fn $setup_fn() -> gilgamesh::snes::rom::ROM {
            let mut roms = common::ASSEMBLED_ROMS.lock().unwrap();
            let rom_path = roms
                .entry($filename)
                .or_insert_with(|| common::assemble($filename))
                .to_string();
            gilgamesh::snes::rom::ROM::from(rom_path).unwrap()
        }
    };
}
