use std::fs::remove_file;
use std::path::PathBuf;
use std::process::Command;

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
