use std::error;
use std::fmt;

/// Gilgamesh error type.
#[derive(Debug)]
pub enum Error {
    NoSelectedSubroutine,
    MissingArg(String),
}

impl error::Error for Error {}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Error::NoSelectedSubroutine => write!(f, "No selected subroutine."),
            Error::MissingArg(s) => write!(f, "Missing argument {}.", s),
        }
    }
}

pub type Result<T> = std::result::Result<T, Error>;
