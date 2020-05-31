mod common;
use common::session;

test_rom!(setup_lorom, "lorom.asm");

#[test]
fn test_help() {
    let mut s = session(&setup_lorom());

    s.send_line("help quit").unwrap();
    s.exp_string("Quit the application").unwrap();
}

#[test]
fn test_quit() {
    let mut s = session(&setup_lorom());

    s.send_line("quit").unwrap();
    s.exp_eof().unwrap();
}

#[test]
fn test_ctrl_c() {
    let mut s = session(&setup_lorom());

    s.send_control('c').unwrap();
    s.wait_for_prompt().unwrap();
}

#[test]
fn test_ctrl_d() {
    let mut s = session(&setup_lorom());

    s.send_control('d').unwrap();
    s.exp_eof().unwrap();
}
