mod common;
use gilgamesh::analysis::Analysis;

test_rom!(setup_rom, "infinite_loop.asm");

#[test]
fn test_instructions() {
    let rom = setup_rom();
    let analysis = Analysis::new(rom);
    analysis.run();

    assert!(analysis.is_visited_pc(0x8000));
}
