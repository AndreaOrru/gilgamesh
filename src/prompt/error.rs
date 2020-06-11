use std::error;
use std::fmt;

/// Gilgamesh error type.
#[derive(Debug)]
pub enum Error {
    MissingArg(String),
}

impl error::Error for Error {}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Error::MissingArg(s) => write!(f, "Missing argument {}.", s),
        }
    }
}
