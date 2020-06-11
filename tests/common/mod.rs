#![allow(dead_code)]

use std::path::PathBuf;
use std::process::Command;

use rexpect::session::{spawn_command, PtyReplSession};

use gilgamesh::snes::rom::ROM;

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

/// Generate a function that returns the required assembled ROM.
#[macro_export]
macro_rules! test_rom {
    ($setup_fn:ident, $filename:literal) => {
        use gilgamesh::snes::rom::ROM;
        gilgamesh::test_rom!($setup_fn, $filename);
    };
}
