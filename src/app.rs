use std::io;
use std::io::{stdout, Stdout, Write};

use colored::*;
use maplit::btreemap;
use rustyline::error::ReadlineError;
use rustyline::Editor;

use crate::analysis::Analysis;
use crate::command::Command;
use crate::snes::rom::ROM;
use crate::{command, command_ref, container};

/// Wrapper around `println!` using the given output stream.
macro_rules! outln {
    ($out:expr) => {
        writeln!($out, "").unwrap();
    };

    ($out:expr, $format:literal, $($args:expr),*) => {
        writeln!($out, $format, $($args,)*).unwrap();
    };
}

/// Gilgamesh's interactive prompt.
pub struct App<W: Write> {
    analysis: Analysis,
    /// Output stream.
    out: W,
    /// The hierarchy of commands.
    commands: Command<Self>,
}

impl App<Stdout> {
    /// Instantiate a prompt session from a ROM.
    pub fn new(rom_path: String) -> io::Result<Self> {
        Ok(Self {
            analysis: Analysis::new(ROM::from(rom_path)?),
            out: stdout(),
            commands: Self::build_commands(),
        })
    }
}

impl<W: Write> App<W> {
    /// Instantiate a prompt with redirected output (for test purposes).
    #[cfg(test)]
    fn with_output(out: W) -> Self {
        Self {
            analysis: Analysis::new(ROM::new()),
            out,
            commands: Self::build_commands(),
        }
    }

    /// Return the hierarchy of supported commands.
    fn build_commands() -> Command<Self> {
        container!(btreemap! {
            "assert" => container!(
                /// Assert stuff.
                btreemap! {
                    "instruction" => command_ref!(Self, assert_instruction),
                    "subroutine"  => command_ref!(Self, assert_subroutine),
                }),

            "help" => command_ref!(Self, help),
            "quit" => command_ref!(Self, quit),
        })
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
                    if !line.is_empty() {
                        rl.add_history_entry(line.as_str());
                        // Commands return true to signal an exit condition.
                        if self.handle_line(line) {
                            break;
                        }
                        outln!(self.out);
                    }
                }
                Err(ReadlineError::Interrupted) => continue, // Ctrl-C.
                Err(ReadlineError::Eof) => break,            // Ctrl-D.
                _ => unreachable!(),
            }
        }
    }

    /// Find command inside the hierarchy of commands.
    fn dig_command<'a>(commands: &'a Command<Self>, parts: &[&str]) -> (&'a Command<Self>, usize) {
        let mut command = commands;
        let mut i = 0;

        while i < parts.len() {
            match command.subcommands.get(parts[i]) {
                Some(c) => command = &c,
                None => break,
            };
            i += 1;
        }

        (command, i)
    }

    /// Parse and execute a command.
    fn handle_line(&mut self, line: String) -> bool {
        let parts: Vec<&str> = line.trim().split_whitespace().collect();

        let (command, i) = Self::dig_command(&self.commands, &parts);
        match command.function {
            Some(function) => function(self, &parts[i..]),
            None => self.help(&parts),
        }
    }

    /// Show help and usage of a command.
    fn help_command(out: &mut W, parts: &[&str], command: &Command<Self>, root: bool) {
        if !root {
            outln!(
                out,
                "{} {}{}\n",
                "Usage:".yellow(),
                parts.join(" ").green(),
                (command.usage_function)().green()
            );
            outln!(out, "{}", (command.help_function.unwrap())());
        }
    }

    /// Show a list of subcommands.
    fn help_list(out: &mut W, command: &Command<Self>, root: bool) {
        if !command.subcommands.is_empty() {
            if root {
                outln!(out, "{}", "Commands:".yellow());
            } else {
                outln!(out, "\n{}", "Subcommands:".yellow());
            }
            for (name, subcommand) in command.subcommands.iter() {
                outln!(
                    out,
                    "  {:15}{}",
                    name.green(),
                    (subcommand.help_function.unwrap())()
                );
            }
        }
    }

    command!(
        /// Show help about commands.
        fn help(&mut self, command: Args) {
            let (cmd, i) = Self::dig_command(&self.commands, command);
            let root = i == 0;
            Self::help_command(&mut self.out, &command[..i], cmd, root);
            Self::help_list(&mut self.out, cmd, root);
        }
    );

    command!(
        /// Quit the application.
        fn quit(&mut self) {
            return true;
        }
    );

    command!(
        /// Assert instruction.
        fn assert_instruction(&mut self, pc: Integer) {
            // TODO: implement.
            return true;
        }
    );

    command!(
        /// Assert subroutine.
        fn assert_subroutine(&mut self) {
            // TODO: implement.
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
    fn test_help() {
        let output = run_command("help");
        assert!(output.starts_with("Commands:"));
        assert!(output.contains("quit"));
        assert!(output.contains("Quit the application."));
    }

    #[test]
    fn test_help_simple_command() {
        let output = run_command("help quit");
        assert_eq!("Usage: quit\n\nQuit the application.\n", output);
    }

    #[test]
    fn test_help_command_container() {
        let output = run_command("help assert");
        assert!(output.starts_with("Usage: assert SUBCOMMAND\n\nAssert stuff."));
    }

    #[test]
    fn test_help_nested_command() {
        let output = run_command("help assert instruction");
        assert_eq!(
            "Usage: assert instruction PC\n\nAssert instruction.\n",
            output
        );
    }

    #[test]
    fn test_help_invalid_command() {
        let output = run_command("help foobar");
        assert!(output.starts_with("Commands:"));
    }

    #[test]
    fn test_help_invalid_subcommand() {
        let output = run_command("help assert foobar");
        assert!(output.starts_with("Usage: assert SUBCOMMAND"));
    }

    #[test]
    fn test_quit() {
        let mut app = App::with_output(stdout());
        let exit = app.handle_line("quit".to_string());
        assert!(exit);
    }
}
