use std::collections::BTreeMap;

use lazy_static::lazy_static;

use crate::prompt::error::Error;

type CommandFunction<App> = fn(&mut App, &[&str]) -> Result<(), Error>;
type HelpFunction = fn() -> &'static String;

/// Command for the interactive prompt.
pub struct Command<App> {
    pub function: Option<CommandFunction<App>>,
    pub help_function: Option<HelpFunction>,
    pub usage_function: HelpFunction,
    pub subcommands: BTreeMap<&'static str, Self>,
}

impl<App> Command<App> {
    /// Instantiate a command.
    pub fn new(
        function: CommandFunction<App>,
        help_function: HelpFunction,
        usage_function: HelpFunction,
    ) -> Self {
        Self {
            function: Some(function),
            help_function: Some(help_function),
            usage_function,
            subcommands: BTreeMap::new(),
        }
    }

    /// Instantiate a container.
    pub fn new_container(
        help_function: HelpFunction,
        subcommands: BTreeMap<&'static str, Self>,
    ) -> Self {
        Self {
            function: None,
            help_function: Some(help_function),
            usage_function: usage_container,
            subcommands,
        }
    }
}

/// Return usage string for container commands.
pub fn usage_container() -> &'static String {
    lazy_static! {
        static ref USAGE: String = String::from(" SUBCOMMAND");
    }
    &USAGE
}

/// Fetch a command argument based on its type and position.
#[macro_export]
macro_rules! argument {
    ($args:ident, $i:ident, $arg:ident, Args) => {
        $args
    };

    ($args:ident, $i:ident, $arg:ident, String) => {
        $args
            .get($i)
            .ok_or($crate::prompt::error::Error::MissingArg(
                stringify!($arg).to_uppercase(),
            ))?
    };

    ($args:ident, $i:ident, $arg:ident, Integer) => {
        usize::from_str_radix($args[$i], 16).unwrap()
    };
}

/// Define a command for the interactive prompt.
#[macro_export]
macro_rules! command {
    (
        #[doc = $help:expr]
        fn $name:ident(&mut $self:ident $(, $arg:ident : $type:ident)*) $body:expr
    ) => {
        fn $name(&mut $self, _args: &[&str]) -> Result<(), $crate::prompt::error::Error> {
            let mut _i = 0;
            $(
                let $arg = $crate::argument!(_args, _i, $arg, $type);
                _i += 1;
            )*
            $body
            #[allow(unreachable_code)]
            Ok(())
        }

        paste::item! {
            fn [<help_ $name>]() -> &'static String {
                lazy_static::lazy_static! {
                    static ref [<HELP_ $name:upper>]: String = $help.trim().to_string();
                }
                &[<HELP_ $name:upper>]
            }

            fn [<usage_ $name>]() -> &'static String {
                lazy_static::lazy_static! {
                    static ref [<USAGE_ $name:upper>]: String = {
                        String::new()
                        $(
                            + " " + &stringify!($arg).to_uppercase()
                        )*
                    };
                }
                &[<USAGE_ $name:upper>]
            }
        }
    };
}

/// Create a reference to a prompt command (used to define the hierarchy of commands).
#[macro_export]
macro_rules! command_ref {
    ($app:ident, $name:ident) => {
        paste::expr! {
            Command::new(
                $app::$name,
                $app::[<help_ $name>],
                $app::[<usage_ $name>],
            )
        }
    };
}

/// Define a command container.
#[macro_export]
macro_rules! container {
    (
        #[doc = $help:expr]
        $subcmds:expr
    ) => {{
        fn help() -> &'static String {
            lazy_static::lazy_static! {
                static ref HELP: String = $help.trim().to_string();
            }
            &HELP
        }
        Command::new_container(help, $subcmds)
    }};

    ($subcmds:expr) => {
        container!(
            ///
            $subcmds
        )
    };
}
