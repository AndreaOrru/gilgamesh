type CommandMethod<App> = fn(&App, &[&str]) -> bool;
type HelpMethod<App> = fn(&App) -> String;

pub struct Command<App> {
    pub function: CommandMethod<App>,
    pub help_function: HelpMethod<App>,
    pub usage_function: HelpMethod<App>,
}

impl<App> Command<App> {
    pub fn new(
        function: CommandMethod<App>,
        help_function: HelpMethod<App>,
        usage_function: HelpMethod<App>,
    ) -> Command<App> {
        Command::<App> {
            function,
            help_function,
            usage_function,
        }
    }
}

#[macro_export]
macro_rules! argument {
    ($args:ident, $i:ident, String) => {
        $args[$i]
    };

    ($args:ident, $i:ident, Integer) => {
        usize::from_str_radix($args[$i], 16).unwrap()
    };
}

#[macro_export]
macro_rules! command {
    ($self:ident, $name:ident, $help:literal, $body: expr) => {
        command!($self, $name,, $help, $body);
    };

    ($self:ident, $name:ident, $(($arg:ident : $type:ident)),*, $help:literal, $body: expr) => {
        fn $name(&$self, _args: &[&str]) -> bool {
            let mut _i = 0;
            $(
                let $arg = argument!(_args, _i, $type);
                _i += 1;
            )*
            $body
            #[allow(unreachable_code)]
            false
        }

        paste::item! {
            fn [<help_ $name>](&$self) -> String {
                $help.to_string()
            }

            fn [<usage_ $name>](&$self) -> String {
                stringify!($name).to_string()
                $(
                    + " " + &stringify!($arg).to_uppercase()
                )*
            }
        }
    };
}

#[macro_export]
macro_rules! command_ref {
    ($app:ident, $name:ident) => {
        paste::expr! {
            Command::new($app::$name, $app::[<help_ $name>], $app::[<usage_ $name>])
        }
    };
}
