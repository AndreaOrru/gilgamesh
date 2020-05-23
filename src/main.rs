mod rom;

use clap::clap_app;
use rom::ROM;
use std::io;

/// Get the ball rolling.
fn main() -> io::Result<()> {
    // Validation function to test the existence of a file.
    let file_exists = |path: &str| {
        if std::fs::metadata(path).is_ok() {
            Ok(())
        } else {
            Err(String::from("File doesn't exist.\n"))
        }
    };

    // Clap's argument parser.
    let matches = clap_app!(
        gilgamesh =>
            (version: "0.0.1")
            (author: "Andrea Orru <andrea@orru.io>")
            (about: "The definitive reverse engineering toolkit for SNES.")
            (@arg ROM: +required {file_exists} "The ROM file to analyze")
    )
    .get_matches();

    // Load the ROM.
    let rom_path = matches.value_of("ROM").unwrap();
    let mut rom = ROM::new(rom_path.into());
    rom.load()?;

    println!("{}", rom.title());
    Ok(())
}
