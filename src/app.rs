use colored::*;
use maplit::hashmap;
use rustyline::error::ReadlineError;
use rustyline::Editor;
use std::collections::HashMap;
use std::io::Write;

use crate::command::Command;
use crate::rom::ROM;
use crate::{command, command_ref};

macro_rules! out {
    ($self:ident) => {
        out!($self, "");
    };

    ($self:ident, $format:literal, $($arg:tt)*) => {
        writeln!($self.output, $format, $($arg)*).unwrap();
    };
}

pub struct App<W: Write> {
    rom: Option<ROM>,
    output: W,
    commands: HashMap<&'static str, Command<Self>>,
}

impl<W: Write> App<W> {
    pub fn new(rom: ROM, output: W) -> Self {
        Self {
            rom: Some(rom),
            output,
            commands: Self::build_commands(),
        }
    }

    #[cfg(test)]
    fn new_test(output: W) -> Self {
        Self {
            rom: None,
            output,
            commands: Self::build_commands(),
        }
    }

    fn build_commands() -> HashMap<&'static str, Command<Self>> {
        hashmap! {
            "help" => command_ref!(Self, help),
            "quit" => command_ref!(Self, quit),
        }
    }

    pub fn run(&mut self) {
        let mut rl = Editor::<()>::new();
        loop {
            let prompt = "> ".yellow().to_string();
            let readline = rl.readline(prompt.as_str());
            match readline {
                Ok(line) => {
                    rl.add_history_entry(line.as_str());
                    if self.handle_line(line) {
                        break;
                    }
                }
                Err(ReadlineError::Interrupted) => continue,
                Err(ReadlineError::Eof) => break,
                _ => unreachable!(),
            }
        }
    }

    fn handle_line(&mut self, line: String) -> bool {
        let parts: Vec<&str> = line.trim().split_whitespace().collect();
        let name = parts[0];
        let args = &parts[1..];

        match self.commands.get(name) {
            Some(command) => (command.function)(self, args),
            _ => unreachable!(),
        }
    }

    command!(
        /// Show help about commands.
        fn help(&self, command: String) {
            match self.commands.get(command) {
                Some(command) => {
                    out!(
                        self,
                        "{} {}\n",
                        "Usage:".yellow(),
                        (command.usage_function)().green()
                    );
                    out!(self, "{}\n", (command.help_function)());
                }
                _ => unreachable!(),
            }
        }
    );

    command!(
        /// Quit the application.
        fn quit(&self) {
            return true;
        }
    );
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::stdout;
    use strip_ansi_escapes::Writer;

    fn run_command(command: &'static str) -> String {
        let mut buffer = Vec::new();
        let mut writer = Writer::new(&mut buffer);
        let mut app = App::new_test(&mut writer);

        app.handle_line(command.to_string());
        drop(writer);

        String::from_utf8(buffer).unwrap()
    }

    #[test]
    fn test_help_command() {
        let output = run_command("help quit");
        assert_eq!("Usage: quit\n\nQuit the application.\n\n", output);
    }

    #[test]
    fn test_quit() {
        let mut app = App::new_test(stdout());
        let exit = app.handle_line("quit".to_string());
        assert!(exit);
    }
}
