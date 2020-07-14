use std::fmt;

use getset::CopyGetters;
use serde::{Deserialize, Serialize};
use strum_macros::IntoStaticStr;

use crate::prompt::error::{Error, Result};

const M_BIT: usize = 5;
const X_BIT: usize = 4;

/// SNES state register (P).
#[derive(Copy, Clone, CopyGetters, Debug, Eq, Hash, PartialEq)]
pub struct State {
    #[getset(get_copy = "pub")]
    p: u8,
}

impl State {
    /// Instantiate state register from the value of P.
    pub fn new(p: u8) -> Self {
        Self { p }
    }

    /// Instantiate a P state from M/X values.
    pub fn from_mx(m: bool, x: bool) -> Self {
        let m = if m { 1 } else { 0 };
        let x = if x { 1 } else { 0 };
        Self {
            p: (m << M_BIT) | (x << X_BIT),
        }
    }

    /// Instantiate a state object from a human-readable expression.
    pub fn from_expr(expr: String) -> Result<Self> {
        let expressions: Vec<&str> = expr.split(',').collect();
        if expressions.len() != 2 {
            return Err(Error::InvalidStateExpr);
        }

        let (mut m, mut x) = (false, false);
        for expression in expressions.iter() {
            let parts: Vec<&str> = expression.split('=').collect();
            let (register, value) = (parts[0], parts[1]);
            match register {
                "m" => m = value.parse::<u8>()? != 0,
                "x" => x = value.parse::<u8>()? != 0,
                _ => return Err(Error::InvalidStateExpr),
            }
        }
        Ok(Self::from_mx(m, x))
    }

    /// Return the value of M.
    pub fn m(&self) -> bool {
        (self.p & (1 << M_BIT)) != 0
    }

    /// Return the value of X.
    pub fn x(&self) -> bool {
        (self.p & (1 << X_BIT)) != 0
    }

    /// Set the value of M.
    pub fn set_m(&mut self, m: bool) {
        if m {
            self.set(1 << M_BIT);
        } else {
            self.reset(1 << M_BIT);
        }
    }

    /// Set the value of X.
    pub fn set_x(&mut self, x: bool) {
        if x {
            self.set(1 << X_BIT);
        } else {
            self.reset(1 << X_BIT);
        }
    }

    /// Set bits in the state register.
    pub fn set(&mut self, mut p: u8) {
        p &= (1 << M_BIT) | (1 << X_BIT);
        self.p |= p;
    }

    /// Reset bits in the state register.
    pub fn reset(&mut self, mut p: u8) {
        p &= (1 << M_BIT) | (1 << X_BIT);
        self.p &= !p;
    }

    /// Return the size of the accumulator.
    pub fn a_size(&self) -> usize {
        if self.m() {
            1
        } else {
            2
        }
    }

    /// Return the size of the index registers.
    pub fn x_size(&self) -> usize {
        if self.x() {
            1
        } else {
            2
        }
    }
}

#[cfg(test)]
mod test_state {
    use super::*;

    #[test]
    fn test_from_mx() {
        let state = State::from_mx(true, false);
        assert!(state.m());
        assert!(!state.x());
    }

    #[test]
    fn test_from_expr() {
        let state = State::from_expr("m=0,x=1".to_string()).unwrap();
        assert_eq!(state.m(), false);
        assert_eq!(state.x(), true);

        let state = State::from_expr("x=0,m=1".to_string()).unwrap();
        assert_eq!(state.m(), true);
        assert_eq!(state.x(), false);
    }

    #[test]
    fn test_size_ax() {
        let mut state = State::from_mx(true, true);
        assert_eq!(state.a_size(), 1);
        assert_eq!(state.x_size(), 1);

        state.reset(0b0011_0000);
        assert_eq!(state.a_size(), 2);
        assert_eq!(state.x_size(), 2);
    }

    #[test]
    fn test_set() {
        let mut state = State::new(0b0000_0000);

        state.set(0b0000_0000);
        assert_eq!(state.p(), 0b0000_0000);

        state.set(0b1111_1111);
        assert_eq!(state.p(), 0b0011_0000);
    }

    #[test]
    fn test_reset() {
        let mut state = State::new(0b1111_1111);

        state.reset(0b0000_0000);
        assert_eq!(state.p(), 0b1111_1111);

        state.reset(0b1111_1111);
        assert_eq!(state.p(), 0b1100_1111);
    }

    #[test]
    fn test_set_reset_mx() {
        let mut state = State::new(0b0000_0000);

        state.set_m(true);
        state.set_x(true);
        assert!(state.m());
        assert!(state.x());

        state.set_m(false);
        state.set_x(false);
        assert!(!state.m());
        assert!(!state.x());
    }
}

/// Possible reasons why a state change is unknown.
#[derive(Copy, Clone, Debug, Deserialize, Eq, Hash, IntoStaticStr, PartialEq, Serialize)]
pub enum UnknownReason {
    Known,
    Unknown,
    IndirectJump,
    MultipleReturnStates,
    StackManipulation,
    SuspectInstruction,
}

/// State change caused by the execution of a subroutine.
#[derive(Copy, CopyGetters, Clone, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
pub struct StateChange {
    #[getset(get_copy = "pub")]
    m: Option<bool>,

    #[getset(get_copy = "pub")]
    x: Option<bool>,

    #[getset(get_copy = "pub")]
    unknown_reason: UnknownReason,
}

impl StateChange {
    /// Instantiate a new subroutine state change.
    pub fn new(m: Option<bool>, x: Option<bool>) -> Self {
        Self {
            m,
            x,
            unknown_reason: UnknownReason::Known,
        }
    }

    /// Instantiate an empty state change (no changes).
    pub fn new_empty() -> Self {
        Self {
            m: None,
            x: None,
            unknown_reason: UnknownReason::Known,
        }
    }

    /// Instantiate an unknown state change.
    pub fn new_unknown(reason: UnknownReason) -> Self {
        Self {
            m: None,
            x: None,
            unknown_reason: reason,
        }
    }

    /// Instantiate a state change object from a human-readable expression.
    pub fn from_expr(expr: String) -> Result<Self> {
        match expr.as_str() {
            "none" => Ok(Self::new_empty()),
            "unknown" => Ok(Self::new_unknown(UnknownReason::Unknown)),
            _ => {
                let expressions: Vec<&str> = expr.split(',').collect();
                match expressions.len() {
                    1 | 2 => {
                        let mut m = None;
                        let mut x = None;

                        for expression in expressions.iter() {
                            let parts: Vec<&str> = expression.split('=').collect();
                            let (register, value) = (parts[0], parts[1]);
                            match register {
                                "m" => m = Some(value.parse::<u8>()? != 0),
                                "x" => x = Some(value.parse::<u8>()? != 0),
                                _ => return Err(Error::InvalidStateExpr),
                            }
                        }
                        Ok(Self::new(m, x))
                    }
                    _ => Err(Error::InvalidStateExpr),
                }
            }
        }
    }

    /// Return true if the state is unknown, false otherwise.
    pub fn unknown(&self) -> bool {
        self.unknown_reason != UnknownReason::Known
    }

    /// Set a state change for M.
    pub fn set_m(&mut self, m: bool) {
        self.m = Some(m);
    }

    /// Set a state change for X.
    pub fn set_x(&mut self, x: bool) {
        self.x = Some(x);
    }

    /// Set bits changed to 1 in P.
    pub fn set(&mut self, p_change: u8) {
        let change = State::new(p_change);
        self.m = if change.m() { Some(true) } else { self.m };
        self.x = if change.x() { Some(true) } else { self.x };
    }

    /// Set bits changed to 0 in P.
    pub fn reset(&mut self, p_change: u8) {
        let change = State::new(p_change);
        self.m = if change.m() { Some(false) } else { self.m };
        self.x = if change.x() { Some(false) } else { self.x };
    }

    /// Simplify the state change based on a state inference.
    pub fn apply_inference(&mut self, inference: StateChange) {
        // If we already knew that M was set, and we're currently
        // setting M, then we are not really changing its value.
        if self.m.is_some() && (self.m == inference.m) {
            self.m = None;
        }
        if self.x.is_some() && (self.x == inference.x) {
            self.x = None;
        }
    }

    /// Simplify the state change based on a state.
    pub fn simplify(&self, state: State) -> StateChange {
        let mut change = self.clone();
        if change.m.is_some() && (state.m() == change.m.unwrap()) {
            change.m = None;
        }
        if change.x.is_some() && (state.x() == change.x.unwrap()) {
            change.x = None;
        }
        change
    }
}

/// Display a state change in human-readable form.
impl fmt::Display for StateChange {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        if self.unknown() {
            write!(f, "unknown")
        } else {
            let m = match self.m {
                Some(m) => vec![format!("m={}", m as u8)],
                None => vec![],
            };
            let x = match self.x {
                Some(x) => vec![format!("x={}", x as u8)],
                None => vec![],
            };
            let mx = [&m[..], &x[..]].concat();

            if m.is_empty() && x.is_empty() {
                write!(f, "none")
            } else {
                write!(f, "{}", mx.join(","))
            }
        }
    }
}

#[cfg(test)]
mod test_state_change {
    use super::*;

    #[test]
    fn test_set() {
        let mut state_change = StateChange::new_empty();
        state_change.set(0b0011_0000);

        assert!(state_change.m.unwrap());
        assert!(state_change.x.unwrap());
    }

    #[test]
    fn test_reset() {
        let mut state_change = StateChange::new_empty();
        state_change.reset(0b0011_0000);

        assert!(!state_change.m.unwrap());
        assert!(!state_change.x.unwrap());
    }

    #[test]
    fn test_display() {
        let unknown = StateChange::new_unknown(UnknownReason::Unknown);
        assert_eq!(unknown.to_string(), "unknown");

        let m = StateChange::new(Some(true), None);
        assert_eq!(m.to_string(), "m=1");

        let x = StateChange::new(None, Some(false));
        assert_eq!(x.to_string(), "x=0");

        let mx = StateChange::new(Some(false), Some(true));
        assert_eq!(mx.to_string(), "m=0,x=1");
    }

    #[test]
    fn test_from_expr() {
        let unknown = StateChange::from_expr("unknown".to_string()).unwrap();
        assert!(unknown.unknown());

        let none = StateChange::from_expr("none".to_string()).unwrap();
        assert_eq!(none.to_string(), "none");

        let m = StateChange::from_expr("m=1".to_string()).unwrap();
        assert_eq!(m.m(), Some(true));

        let mx = StateChange::from_expr("m=1,x=0".to_string()).unwrap();
        assert_eq!(mx.m(), Some(true));
        assert_eq!(mx.x(), Some(false));
    }

    #[test]
    fn test_apply_inference() {
        let mut mx = StateChange::new(Some(true), Some(false));
        let inference = StateChange::new(Some(true), Some(false));
        mx.apply_inference(inference);

        assert!(mx.m.is_none());
        assert!(mx.x.is_none());
    }
}
