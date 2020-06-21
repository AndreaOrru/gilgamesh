use std::fs::create_dir_all;
use std::io;
use std::io::{stdout, Stdout, Write};
use std::path::Path;
use std::rc::Rc;
use std::str::FromStr;

use colored::*;
use maplit::btreemap;
use rustyline::error::ReadlineError;
use rustyline::hint::{Hinter, HistoryHinter};
use rustyline::{Context, Editor};
use rustyline_derive::{Completer, Helper, Highlighter, Validator};

use crate::analysis::Analysis;
use crate::disassembly::Disassembly;
use crate::prompt::command::Command;
use crate::prompt::error::{Error, Result};
use crate::snes::opcodes::Op;
use crate::snes::rom::ROM;
use crate::snes::state::{StateChange, UnknownReason};
use crate::snes::subroutine::Subroutine;
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

/// Custom prompt helper with history hinting.
#[derive(Completer, Helper, Highlighter, Validator)]
struct AppHelper {
    hinter: HistoryHinter,
}
impl Hinter for AppHelper {
    fn hint(&self, line: &str, pos: usize, ctx: &Context<'_>) -> Option<String> {
        match self.hinter.hint(line, pos, ctx) {
            Some(hint) => Some(hint.bright_black().to_string()),
            None => None,
        }
    }
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
        // Initialize the line editor with history hints.
        let helper = AppHelper {
            hinter: HistoryHinter {},
        };
        let mut rl = Editor::new();
        rl.set_helper(Some(helper));

        // Load history file if it exists.
        let history = shellexpand::tilde(HISTORY_FILE).into_owned();
        rl.load_history(&history).ok();

        while !self.exit {
            let prompt = self.prompt();
            let readline = rl.readline(&prompt);

            match readline {
                // Command line to be parsed.
                Ok(line) => {
                    // TODO: find a better way to handle colored hints.
                    let line = String::from_utf8(strip_ansi_escapes::strip(line).unwrap()).unwrap();
                    if !line.is_empty() {
                        rl.add_history_entry(&line);
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
            Some(pc) => format!("[{}]> ", self.analysis.label(pc, None).unwrap()).yellow(),
            None => "> ".yellow(),
        };
        prompt.to_string()
    }

    /// Find command inside the hierarchy of commands.
    fn dig_command<'a>(
        commands: &'a Command<Self>,
        parts: &[String],
    ) -> (&'a Command<Self>, usize) {
        let mut command = commands;
        let mut i = 0;

        while i < parts.len() {
            match command.subcommands.get(parts[i].as_str()) {
                Some(c) => command = &c,
                None => break,
            };
            i += 1;
        }

        (command, i)
    }

    /// Parse and execute a command.
    fn handle_line(&mut self, line: String) {
        let parts = shell_words::split(line.trim()).unwrap();

        let (command, i) = Self::dig_command(&self.commands, &parts);
        match command.function {
            Some(function) => match function(self, &parts[i..]) {
                Ok(()) => {}
                Err(e @ Error::MissingArg(_)) => {
                    self.help(&parts).unwrap();
                    outln!(self.out, "{}\n", e.to_string().red());
                }
                Err(e) => {
                    outln!(self.out, "{}\n", e.to_string().red());
                }
            },
            None => self.help(&parts).unwrap(),
        }
    }

    /// Show help and usage of a command.
    fn help_command(out: &mut W, parts: &[String], command: &Command<Self>, root: bool) {
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

    /// Get the current subroutine or raise an error.
    pub fn get_subroutine(&self) -> Result<usize> {
        self.current_subroutine.ok_or(Error::NoSelectedSubroutine)
    }

    /// Return a subroutine label formatted for display inside a list.
    fn format_subroutine(sub: &Subroutine) -> String {
        let mut s = String::new();
        if sub.has_unknown_state_change() {
            s.push_str(&sub.label().red().to_string());
            if sub.is_unknown_because_of(UnknownReason::SuspectInstruction) {
                s.push_str(&format!(" {}", "[!]".on_bright_red()));
            } else if sub.is_unknown_because_of(UnknownReason::IndirectJump) {
                s.push_str(&" [*]".red().to_string());
            } else if sub.is_unknown_because_of(UnknownReason::MultipleReturnStates) {
                s.push_str(&" [+]".red().to_string());
            }
        } else {
            s.push_str(&sub.label().green().to_string());
        }
        s
    }

    /// Print all the active instruction assertions.
    fn list_instruction_assertions(&mut self) {
        let assertions = self.analysis.instruction_assertions().borrow();
        outln!(self.out, "{}", "ASSERTED INSTRUCTION STATE CHANGES:".red());

        for (pc, state_change) in assertions.iter() {
            let subroutines = self.analysis.instruction_subroutines(*pc);
            let instruction = self.analysis.any_instruction(*pc);
            let disassembly = Disassembly::instruction_raw(instruction);

            // Instruction information.
            outln!(
                self.out,
                "  {}  {} -> {}\n",
                format!("${:06X}", *pc).magenta(),
                disassembly,
                state_change.to_string().green()
            );

            // List of subroutines containing this instruction.
            if !subroutines.is_empty() {
                let labels: Vec<_> = subroutines
                    .iter()
                    .map(|pc| self.analysis.label(*pc, None).unwrap())
                    .collect();
                outln!(self.out, "    {}\n", labels.join(", ").bright_black());
            }
        }
        outln!(self.out);
    }

    /// Print all the active subroutine assertions.
    fn list_subroutine_assertions(&mut self) {
        let assertions = self.analysis.subroutine_assertions().borrow();
        outln!(self.out, "{}", "ASSERTED SUBROUTINE STATE CHANGES:".red());

        for (sub_pc, state_changes) in assertions.iter() {
            for (instr_pc, state_change) in state_changes.iter() {
                let sub_label = self.analysis.label(*sub_pc, None).unwrap();
                let instruction = self.analysis.any_instruction(*instr_pc);
                let disassembly = Disassembly::instruction_raw(instruction);
                outln!(
                    self.out,
                    "  {:18}${:06X}  {} -> {}",
                    (sub_label + ":").magenta(),
                    instr_pc,
                    disassembly,
                    state_change.to_string().green()
                )
            }
        }
        outln!(self.out);
    }

    /**************************************************************************/

    /// Return the hierarchy of supported commands.
    fn build_commands() -> Command<Self> {
        container!(btreemap! {
            "analyze" => command_ref!(Self, analyze),
            "assert" => container!(
                /// Define known processor states for instructions and subroutines.
                btreemap! {
                    "instruction" => command_ref!(Self, assert_instruction),
                    "subroutine"  => command_ref!(Self, assert_subroutine),
                }),
            "comment" => command_ref!(Self, comment),
            "deassert" => container!(
                /// Remove previously defined assertions.
                btreemap! {
                    "instruction" => command_ref!(Self, deassert_instruction),
                    "subroutine"  => command_ref!(Self, deassert_subroutine),
                }),
            "describe" => command_ref!(Self, describe),
            "disassembly" => command_ref!(Self, disassembly),
            "help" => command_ref!(Self, help),
            "list" => container!(
                /// List various types of entities.
                btreemap! {
                    "assertions" => command_ref!(Self, list_assertions),
                    "subroutines" => command_ref!(Self, list_subroutines),
                }),
            "rom" => command_ref!(Self, rom),
            "subroutine" => command_ref!(Self, subroutine),
            "quit" => command_ref!(Self, quit),
        })
    }

    command!(
        /// Run the analysis on the ROM.
        fn analyze(&mut self) {
            self.analysis.run();
        }
    );

    command!(
        /// Define how the processor state changes after an instruction's execution.
        fn assert_instruction(&mut self, pc: Integer, state_expr: String) {
            let state_change = StateChange::from_expr(state_expr).unwrap();
            self.analysis.add_instruction_assertion(pc, state_change);
        }
    );

    command!(
        /// Define a known processor return state for a given subroutine.
        fn assert_subroutine(&mut self, pc: Integer, state_expr: String) {
            let state_change = StateChange::from_expr(state_expr).unwrap();
            self.analysis
                .add_subroutine_assertion(self.get_subroutine()?, pc, state_change);
        }
    );

    command!(
        /// Set comment for an instruction.
        fn comment(&mut self, pc: Integer, comment: String) {
            let mut comments = self.analysis.comments().borrow_mut();
            if comment.is_empty() {
                comments.remove(&pc);
            } else {
                comments.insert(pc, comment);
            }
        }
    );

    command!(
        /// Remove previously defined instruction assertions.
        fn deassert_instruction(&mut self, pc: Integer) {
            self.analysis.del_instruction_assertion(pc);
        }
    );

    command!(
        /// Remove previously defined subroutine assertions.
        fn deassert_subroutine(&mut self, pc: Integer) {
            self.analysis
                .del_subroutine_assertion(self.get_subroutine()?, pc);
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
            let subroutine = self.get_subroutine()?;
            let disassembly = Disassembly::new(self.analysis.clone());
            let s = disassembly.subroutine(subroutine);
            outln!(self.out, "{}", s);
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
        /// List active assertions.
        fn list_assertions(&mut self) {
            self.list_subroutine_assertions();
            self.list_instruction_assertions();
        }
    );

    command!(
        /// List subroutines.
        fn list_subroutines(&mut self) {
            let subroutines = self.analysis.subroutines().borrow();
            for sub in subroutines.values() {
                outln!(self.out, "{}", Self::format_subroutine(sub));
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
        assert!(output.starts_with("Usage: assert SUBCOMMAND\n\n"));
    }

    #[test]
    fn test_help_nested_command() {
        let output = run_command("help assert instruction");
        assert!(output.starts_with("Usage: assert instruction PC STATE_EXPR\n\n"));
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
