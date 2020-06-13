use std::fs::create_dir_all;
use std::io;
use std::io::{stdout, Stdout, Write};
use std::path::Path;
use std::rc::Rc;
use std::str::FromStr;

use colored::*;
use maplit::btreemap;
use rustyline::error::ReadlineError;
use rustyline::Editor;

use crate::analysis::Analysis;
use crate::prompt::command::Command;
use crate::prompt::error::Error;
use crate::snes::opcodes::Op;
use crate::snes::rom::ROM;
use crate::{command, command_ref, container};

const HISTORY_FILE: &str = "~/.local/share/gilgamesh/history.log";

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
    analysis: Rc<Analysis>,
    /// Output stream.
    out: W,
    /// The hierarchy of commands.
    commands: Command<Self>,
    /// Whether the user has requested to exit.
    exit: bool,
    /// Subroutine currently under inspection.
    current_subroutine: Option<usize>,
}

impl App<Stdout> {
    /// Instantiate a prompt session from a ROM.
    pub fn new(rom_path: String) -> io::Result<Self> {
        Ok(Self {
            analysis: Analysis::new(ROM::from(rom_path)?),
            out: stdout(),
            commands: Self::build_commands(),
            exit: false,
            current_subroutine: None,
        })
    }
}

impl<W: Write> App<W> {
    /// Return the hierarchy of supported commands.
    fn build_commands() -> Command<Self> {
        container!(btreemap! {
            "analyze" => command_ref!(Self, analyze),
            "assert" => container!(
                /// Assert stuff.
                btreemap! {
                    "instruction" => command_ref!(Self, assert_instruction),
                    "subroutine"  => command_ref!(Self, assert_subroutine),
                }),
            "describe" => command_ref!(Self, describe),
            "disassembly" => command_ref!(Self, disassembly),
            "help" => command_ref!(Self, help),
            "list" => container!(
                /// List various types of entities.
                btreemap! {
                    "subroutines"  => command_ref!(Self, list_subroutines),
                }),
            "rom" => command_ref!(Self, rom),
            "subroutine" => command_ref!(Self, subroutine),
            "quit" => command_ref!(Self, quit),
        })
    }

    /// Instantiate a prompt with redirected output (for test purposes).
    #[cfg(test)]
    fn with_output(out: W) -> Self {
        Self {
            analysis: Analysis::new(ROM::new()),
            out,
            commands: Self::build_commands(),
            exit: false,
            current_subroutine: None,
        }
    }

    /// Start the prompt loop.
    pub fn run(&mut self) {
        let mut rl = Editor::<()>::new();

        // Load history file if it exists.
        let history = shellexpand::tilde(HISTORY_FILE).into_owned();
        rl.load_history(&history).ok();

        while !self.exit {
            let prompt = self.prompt();
            let readline = rl.readline(prompt.as_str());

            match readline {
                // Command line to be parsed.
                Ok(line) => {
                    if !line.is_empty() {
                        rl.add_history_entry(line.as_str());
                        self.handle_line(line);
                    }
                }
                Err(ReadlineError::Interrupted) => continue, // Ctrl-C.
                Err(ReadlineError::Eof) => break,            // Ctrl-D.
                _ => unreachable!(),
            }
        }

        // Save history file, creating parent folders if necessary.
        create_dir_all(Path::new(&history).parent().unwrap()).ok();
        rl.save_history(&history).unwrap();
    }

    fn prompt(&self) -> String {
        let prompt = match self.current_subroutine {
            Some(pc) => format!("[{}]> ", self.analysis.label(pc).unwrap()).yellow(),
            None => "> ".yellow(),
        };
        prompt.to_string()
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
    fn handle_line(&mut self, line: String) {
        let parts: Vec<&str> = line.trim().split_whitespace().collect();

        let (command, i) = Self::dig_command(&self.commands, &parts);
        match command.function {
            Some(function) => match function(self, &parts[i..]) {
                Ok(()) => {}
                Err(e @ Error::MissingArg(_)) => {
                    self.help(&parts).unwrap();
                    outln!(self.out, "{}\n", e.to_string().red());
                }
            },
            None => self.help(&parts).unwrap(),
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
        /// Run the analysis on the ROM.
        fn analyze(&mut self) {
            self.analysis.run();
        }
    );

    command!(
        /// Describe an opcode.
        fn describe(&mut self, opcode: String) {
            if let Ok(op) = Op::from_str(&opcode.to_uppercase()) {
                outln!(self.out, "{}\n", op.description());
            }
        }
    );

    command!(
        /// Show disassembly of selected subroutine.
        fn disassembly(&mut self) {
            let subroutines = self.analysis.subroutines().borrow();
            let sub = &subroutines[&self.current_subroutine.unwrap()];

            for instruction in sub.instructions().iter() {
                outln!(
                    self.out,
                    "{}",
                    instruction.disassembly(self.analysis.clone())
                );
            }
        }
    );

    command!(
        /// Show help about commands.
        fn help(&mut self, command: Args) {
            let (cmd, i) = Self::dig_command(&self.commands, command);
            let root = i == 0;
            Self::help_command(&mut self.out, &command[..i], cmd, root);
            Self::help_list(&mut self.out, cmd, root);
            outln!(self.out);
        }
    );

    command!(
        /// List subroutines.
        fn list_subroutines(&mut self) {
            let subroutines = self.analysis.subroutines().borrow();
            for (_, sub) in subroutines.iter() {
                outln!(self.out, "{}", sub.label().green());
            }
            outln!(self.out);
        }
    );

    #[rustfmt::skip]
    command!(
        /// Show general information on the ROM.
        fn rom(&mut self) {
            let rom = &self.analysis.rom;
            outln!(self.out, "{:10}{}", "Title:".green(), rom.title());
            outln!(self.out, "{:10}{}", "Type:".green(), rom.rom_type().as_ref());
            outln!(self.out, "{:10}{}", "Size:".green(), rom.size() / 1024);
            outln!(self.out, "{:10}",   "Vectors:".green());
            outln!(self.out, "  {:8}${:06X}", "RESET:".green(), rom.reset_vector());
            outln!(self.out, "  {:8}${:06X}", "NMI:".green(), rom.nmi_vector());
            outln!(self.out);
        }
    );

    command!(
        /// Select which subroutine to inspect.
        fn subroutine(&mut self, label: String) {
            let sub = self.analysis.label_value(label);
            if let Some(pc) = sub {
                self.current_subroutine = Some(pc);
            }
        }
    );

    command!(
        /// Quit the application.
        fn quit(&mut self) {
            self.exit = true;
        }
    );

    command!(
        /// Assert instruction.
        fn assert_instruction(&mut self, _pc: Integer) {
            // TODO: implement.
        }
    );

    command!(
        /// Assert subroutine.
        fn assert_subroutine(&mut self) {
            // TODO: implement.
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
        assert_eq!("Usage: quit\n\nQuit the application.\n\n", output);
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
            "Usage: assert instruction _PC\n\nAssert instruction.\n\n",
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
    fn test_missing_argument() {
        let output = run_command("describe");
        assert!(output.ends_with("Missing argument OPCODE.\n\n"));
    }

    #[test]
    fn test_quit() {
        let mut app = App::with_output(stdout());
        app.handle_line("quit".to_string());
        assert!(app.exit);
    }
}
