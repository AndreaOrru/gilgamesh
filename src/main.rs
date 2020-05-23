use clap::clap_app;

fn main() {
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

    // Get the ROM's path.
    let rom_path = matches.value_of("ROM").unwrap();
    println!("{}", rom_path);
}
