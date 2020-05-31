type CommandMethod<App> = fn(&mut App, &[&str]) -> bool;
type HelpMethod = fn() -> &'static String;

pub struct Command<App> {
    pub function: CommandMethod<App>,
    pub help_function: HelpMethod,
    pub usage_function: HelpMethod,
}

impl<App> Command<App> {
    pub fn new(
        function: CommandMethod<App>,
        help_function: HelpMethod,
        usage_function: HelpMethod,
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
    (
        #[doc = $help:expr]
        fn $name:ident(&$self:ident $(, $arg:ident : $type:ident)*) $body:expr
    ) => {
        fn $name(&mut $self, _args: &[&str]) -> bool {
            let mut _i = 0;
            $(
                let $arg = $crate::argument!(_args, _i, $type);
                _i += 1;
            )*
            $body
            #[allow(unreachable_code)]
            false
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
                        stringify!($name).to_string()
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

#[macro_export]
macro_rules! command_ref {
    ($app:ident, $name:ident) => {
        paste::expr! {
            Command::new($app::$name, $app::[<help_ $name>], $app::[<usage_ $name>])
        }
    };
}
