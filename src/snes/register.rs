use crate::snes::state::StateRegister;

/// 8/16-bit SNES register.
#[derive(Copy, Clone)]
pub struct Register {
    is_accumulator: bool,
    lo: Option<u16>,
    hi: Option<u16>,
}

impl Register {
    /// Instantiate a Register object.
    pub fn new(is_accumulator: bool) -> Self {
        Self {
            is_accumulator,
            lo: None,
            hi: None,
        }
    }

    /// Return the size of the register in the given state.
    pub fn size(&self, state: StateRegister) -> usize {
        if self.is_accumulator {
            state.a_size()
        } else {
            state.x_size()
        }
    }

    /// Get the value of the register in the given state.
    pub fn get(&self, state: StateRegister) -> Option<u16> {
        match self.size(state) {
            1 => self.lo,
            _ => self.get_whole(),
        }
    }

    /// Get the 16-bit value of the register.
    pub fn get_whole(&self) -> Option<u16> {
        if self.lo.is_none() || self.hi.is_none() {
            None
        } else {
            let (hi, lo) = (self.hi.unwrap(), self.lo.unwrap());
            Some((hi << 8) | lo)
        }
    }

    /// Set the value of the register in the given state.
    pub fn set(&mut self, state: StateRegister, value: Option<u16>) {
        match value {
            Some(v) => {
                self.lo = Some(v & 0xFF);
                if self.size(state) > 1 {
                    self.hi = Some((v >> 8) & 0xFF);
                }
            }
            None => match self.size(state) {
                1 => self.lo = None,
                _ => {
                    self.lo = None;
                    self.hi = None;
                }
            },
        }
    }

    /// Set the 16-bit value of the register.
    pub fn set_whole(&mut self, value: Option<u16>) {
        match value {
            Some(v) => {
                self.lo = Some(v & 0xFF);
                self.hi = Some((v >> 8) & 0xFF);
            }
            None => {
                self.lo = None;
                self.hi = None;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_size() {
        let mut state = StateRegister::from_mx(true, true);
        let a = Register::new(true);
        let x = Register::new(false);

        assert_eq!(a.size(state), 1);
        assert_eq!(x.size(state), 1);

        state.set_m(false);
        assert_eq!(a.size(state), 2);

        state.set_x(false);
        assert_eq!(x.size(state), 2);
    }

    #[test]
    fn test_get_set() {
        let mut state = StateRegister::from_mx(true, true);
        let mut a = Register::new(true);

        // Only lower 8-bits known.
        a.set(state, Some(0xFF));
        assert_eq!(a.get(state).unwrap(), 0xFF);
        // 16-bits unknown.
        state.set_m(false);
        assert!(a.get(state).is_none());

        // 16-bits known.
        a.set(state, Some(0xFFFF));
        assert_eq!(a.get(state).unwrap(), 0xFFFF);
        // 8-bits known.
        state.set_m(true);
        assert_eq!(a.get(state).unwrap(), 0xFF);

        // 16-bits unknown.
        state.set_m(false);
        a.set(state, None);
        assert!(a.get(state).is_none());
        // 8-bits unknown.
        state.set_m(true);
        assert!(a.get(state).is_none());
    }

    #[test]
    fn test_get_set_whole() {
        let mut state = StateRegister::from_mx(true, true);
        let mut a = Register::new(true);

        a.set_whole(Some(0xFFFF));
        assert_eq!(a.get(state).unwrap(), 0xFF);
        assert_eq!(a.get_whole().unwrap(), 0xFFFF);

        state.set_m(false);
        assert_eq!(a.get(state).unwrap(), 0xFFFF);
    }
}
