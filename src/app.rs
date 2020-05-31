use std::collections::HashMap;
use std::io::{stdout, Stdout, Write};

use colored::*;
use maplit::hashmap;
use rustyline::error::ReadlineError;
use rustyline::Editor;

use crate::command::Command;
use crate::rom::ROM;
use crate::{command, command_ref};

/// Wrapper around `println!` using the configured output stream.
macro_rules! out {
    ($self:ident) => {
        out!($self, "");
    };

    ($self:ident, $format:literal, $($arg:tt)*) => {
        writeln!($self.output, $format, $($arg)*).unwrap();
    };
}

/// Gilgamesh's interactive prompt.
pub struct App<W: Write> {
    /// ROM on which Gilgamesh is operating.
    rom: Option<ROM>,
    /// Output stream.
    output: W,
    /// The hierarchy of commands.
    commands: HashMap<&'static str, Command<Self>>,
}

impl App<Stdout> {
    /// Instantiate a prompt session from a ROM.
    pub fn new(rom: ROM) -> Self {
        Self {
            rom: Some(rom),
            output: stdout(),
            commands: Self::build_commands(),
        }
    }
}

impl<W: Write> App<W> {
    /// Instantiate a prompt with redirected output (for test purposes).
    #[cfg(test)]
    fn with_output(output: W) -> Self {
        Self {
            rom: None,
            output,
            commands: Self::build_commands(),
        }
    }

    /// Return the hierarchy of supported commands.
    fn build_commands() -> HashMap<&'static str, Command<Self>> {
        hashmap! {
            "help" => command_ref!(Self, help),
            "quit" => command_ref!(Self, quit),
        }
    }

    /// Start the prompt loop.
    pub fn run(&mut self) {
        let mut rl = Editor::<()>::new();
        loop {
            let prompt = "> ".yellow().to_string();
            let readline = rl.readline(prompt.as_str());

            match readline {
                // Command line to be parsed.
                Ok(line) => {
                    rl.add_history_entry(line.as_str());
                    // Commands return true to signal an exit condition.
                    if self.handle_line(line) {
                        break;
                    }
                }
                Err(ReadlineError::Interrupted) => continue, // Ctrl-C.
                Err(ReadlineError::Eof) => break,            // Ctrl-D.
                _ => unreachable!(),
            }
        }
    }

    /// Parse and execute a command.
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

    /// Run a command in the prompt and return its output.
    fn run_command(command: &'static str) -> String {
        // Redirected de-colored output to a vector.
        let mut buffer = Vec::new();
        let mut writer = Writer::new(&mut buffer);
        let mut app = App::with_output(&mut writer);

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
        let mut app = App::with_output(stdout());
        let exit = app.handle_line("quit".to_string());
        assert!(exit);
    }
}