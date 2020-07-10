use std::collections::HashSet;
use std::rc::Rc;

use maplit::hashset;

use crate::analysis::Analysis;
use crate::snes::instruction::{Instruction, InstructionType};
use crate::snes::opcodes::{AddressMode, Op};
use crate::snes::register::Register;
use crate::snes::rom::ROM;
use crate::snes::stack;
use crate::snes::state::{State, StateChange, UnknownReason};

/// SNES CPU emulation.
#[allow(non_snake_case)]
#[derive(Clone)]
pub struct CPU {
    /// Reference to the analysis.
    analysis: Rc<Analysis>,

    /// Whether we should stop emulating after the current instruction.
    stop: bool,

    /// Program Counter.
    pc: usize,

    /// Subroutine currently being executed.
    subroutine: usize,

    /// Processor state.
    state: State,

    /// Processor state change caused by the execution of this subroutine.
    state_change: StateChange,

    /// What we know about the CPU state based on the
    /// sequence of instructions we have executed.
    state_inference: StateChange,

    /// Stack.
    stack: stack::Stack,

    /// Registers.
    A: Register,
}

impl CPU {
    /// Instantiate a CPU object.
    pub fn new(analysis: &Rc<Analysis>, pc: usize, subroutine: usize, p: u8) -> Self {
        Self {
            analysis: analysis.clone(),
            stop: false,
            pc,
            subroutine,
            state: State::new(p),
            state_change: StateChange::new_empty(),
            state_inference: StateChange::new_empty(),
            stack: stack::Stack::new(),
            A: Register::new(true),
        }
    }

    /// Start emulating.
    pub fn run(&mut self) {
        while !self.stop {
            self.step();
        }
    }

    /// Fetch and execute the next instruction.
    fn step(&mut self) {
        // Stop if we have jumped into RAM.
        if ROM::is_ram(self.pc) {
            return self.stop = true;
        }

        let opcode = self.analysis.rom.read_byte(self.pc);
        let argument = self.analysis.rom.read_address(self.pc + 1);
        let instruction = Instruction::new(
            self.pc,
            self.subroutine,
            self.state.p(),
            opcode,
            argument,
            self.state_change,
        );

        // Stop the analysis if we have already visited this instruction.
        if self.analysis.is_visited(instruction) {
            self.stop = true;
        } else {
            self.analysis.add_instruction(instruction);
            self.execute(instruction);
        }
    }

    /// Emulate an instruction.
    fn execute(&mut self, instruction: Instruction) {
        self.pc += instruction.size();

        // See if we can learn something about the *required*
        // state of the CPU based on the current instruction.
        self.derive_state_inference(instruction);

        match instruction.typ() {
            InstructionType::Branch => self.branch(instruction),
            InstructionType::Call => self.call(instruction),
            InstructionType::Interrupt => self.interrupt(instruction),
            InstructionType::Jump => self.jump(instruction),
            InstructionType::Return => self.ret(instruction),
            InstructionType::SepRep => self.sep_rep(instruction),
            InstructionType::Pop => self.pop(instruction),
            InstructionType::Push => self.push(instruction),
            _ if instruction.changes_a() => self.change_a(instruction),
            _ if instruction.changes_stack() => self.change_stack(instruction),
            _ => {}
        }
    }

    /// Branch instruction emulation.
    fn branch(&mut self, instruction: Instruction) {
        // Run a parallel instance of the CPU to cover
        // the case in which the branch is not taken.
        let mut cpu = self.clone();
        cpu.run();

        // Log the fact that the current instruction references the
        // instruction pointed by the branch. Then take the branch.
        let target = instruction.absolute_argument().unwrap();
        self.analysis
            .add_reference(instruction.pc(), target, self.subroutine);
        self.pc = target;
    }

    /// Call instruction emulation.
    fn call(&mut self, instruction: Instruction) {
        match self.jump_targets(instruction) {
            Some(targets) => {
                for target in targets.iter().copied() {
                    // Create a parallel instance of the CPU to
                    // execute the subroutine that is being called.
                    let mut cpu = self.clone();
                    cpu.state_change = StateChange::new_empty();
                    cpu.subroutine = target;
                    cpu.pc = target;

                    // Emulate the called subroutine.
                    self.analysis.add_subroutine(target, None);
                    self.analysis
                        .add_reference(instruction.pc(), target, self.subroutine);
                    cpu.run();
                }
                // Propagate called subroutines state to caller.
                self.propagate_subroutine_state(instruction.pc(), targets);
            }
            None => self.unknown_state_change(instruction.pc(), UnknownReason::IndirectJump),
        }
    }

    /// Emulate instructions that modify the value of A.
    fn change_a(&mut self, i: Instruction) {
        #[allow(non_snake_case)]
        let A = &mut self.A;
        let s = self.state;

        match i.address_mode() {
            AddressMode::ImmediateM => {
                let a = A.get(s);
                let arg = i.argument().unwrap() as u16;
                match i.operation() {
                    Op::LDA => A.set(s, Some(arg)),
                    Op::ADC if a.is_some() => A.set(s, Some(a.unwrap() + arg)),
                    Op::SBC if a.is_some() => A.set(s, Some(a.unwrap() - arg)),
                    _ => A.set(s, None),
                }
            }
            _ => {
                match i.operation() {
                    Op::TSC => A.set_whole(Some(self.stack.pointer() as u16)),
                    Op::PLA => {
                        // TODO: assign value to A.
                        self.stack.pop(self.state.a_size());
                    }
                    _ => A.set(s, None),
                }
            }
        }
    }

    /// Emulate instructions that modify the stack pointer.
    fn change_stack(&mut self, i: Instruction) {
        match i.operation() {
            Op::TCS => match self.A.get_whole() {
                Some(a) => self.stack.set_pointer(i, a),
                None => self.unknown_state_change(i.pc(), UnknownReason::StackManipulation),
            },
            _ => {}
        }
    }

    /// Interrupt instruction emulation.
    fn interrupt(&mut self, i: Instruction) {
        self.unknown_state_change(i.pc(), UnknownReason::SuspectInstruction);
    }

    /// Jump instruction emulation.
    fn jump(&mut self, instruction: Instruction) {
        match self.jump_targets(instruction) {
            Some(targets) => {
                // Execute each target in a CPU instance.
                for target in targets.iter().copied() {
                    self.analysis
                        .add_reference(instruction.pc(), target, self.subroutine);
                    let mut cpu = self.clone();
                    cpu.pc = target;
                    cpu.run();
                }
                // Targets have already been executed - stop here.
                self.stop = true;
            }
            None => self.unknown_state_change(instruction.pc(), UnknownReason::IndirectJump),
        }
    }

    /// Return instruction emulation.
    fn ret(&mut self, i: Instruction) {
        self.stop = true;
        self.analysis
            .add_state_change(self.subroutine, i.pc(), self.state_change);
    }

    /// SEP/REP instruction emulation.
    fn sep_rep(&mut self, instruction: Instruction) {
        let arg = instruction.absolute_argument().unwrap();
        match instruction.operation() {
            Op::SEP => {
                self.state.set(arg as u8);
                self.state_change.set(arg as u8);
            }
            Op::REP => {
                self.state.reset(arg as u8);
                self.state_change.reset(arg as u8);
            }
            _ => unreachable!(),
        }
        // Simplify the state change by applying our knowledge
        // of the current state. I.e. if we know that the
        // processor is operating in 8-bits accumulator mode
        // and we switch to that same mode, effectively no
        // state change is being performed.
        self.state_change.apply_inference(self.state_inference)
    }

    /// Push a value onto the stack.
    fn push(&mut self, instruction: Instruction) {
        match instruction.operation() {
            Op::PHP => self.stack.push_one(
                instruction,
                stack::Data::State(self.state, self.state_change),
            ),
            // TODO: emulate other push instructions.
            _ => {}
        }
    }

    /// Pop a value from the stack.
    fn pop(&mut self, instruction: Instruction) {
        match instruction.operation() {
            Op::PLP => {
                let entry = self.stack.pop_one();
                match entry.instruction {
                    // Regular state restore.
                    Some(i) if i.operation() == Op::PHP => match entry.data {
                        stack::Data::State(state, state_change) => {
                            self.state = state;
                            self.state_change = state_change;
                        }
                        _ => unreachable!(),
                    },
                    // Stack manipulation. Stop here.
                    _ => {
                        self.unknown_state_change(
                            instruction.pc(),
                            UnknownReason::StackManipulation,
                        );
                        self.stop = true;
                    }
                }
            }
            // TODO: emulate other pop instructions.
            _ => {}
        }
    }

    /// Take the state change of the given subroutines and
    /// propagate it to to the current subroutine state.
    fn propagate_subroutine_state(&mut self, call_pc: usize, targets: HashSet<usize>) {
        let subroutines = self.analysis.subroutines().borrow();
        let mut state_changes = HashSet::<StateChange>::new();

        // Iterate through all the called subroutines.
        for target in targets.iter().copied() {
            let sub = &subroutines[&target];

            // Unknown state change.
            if sub.has_unknown_state_change() {
                drop(subroutines);
                return self.unknown_state_change(call_pc, UnknownReason::Unknown);
            } else {
                state_changes.extend(sub.simplified_state_changes(self.state));
            }
        }

        // Ambiguous states.
        if state_changes.len() != 1 {
            // TODO: simplify all the state changes.
            drop(subroutines);
            return self.unknown_state_change(call_pc, UnknownReason::MultipleReturnStates);
        }

        // Single, valid state change that we can propagate.
        let state_change = *state_changes.iter().next().unwrap();
        Self::apply_state_change(&mut self.state, &mut self.state_change, state_change);
    }

    /// Signal an unknown subroutine state change.
    fn unknown_state_change(&mut self, pc: usize, reason: UnknownReason) {
        match self.analysis.instruction_assertion(pc) {
            // Instruction assertion?
            Some(state_change) => {
                Self::apply_state_change(&mut self.state, &mut self.state_change, state_change);
            }
            None => {
                // Subroutine assertion?
                let state_change = match self.analysis.subroutine_assertion(self.subroutine, pc) {
                    Some(state_change) => state_change,
                    None => StateChange::new_unknown(reason),
                };
                // Unknown state.
                self.analysis
                    .add_state_change(self.subroutine, pc, state_change);
                self.stop = true;
            }
        }
    }

    /// Apply a state change to the current CPU instance.
    fn apply_state_change(
        state: &mut State,
        state_change: &mut StateChange,
        new_state_change: StateChange,
    ) {
        if let Some(m) = new_state_change.m() {
            state.set_m(m);
            state_change.set_m(m);
        }
        if let Some(x) = new_state_change.x() {
            state.set_x(x);
            state_change.set_x(x);
        }
    }

    /// Derive a state inference from the current state and given instruction.
    fn derive_state_inference(&mut self, instruction: Instruction) {
        // If we're executing an instruction with a certain operand size,
        // and no state change has been performed in the current subroutine,
        // then we can infer that the state of the processor as we enter
        // the subroutine *must* be the same in all cases.
        match instruction.address_mode() {
            AddressMode::ImmediateM if self.state_change.m().is_none() => {
                self.state_inference.set_m(self.state.m());
            }
            AddressMode::ImmediateX if self.state_change.x().is_none() => {}
            _ => {
                self.state_inference.set_x(self.state.x());
            }
        }
    }

    /// Given a jump or call instruction, return its target(s), if any.
    fn jump_targets(&self, instruction: Instruction) -> Option<HashSet<usize>> {
        let jump_assertions = self.analysis.jump_assertions().borrow();
        match instruction.absolute_argument() {
            Some(target) => Some(hashset! { target }),
            None => jump_assertions
                .get(&instruction.pc())
                .map(|h| h.iter().map(|j| j.target).collect()),
        }
    }

    #[cfg(test)]
    fn setup_instruction(&self, opcode: u8, argument: usize) -> Instruction {
        Instruction::test(self.pc, self.subroutine, self.state.p(), opcode, argument)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::analysis::Reference;

    fn setup_cpu(p: u8) -> CPU {
        let analysis = Analysis::new(ROM::new());
        analysis.add_subroutine(0x8000, None);
        CPU::new(&analysis, 0x8000, 0x8000, p)
    }

    #[test]
    fn test_branch() {
        let mut cpu = setup_cpu(0b0000_0000);
        cpu.stop = true;

        let bcc = cpu.setup_instruction(0x90, 0x10);
        cpu.execute(bcc);
        assert_eq!(cpu.pc, 0x8012);
    }

    #[test]
    fn test_call() {
        let mut cpu = setup_cpu(0b0000_0000);
        cpu.stop = true;

        let jsr = cpu.setup_instruction(0x20, 0x9000);
        cpu.execute(jsr);

        assert_eq!(cpu.pc, 0x8003);
        assert!(cpu.analysis.is_subroutine(0x9000));
    }

    #[test]
    fn test_interrupt() {
        let mut cpu = setup_cpu(0b0000_0000);
        let brk = cpu.setup_instruction(0x00, 0x00);
        cpu.execute(brk);
        assert!(cpu.stop);
    }

    #[test]
    fn test_jump() {
        let mut cpu = setup_cpu(0b0000_0000);
        cpu.stop = true;

        let jmp = cpu.setup_instruction(0x4C, 0x9000);
        cpu.execute(jmp);

        let references = cpu.analysis.references().borrow();
        assert!(references[&0x8000].contains(&Reference {
            target: 0x9000,
            subroutine: 0x8000
        }));
    }

    #[test]
    fn test_ret() {
        let mut cpu = setup_cpu(0b0000_0000);
        let rts = cpu.setup_instruction(0x60, 0x00);
        cpu.execute(rts);
        assert!(cpu.stop);

        let mut cpu = setup_cpu(0b0000_0000);
        let rtl = cpu.setup_instruction(0x6B, 0x00);
        cpu.execute(rtl);
        assert!(cpu.stop);
    }

    #[test]
    fn test_sep_rep() {
        let mut cpu = setup_cpu(0b0000_0000);

        let sep = cpu.setup_instruction(0xE2, 0x30);
        cpu.execute(sep);
        assert_eq!(cpu.pc, sep.pc() + 2);
        assert_eq!(cpu.state.p(), 0b0011_0000);

        let rep = cpu.setup_instruction(0xC2, 0x30);
        cpu.execute(rep);
        assert_eq!(cpu.pc, rep.pc() + 2);
        assert_eq!(cpu.state.p(), 0b0000_0000);
    }
}
