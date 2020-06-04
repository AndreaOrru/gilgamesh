pub struct CPU {
    analysis: &Analysis,

    pc: usize,
    subroutine: usize,

    state_register: StateRegister,
}
