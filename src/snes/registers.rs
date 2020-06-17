use crate::snes::state::StateRegister;

#[derive(Copy, Clone)]
struct Register {
    state: StateRegister,
    is_accumulator: bool,
    lo: Option<u16>,
    hi: Option<u16>,
}

impl Register {
    pub fn new(state: StateRegister, is_accumulator: bool) -> Self {
        Self {
            state,
            is_accumulator,
            lo: None,
            hi: None,
        }
    }

    pub fn size(&self) -> usize {
        if self.is_accumulator {
            self.state.a_size()
        } else {
            self.state.x_size()
        }
    }

    pub fn get(&self) -> Option<u16> {
        match self.size() {
            1 => self.lo,
            _ => self.get_whole(),
        }
    }

    pub fn get_whole(&self) -> Option<u16> {
        if self.lo.is_none() || self.hi.is_none() {
            None
        } else {
            let (hi, lo) = (self.hi.unwrap(), self.lo.unwrap());
            Some((hi << 8) | lo)
        }
    }

    pub fn set(&mut self, value: Option<u16>) {
        match value {
            Some(v) => {
                self.lo = Some(v & 0xFF);
                if self.size() > 1 {
                    self.hi = Some((v >> 8) & 0xFF);
                }
            }
            None => match self.size() {
                1 => self.lo = None,
                _ => {
                    self.lo = None;
                    self.hi = None;
                }
            },
        }
    }

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

#[derive(Copy, Clone)]
pub struct Registers {
    state: StateRegister,
    a: Register,
    x: Register,
    y: Register,
}

impl Registers {
    pub fn new(state: StateRegister) -> Self {
        Self {
            state,
            a: Register::new(state, true),
            x: Register::new(state, false),
            y: Register::new(state, false),
        }
    }
}
