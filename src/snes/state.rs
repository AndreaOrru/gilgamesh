use getset::CopyGetters;

const M_BIT: usize = 5;
const X_BIT: usize = 4;

/// SNES state register (P).
#[derive(CopyGetters, Eq, PartialEq, Hash)]
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
