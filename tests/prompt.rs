mod common;
use rexpect::session::{spawn_command, PtyReplSession};
use std::process::Command;

use gilgamesh::rom::ROM;

test_rom!(setup_lorom, "lorom.asm");

fn session(rom: &ROM) -> PtyReplSession {
    let mut command = Command::new("./target/debug/gilgamesh");
    command.arg(rom.path()).env("NO_COLOR", "1");

    let mut s = PtyReplSession {
        echo_on: false,
        prompt: "> ".to_string(),
        pty_session: spawn_command(command, Some(1_000)).unwrap(),
        quit_command: Some("quit".to_string()),
    };
    s.wait_for_prompt().unwrap();
    s
}

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
