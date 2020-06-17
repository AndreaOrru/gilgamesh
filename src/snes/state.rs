use getset::CopyGetters;

const M_BIT: usize = 5;
const X_BIT: usize = 4;

/// SNES state register (P).
#[derive(Copy, Clone, CopyGetters, Debug, Eq, PartialEq, Hash)]
pub struct StateRegister {
    #[getset(get_copy = "pub")]
    p: u8,
}

impl StateRegister {
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
mod test_state_register {
    use super::*;

    #[test]
    fn test_from_mx() {
        let state = StateRegister::from_mx(true, false);
        assert!(state.m());
        assert!(!state.x());
    }

    #[test]
    fn test_size_ax() {
        let mut state = StateRegister::from_mx(true, true);
        assert_eq!(state.a_size(), 1);
        assert_eq!(state.x_size(), 1);

        state.reset(0b0011_0000);
        assert_eq!(state.a_size(), 2);
        assert_eq!(state.x_size(), 2);
    }

    #[test]
    fn test_set() {
        let mut state = StateRegister::new(0b0000_0000);

        state.set(0b0000_0000);
        assert_eq!(state.p(), 0b0000_0000);

        state.set(0b1111_1111);
        assert_eq!(state.p(), 0b0011_0000);
    }

    #[test]
    fn test_reset() {
        let mut state = StateRegister::new(0b1111_1111);

        state.reset(0b0000_0000);
        assert_eq!(state.p(), 0b1111_1111);

        state.reset(0b1111_1111);
        assert_eq!(state.p(), 0b1100_1111);
    }

    #[test]
    fn test_set_reset_mx() {
        let mut state = StateRegister::new(0b0000_0000);

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
#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash)]
pub enum UnknownReason {
    Known,
    Unknown,
    IndirectJump,
    SuspectInstruction,
}

/// State change caused by the execution of a subroutine.
#[derive(Copy, CopyGetters, Clone, Debug, Eq, PartialEq, Hash)]
pub struct SubStateChange {
    #[getset(get_copy = "pub")]
    m: Option<bool>,

    #[getset(get_copy = "pub")]
    x: Option<bool>,

    #[getset(get_copy = "pub")]
    unknown_reason: UnknownReason,
}

impl SubStateChange {
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
        let change = StateRegister::new(p_change);
        self.m = if change.m() { Some(true) } else { self.m };
        self.x = if change.x() { Some(true) } else { self.x };
    }

    /// Set bits changed to 0 in P.
    pub fn reset(&mut self, p_change: u8) {
        let change = StateRegister::new(p_change);
        self.m = if change.m() { Some(false) } else { self.m };
        self.x = if change.x() { Some(false) } else { self.x };
    }
}

#[cfg(test)]
mod test_sub_state_change {
    use super::*;

    #[test]
    fn test_set() {
        let mut state_change = SubStateChange::new_empty();
        state_change.set(0b0011_0000);

        assert!(state_change.m.unwrap());
        assert!(state_change.x.unwrap());
    }

    #[test]
    fn test_reset() {
        let mut state_change = SubStateChange::new_empty();
        state_change.reset(0b0011_0000);

        assert!(!state_change.m.unwrap());
        assert!(!state_change.x.unwrap());
    }
}
