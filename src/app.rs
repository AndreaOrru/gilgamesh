use colored::*;
use lazy_static::lazy_static;
use maplit::hashmap;
use rustyline::error::ReadlineError;
use rustyline::Editor;
use std::collections::HashMap;

use crate::command::Command;
use crate::rom::ROM;
use crate::{argument, command, command_ref};

lazy_static! {
    static ref COMMANDS: HashMap<&'static str, Command<App>> = hashmap! {
        "help" => command_ref!(App, help),
        "quit" => command_ref!(App, quit),
    };
}

pub struct App {
    rom: ROM,
}

impl App {
    pub fn new(rom: ROM) -> App {
        App { rom }
    }

    pub fn run(&self) {
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

    fn handle_line(&self, line: String) -> bool {
        let parts: Vec<&str> = line.trim().split_whitespace().collect();
        let name = parts[0];
        let args = &parts[1..];

        match COMMANDS.get(name) {
            Some(command) => (command.function)(self, args),
            _ => unreachable!(),
        }
    }

    command!(
        self,
        help,
        (command: String),
        "Show help about commands.",
        {
            match COMMANDS.get(command) {
                Some(command) => {
                    println!(
                        "{} {}\n",
                        "Usage:".yellow(),
                        (command.usage_function)(self).green()
                    );
                    println!("{}\n", (command.help_function)(self));
                }
                _ => unreachable!(),
            }
        }
    );

    command!(self, quit, "Quit the application.", {
        return true;
    });
}
