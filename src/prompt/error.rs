use std::error;
use std::fmt;
use std::io;
use std::num::ParseIntError;

/// Gilgamesh error type.
#[derive(Debug)]
pub enum Error {
    AlreadyAnalyzed,
    InvalidLabel(String),
    InvalidLabelType,
    InvalidStateExpr,
    InvalidStepSize,
    IOError(io::Error),
    LabelAlreadyUsed(String),
    MissingArg(String),
    NoSelectedSubroutine,
    ParseInt(ParseIntError),
    ReservedLabel(String),
    UnknownLabel(String),
}

impl error::Error for Error {}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Error::AlreadyAnalyzed => write!(f, "Address has already been analyzed."),
            Error::InvalidLabel(l) => write!(f, "Invalid label \"{}\".", l),
            Error::InvalidLabelType => write!(f, "Invalid label type."),
            Error::InvalidStateExpr => write!(f, "Invalid state expression."),
            Error::InvalidStepSize => write!(f, "Can only build groups up to 16 bytes."),
            Error::IOError(_) => write!(f, "Error opening file."),
            Error::LabelAlreadyUsed(l) => write!(f, "Label already in use \"{}\".", l),
            Error::MissingArg(s) => write!(f, "Missing argument {}.", s),
            Error::NoSelectedSubroutine => write!(f, "No selected subroutine."),
            Error::ParseInt(_) => write!(f, "Invalid integer value."),
            Error::ReservedLabel(l) => write!(f, "Reserved label \"{}\".", l),
            Error::UnknownLabel(l) => write!(f, "Unknown label \"{}\".", l),
        }
    }
}

impl From<ParseIntError> for Error {
    fn from(err: ParseIntError) -> Error {
        Error::ParseInt(err)
    }
}

impl From<io::Error> for Error {
    fn from(err: io::Error) -> Error {
        Error::IOError(err)
    }
}

pub type Result<T> = std::result::Result<T, Error>;
