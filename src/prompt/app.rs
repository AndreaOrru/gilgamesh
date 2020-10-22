use std::borrow::Cow::{self, Owned};
use std::collections::{HashMap, HashSet};
use std::fs::{create_dir_all, read_to_string, File};
use std::io;
use std::io::{stdout, Stdout, Write};
use std::path::Path;
use std::rc::Rc;
use std::str::FromStr;

use colored::*;
use itertools::sorted;
use maplit::btreemap;
use rustyline::error::ReadlineError;
use rustyline::highlight::Highlighter;
use rustyline::hint::{Hinter, HistoryHinter};
use rustyline::{Context, Editor};
use rustyline_derive::{Completer, Helper, Validator};

use crate::analysis::Analysis;
use crate::disassembly::Disassembly;
use crate::prompt::command::Command;
use crate::prompt::error::{Error, Result};
use crate::snes::opcodes::Op;
use crate::snes::rom::ROM;
use crate::snes::state::{State, StateChange, UnknownReason};
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
#[derive(Completer, Helper, Validator)]
struct AppHelper {
    highlighter: AppHighlighter,
    hinter: HistoryHinter,
}
impl Hinter for AppHelper {
    type Hint = String;
    fn hint(&self, line: &str, pos: usize, ctx: &Context<'_>) -> Option<String> {
        self.hinter.hint(line, pos, ctx)
    }
}
/// Highlight hints in bright black.
struct AppHighlighter {}
impl Highlighter for AppHighlighter {
    fn highlight_hint<'h>(&self, hint: &'h str) -> Cow<'h, str> {
        Owned(hint.bright_black().to_string())
    }
}
impl Highlighter for AppHelper {
    fn highlight_hint<'h>(&self, hint: &'h str) -> Cow<'h, str> {
        self.highlighter.highlight_hint(hint)
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
            highlighter: AppHighlighter {},
            hinter: HistoryHinter {},
        };
        let mut rl = Editor::new();
        rl.set_helper(Some(helper));

        // Load history file if it exists.
        let history = shellexpand::tilde(HISTORY_FILE).into_owned();
        rl.load_history(&history).ok();

        // Load analysis saved state if it exists.
        if self.load_analysis().is_err() {
            self.analysis.run();
        }

        while !self.exit {
            let prompt = self.prompt();
            let readline = rl.readline(&prompt);

            match readline {
                // Command line to be parsed.
                Ok(line) => {
                    if !line.is_empty() {
                        rl.add_history_entry(&line);
                        self.handle_line(line);
                    }
                }
                Err(ReadlineError::Interrupted) => continue, // Ctrl-C.
                Err(ReadlineError::Eof) => self.exit = true, // Ctrl-D.
                _ => unreachable!(),
            }

            // Ask for confirmation before exiting.
            if self.exit && !Self::yes_no_prompt("Are you sure you want to quit without saving?") {
                self.exit = false;
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
                let name = if subcommand.subcommands.is_empty() {
                    name.to_string()
                } else {
                    format!("{}...", name)
                };
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
    fn format_subroutine(&self, sub: &Subroutine) -> String {
        let mut s = String::new();

        // Pick foreground color.
        let mut fg = if sub.has_unknown_state_change() {
            "red"
        } else if self.analysis.subroutine_contains_assertions(sub.pc()) {
            "magenta"
        } else if self.analysis.is_jump_table_target(sub.pc()) {
            "blue"
        } else {
            "green"
        };
        // Pick background color.
        let mut bg = None;
        if self.analysis.is_entry_point(sub.pc()) {
            bg = Some(fg);
            fg = "black";
        }
        // Add label.
        if let Some(bg) = bg {
            s.push_str(&sub.label().color(fg).on_color(bg).to_string());
        } else {
            s.push_str(&sub.label().color(fg).to_string());
        }

        // Add state indicators.
        if sub.has_unknown_state_change() {
            if sub.is_unknown_because_of(UnknownReason::SuspectInstruction) {
                s.push_str(&format!(" {}", "[!]".on_bright_red()));
            } else if sub.is_unknown_because_of(UnknownReason::StackManipulation) {
                s.push_str(&" [?]".red().to_string());
            } else if sub.is_unknown_because_of(UnknownReason::IndirectJump) {
                s.push_str(&" [*]".red().to_string());
            } else if sub.is_unknown_because_of(UnknownReason::MultipleReturnStates) {
                s.push_str(&" [+]".red().to_string());
            } else if sub.is_unknown_because_of(UnknownReason::Recursion) {
                s.push_str(&" [∞]".red().to_string());
            } else if sub.is_unknown_because_of(UnknownReason::MutableCode) {
                s.push_str(&" [$]".red().to_string());
            }
        }
        // Asserted jumptable.
        if self.analysis.subroutine_contains_jumptable(sub.pc()) {
            s.push_str(&" [*]".magenta().to_string());
        }
        // Multiple known return states.
        if sub.unique_state_changes().len() > 1 {
            s.push_str(&" [+]".yellow().to_string());
        }

        s
    }

    /// Print all the active instruction assertions.
    fn list_instruction_assertions(&mut self) {
        let assertions = self.analysis.instruction_assertions().borrow();
        outln!(self.out, "{}", "ASSERTED INSTRUCTION STATE CHANGES:".red());

        for (pc, state_change) in assertions.iter() {
            let instruction = self.analysis.any_instruction(*pc);
            let disassembly = Disassembly::instruction_raw(instruction);
            outln!(
                self.out,
                "  {}  {} -> {}",
                format!("${:06X}", *pc).magenta(),
                disassembly,
                state_change.to_string().green()
            );

            let sub_labels = self.analysis.instruction_subroutine_labels(*pc);
            if !sub_labels.is_empty() {
                outln!(self.out, "    {}", sub_labels.join(", ").bright_black());
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

    /// Load the state of the analysis from a JSON file.
    fn load_analysis(&mut self) -> Result<()> {
        let json_path = self.analysis.rom.json_path();
        let json = read_to_string(json_path)?;
        self.analysis = Analysis::from_json(json)?;
        Ok(())
    }

    /// Print a stacks of subroutine calls.
    fn print_stack_traces(&mut self, stack_traces: HashSet<Vec<usize>>) {
        outln!(self.out, "{}", "STACK TRACES:".red());

        let subroutines = self.analysis.subroutines().borrow();
        if stack_traces.is_empty() {
            outln!(self.out, "{}", "  Entry point.");
        } else {
            for stack_trace in stack_traces.iter() {
                for caller_pc in stack_trace.iter() {
                    let caller = subroutines.get(caller_pc).unwrap();
                    outln!(
                        self.out,
                        "  ${:06X}  {}",
                        caller.pc(),
                        self.format_subroutine(caller)
                    );
                }
                outln!(self.out);
            }
        }
    }

    /// Show the changes in processor state caused by the execution of a subroutine.
    fn print_state_changes(
        &mut self,
        known: HashMap<usize, StateChange>,
        unknown: HashMap<usize, StateChange>,
    ) {
        outln!(self.out, "{}", "STATE CHANGES:".red());

        let mut state_changes: Vec<(usize, StateChange)> =
            known.into_iter().chain(unknown).collect();
        state_changes.sort();

        for (instr_pc, change) in state_changes.iter() {
            let s = change.to_string();
            outln!(
                self.out,
                "  ${:06X}  {}",
                instr_pc,
                if change.unknown() { s.red() } else { s.green() }
            );
        }
        outln!(self.out);
    }

    /// Show a yes/no prompt, return true if yes, false otherwise.
    fn yes_no_prompt(question: &str) -> bool {
        let mut rl = Editor::<()>::new();
        let s = rl.readline(&format!("{} (y/n) ", question).yellow().to_string());
        s.unwrap_or_else(|_| "n".to_string()) == "y"
    }

    /***************************************************************************/

    /// Return the hierarchy of supported commands.
    fn build_commands() -> Command<Self> {
        container!(btreemap! {
            "analyze" => command_ref!(Self, analyze),
            "assert" => container!(
                /// Define known processor states for instructions and subroutines.
                btreemap! {
                    "entrypoint" => command_ref!(Self, assert_entrypoint),
                    "instruction" => command_ref!(Self, assert_instruction),
                    "jump" => command_ref!(Self, assert_jump),
                    "jumptable" => command_ref!(Self, assert_jumptable),
                    "subroutine"  => command_ref!(Self, assert_subroutine),
                }),
            "autoanalyze" => command_ref!(Self, autoanalyze),
            "comment" => command_ref!(Self, comment),
            "deassert" => container!(
                /// Remove previously defined assertions.
                btreemap! {
                    "instruction" => command_ref!(Self, deassert_instruction),
                    "jump" => command_ref!(Self, deassert_jump),
                    "jumptable" => command_ref!(Self, deassert_jumptable),
                    "subroutine"  => command_ref!(Self, deassert_subroutine),
                }),
            "describe" => command_ref!(Self, describe),
            "disassembly" => command_ref!(Self, disassembly),
            "help" => command_ref!(Self, help),
            "list" => container!(
                /// List various types of entities.
                btreemap! {
                    "assertions" => command_ref!(Self, list_assertions),
                    "jumps" => command_ref!(Self, list_jumps),
                    "subroutines" => command_ref!(Self, list_subroutines),
                }),
            "load" => command_ref!(Self, load),
            "memory" => command_ref!(Self, memory),
            "rename" => command_ref!(Self, rename),
            "reset" => command_ref!(Self, reset),
            "rom" => command_ref!(Self, rom),
            "save" => command_ref!(Self, save),
            "subroutine" => command_ref!(Self, subroutine),
            "query" => container!(
                /// Query the analysis log in various ways.
                btreemap! {
                    "subroutine" => command_ref!(Self, query_subroutine),
                }),
            "translate" => command_ref!(Self, translate),
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
        /// Add an entry point to the analysis.
        fn assert_entrypoint(&mut self, pc: Integer, name: String, state_expr: String) {
            let state = State::from_expr(state_expr).unwrap();
            self.analysis.add_entry_point(pc, name, state)?;
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
        /// Define an indirect jump target.
        fn assert_jump(&mut self, caller_pc: Integer, target_pc: Integer) {
            self.analysis
                .add_jump_assertion(caller_pc, Some(target_pc), None);
        }
    );

    command!(
        /// Define a jump table.
        fn assert_jumptable(&mut self, caller_pc: Integer, range: Range) {
            self.analysis.add_jumptable_assertion(caller_pc, range);
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
        /// Analyze and apply suggested assertions as far as possible.
        fn autoanalyze(&mut self) {
            self.analysis.auto_run();
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
        /// Remove previously defined jump assertion.
        fn deassert_jump(&mut self, caller_pc: Integer, ?target_pc: Integer) {
            self.analysis.del_jump_assertion(caller_pc, target_pc);
        }
    );

    command!(
        /// Remove previously defined jump table assertion.
        fn deassert_jumptable(&mut self, caller_pc: Integer, range: Range) {
            self.analysis.del_jumptable_assertion(caller_pc, range);
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
        /// List indirect jumps.
        fn list_jumps(&mut self) {
            let assertions = self.analysis.jump_assertions().borrow();
            let jumps = self.analysis.indirect_jumps().borrow();
            let jump_pcs = sorted(jumps.keys().copied());

            for pc in jump_pcs {
                let instruction = self.analysis.any_instruction(pc);
                let disassembly = Disassembly::instruction_raw(instruction);
                let color = if assertions.contains_key(&pc) {
                    "magenta"
                } else {
                    "red"
                };

                outln!(
                    self.out,
                    "{}  {}",
                    format!("${:06X}", pc).color(color),
                    disassembly
                );

                let sub_labels = self.analysis.instruction_subroutine_labels(pc);
                if !sub_labels.is_empty() {
                    outln!(self.out, "  {}", sub_labels.join(", ").bright_black());
                }
            }
            outln!(self.out);
        }
    );

    command!(
        /// List subroutines.
        fn list_subroutines(&mut self) {
            let subroutines = self.analysis.subroutines().borrow();
            for sub in subroutines.values() {
                outln!(
                    self.out,
                    "${:06X}  {}",
                    sub.pc(),
                    self.format_subroutine(sub)
                );
            }
            outln!(self.out);
        }
    );

    command!(
        /// Load the state of the analysis from a JSON file.
        fn load(&mut self) {
            if Self::yes_no_prompt("Are you sure you want to load the saved analysis?") {
                self.load_analysis()?;
            }
        }
    );

    command!(
        /// Show an hex view of a region of the ROM.
        fn memory(&mut self, address: Integer, size: Integer, step: Integer) {
            if step > 16 {
                return Err(Error::InvalidStepSize);
            }

            let mut s = String::new();
            let nl_threshold = (16 / step) * step;

            // Table header.
            let header = {
                let mut s = Vec::new();
                for n in (0..nl_threshold).step_by(step) {
                    s.push(format!("{:02X}", n));
                }
                s.push("".to_string());
                s.join(&" ".repeat((2 * step) - 1))
            };
            s.push_str(&format!("{:8}│ {}\n", "", header).bright_black().to_string());
            s.push_str(
                &format!("{}┼{}\n", "─".repeat(8), "─".repeat(header.len()))
                    .bright_black()
                    .to_string(),
            );

            // Table body.
            let colors = ["white", "cyan"];
            for (color_idx, i) in (address..address + size).step_by(step).enumerate() {
                // Base address.
                if (i - address) % nl_threshold == 0 {
                    if i - address != 0 {
                        s.push('\n');
                    }
                    s.push_str(&format!("${:06X} │ ", i).bright_black().to_string());
                }
                // Bytes.
                for (j, b) in self.analysis.rom.read(i, step).iter().enumerate() {
                    let color = match self.analysis.find_instruction(i + j) {
                        Some(_) => "yellow",
                        None => colors[color_idx % colors.len()],
                    };
                    s.push_str(&format!("{:02X}", b).color(color).to_string());
                }
                s.push(' ');
            }

            outln!(self.out, "{}\n", s);
        }
    );

    command!(
        /// Rename a label or subroutine.
        fn rename(&mut self, old_or_new: String, ?new: String) {
            if let Some(new) = new {
                // Rename a label or subroutine.
                let old = old_or_new;
                self.analysis.rename_label(old, new, self.current_subroutine)?;
            } else {
                // Rename current subroutine.
                let new = old_or_new;
                let old = self.analysis.label(self.get_subroutine()?, None).unwrap();
                self.analysis.rename_label(old, new, None)?;
            };
        }
    );

    command!(
        /// Reset the analysis (start from scratch).
        fn reset(&mut self) {
            if Self::yes_no_prompt("Are you sure you want to reset the entire analysis?") {
                self.analysis.reset();
                self.analysis.run();
                self.current_subroutine = None;
            }
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
        /// Save the state of the analysis to a JSON file.
        fn save(&mut self) {
            let json = self.analysis.to_json();
            let json_path = self.analysis.rom.json_path();

            // Ask for confirmation before overwriting an existing analysis.
            if !Path::new(&json_path).exists()
                || Self::yes_no_prompt("Are you sure you want to overwrite the saved analysis?")
            {
                let mut json_file = File::create(json_path).unwrap();
                json_file.write_all(json.as_bytes()).unwrap();
            }
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
        /// Show information on a subroutine (such as state and stack trace).
        fn query_subroutine(&mut self, ?label: String) {
            let (stack_traces, known_changes, unknown_changes) = {
                let sub_pc = match label {
                    Some(label) => self.analysis.label_value(label).unwrap(),
                    None => self.get_subroutine()?,
                };
                let subs = self.analysis.subroutines().borrow();
                let sub = subs.get(&sub_pc).unwrap();
                (sub.stack_traces().to_owned(), sub.state_changes().to_owned(), sub.unknown_state_changes().to_owned())
            };
            self.print_stack_traces(stack_traces);
            self.print_state_changes(known_changes, unknown_changes);
        }
    );

    command!(
        /// Translate a SNES address to a PC address.
        fn translate(&mut self, address: Integer) {
            let translated = self.analysis.rom.translate(address);
            outln!(self.out, "{} ${:06X}", "SNES:".green(), address);
            outln!(self.out, "{} ${:06X}", "PC:  ".green(), translated);
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
