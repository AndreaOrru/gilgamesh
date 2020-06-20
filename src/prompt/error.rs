use std::error;
use std::fmt;
use std::num::ParseIntError;

/// Gilgamesh error type.
#[derive(Debug)]
pub enum Error {
    InvalidStateExpr,
    MissingArg(String),
    NoSelectedSubroutine,
    ParseInt(ParseIntError),
}

impl error::Error for Error {}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Error::InvalidStateExpr => write!(f, "Invalid state expression."),
            Error::MissingArg(s) => write!(f, "Missing argument {}.", s),
            Error::NoSelectedSubroutine => write!(f, "No selected subroutine."),
            Error::ParseInt(_) => write!(f, "Invalid integer value."),
        }
    }
}

impl From<ParseIntError> for Error {
    fn from(err: ParseIntError) -> Error {
        Error::ParseInt(err)
    }
}

pub type Result<T> = std::result::Result<T, Error>;
