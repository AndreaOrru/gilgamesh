from enum import Enum, IntEnum
from typing import List, Tuple


class AddressMode(IntEnum):
    IMPLIED = 0
    IMMEDIATE_M = 1
    IMMEDIATE_X = 2
    IMMEDIATE_8 = 3
    RELATIVE = 4
    RELATIVE_LONG = 5
    DIRECT_PAGE = 6
    DIRECT_PAGE_INDEXED_X = 7
    DIRECT_PAGE_INDEXED_Y = 8
    DIRECT_PAGE_INDIRECT = 9
    DIRECT_PAGE_INDEXED_INDIRECT = 10
    DIRECT_PAGE_INDIRECT_INDEXED = 11
    DIRECT_PAGE_INDIRECT_LONG = 12
    DIRECT_PAGE_INDIRECT_INDEXED_LONG = 13
    ABSOLUTE = 14
    ABSOLUTE_INDEXED_X = 15
    ABSOLUTE_INDEXED_Y = 16
    ABSOLUTE_LONG = 17
    ABSOLUTE_INDEXED_LONG = 18
    STACK_RELATIVE = 19
    STACK_RELATIVE_INDIRECT_INDEXED = 20
    ABSOLUTE_INDIRECT = 21
    ABSOLUTE_INDIRECT_LONG = 22
    ABSOLUTE_INDEXED_INDIRECT = 23
    IMPLIED_ACCUMULATOR = 24
    MOVE = 25
    STACK_ABSOLUTE = 26
    PEI_DIRECT_PAGE_INDIRECT = 27


argument_size_table = [
    0,  # IMPLIED
    None,  # IMMEDIATE_M
    None,  # IMMEDIATE_X
    1,  # IMMEDIATE_8
    1,  # RELATIVE
    2,  # RELATIVE_LONG
    1,  # DIRECT_PAGE
    1,  # DIRECT_PAGE_INDEXED_X
    1,  # DIRECT_PAGE_INDEXED_Y
    1,  # DIRECT_PAGE_INDIRECT
    1,  # DIRECT_PAGE_INDEXED_INDIRECT
    1,  # DIRECT_PAGE_INDIRECT_INDEXED
    1,  # DIRECT_PAGE_INDIRECT_LONG
    1,  # DIRECT_PAGE_INDIRECT_INDEXED_LONG
    2,  # ABSOLUTE
    2,  # ABSOLUTE_INDEXED_X
    2,  # ABSOLUTE_INDEXED_Y
    3,  # ABSOLUTE_LONG
    3,  # ABSOLUTE_INDEXED_LONG
    1,  # STACK_RELATIVE
    1,  # STACK_RELATIVE_INDIRECT_INDEXED
    2,  # ABSOLUTE_INDIRECT
    2,  # ABSOLUTE_INDIRECT_LONG
    2,  # ABSOLUTE_INDEXED_INDIRECT
    0,  # IMPLIED_ACCUMULATOR
    2,  # MOVE
    2,  # STACK_ABSOLUTE
    1,  # PEI_DIRECT_PAGE_INDIRECT
]


class Op(Enum):
    ADC = 0
    AND = 1
    ASL = 2
    BCC = 3
    BCS = 4
    BEQ = 5
    BIT = 6
    BMI = 7
    BNE = 8
    BPL = 9
    BRA = 10
    BRK = 11
    BRL = 12
    BVC = 13
    BVS = 14
    CLC = 15
    CLD = 16
    CLI = 17
    CLV = 18
    CMP = 19
    COP = 20
    CPX = 21
    CPY = 22
    DEC = 23
    DEX = 24
    DEY = 25
    EOR = 26
    INC = 27
    INX = 28
    INY = 29
    JML = 30
    JMP = 31
    JSL = 32
    JSR = 33
    LDA = 34
    LDX = 35
    LDY = 36
    LSR = 37
    MVN = 38
    MVP = 39
    NOP = 40
    ORA = 41
    PEA = 42
    PEI = 43
    PER = 44
    PHA = 45
    PHB = 46
    PHD = 47
    PHK = 48
    PHP = 49
    PHX = 50
    PHY = 51
    PLA = 52
    PLB = 53
    PLD = 54
    PLP = 55
    PLX = 56
    PLY = 57
    REP = 58
    ROL = 59
    ROR = 60
    RTI = 61
    RTL = 62
    RTS = 63
    SBC = 64
    SEC = 65
    SED = 66
    SEI = 67
    SEP = 68
    STA = 69
    STP = 70
    STX = 71
    STY = 72
    STZ = 73
    TAX = 74
    TAY = 75
    TCD = 76
    TCS = 77
    TDC = 78
    TRB = 79
    TSB = 80
    TSC = 81
    TSX = 82
    TXA = 83
    TXS = 84
    TXY = 85
    TYA = 86
    TYX = 87
    WAI = 88
    WDM = 89
    XBA = 90
    XCE = 91


opcode_table: List[Tuple[Op, AddressMode]] = [
    (Op.BRK, AddressMode.IMMEDIATE_8),
    (Op.ORA, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.COP, AddressMode.IMMEDIATE_8),
    (Op.ORA, AddressMode.STACK_RELATIVE),
    (Op.TSB, AddressMode.DIRECT_PAGE),
    (Op.ORA, AddressMode.DIRECT_PAGE),
    (Op.ASL, AddressMode.DIRECT_PAGE),
    (Op.ORA, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.PHP, AddressMode.IMPLIED),
    (Op.ORA, AddressMode.IMMEDIATE_M),
    (Op.ASL, AddressMode.IMPLIED_ACCUMULATOR),
    (Op.PHD, AddressMode.IMPLIED),
    (Op.TSB, AddressMode.ABSOLUTE),
    (Op.ORA, AddressMode.ABSOLUTE),
    (Op.ASL, AddressMode.ABSOLUTE),
    (Op.ORA, AddressMode.ABSOLUTE_LONG),
    (Op.BPL, AddressMode.RELATIVE),
    (Op.ORA, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.ORA, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.ORA, AddressMode.STACK_RELATIVE_INDIRECT_INDEXED),
    (Op.TRB, AddressMode.DIRECT_PAGE),
    (Op.ORA, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.ASL, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.ORA, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.CLC, AddressMode.IMPLIED),
    (Op.ORA, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.INC, AddressMode.IMPLIED_ACCUMULATOR),
    (Op.TCS, AddressMode.IMPLIED),
    (Op.TRB, AddressMode.ABSOLUTE),
    (Op.ORA, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.ASL, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.ORA, AddressMode.ABSOLUTE_INDEXED_LONG),
    (Op.JSR, AddressMode.ABSOLUTE),
    (Op.AND, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.JSL, AddressMode.ABSOLUTE_LONG),
    (Op.AND, AddressMode.STACK_RELATIVE),
    (Op.BIT, AddressMode.DIRECT_PAGE),
    (Op.AND, AddressMode.DIRECT_PAGE),
    (Op.ROL, AddressMode.DIRECT_PAGE),
    (Op.AND, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.PLP, AddressMode.IMPLIED),
    (Op.AND, AddressMode.IMMEDIATE_M),
    (Op.ROL, AddressMode.IMPLIED_ACCUMULATOR),
    (Op.PLD, AddressMode.IMPLIED),
    (Op.BIT, AddressMode.ABSOLUTE),
    (Op.AND, AddressMode.ABSOLUTE),
    (Op.ROL, AddressMode.ABSOLUTE),
    (Op.AND, AddressMode.ABSOLUTE_LONG),
    (Op.BMI, AddressMode.RELATIVE),
    (Op.AND, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.AND, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.AND, AddressMode.STACK_RELATIVE_INDIRECT_INDEXED),
    (Op.BIT, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.AND, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.ROL, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.AND, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.SEC, AddressMode.IMPLIED),
    (Op.AND, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.DEC, AddressMode.IMPLIED_ACCUMULATOR),
    (Op.TSC, AddressMode.IMPLIED),
    (Op.BIT, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.AND, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.ROL, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.AND, AddressMode.ABSOLUTE_INDEXED_LONG),
    (Op.RTI, AddressMode.IMPLIED),
    (Op.EOR, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.WDM, AddressMode.IMMEDIATE_8),
    (Op.EOR, AddressMode.STACK_RELATIVE),
    (Op.MVP, AddressMode.MOVE),
    (Op.EOR, AddressMode.DIRECT_PAGE),
    (Op.LSR, AddressMode.DIRECT_PAGE),
    (Op.EOR, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.PHA, AddressMode.IMPLIED),
    (Op.EOR, AddressMode.IMMEDIATE_M),
    (Op.LSR, AddressMode.IMPLIED_ACCUMULATOR),
    (Op.PHK, AddressMode.IMPLIED),
    (Op.JMP, AddressMode.ABSOLUTE),
    (Op.EOR, AddressMode.ABSOLUTE),
    (Op.LSR, AddressMode.ABSOLUTE),
    (Op.EOR, AddressMode.ABSOLUTE_LONG),
    (Op.BVC, AddressMode.RELATIVE),
    (Op.EOR, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.EOR, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.EOR, AddressMode.STACK_RELATIVE_INDIRECT_INDEXED),
    (Op.MVN, AddressMode.MOVE),
    (Op.EOR, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.LSR, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.EOR, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.CLI, AddressMode.IMPLIED),
    (Op.EOR, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.PHY, AddressMode.IMPLIED),
    (Op.TCD, AddressMode.IMPLIED),
    (Op.JML, AddressMode.ABSOLUTE_LONG),
    (Op.EOR, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.LSR, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.EOR, AddressMode.ABSOLUTE_INDEXED_LONG),
    (Op.RTS, AddressMode.IMPLIED),
    (Op.ADC, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.PER, AddressMode.RELATIVE_LONG),
    (Op.ADC, AddressMode.STACK_RELATIVE),
    (Op.STZ, AddressMode.DIRECT_PAGE),
    (Op.ADC, AddressMode.DIRECT_PAGE),
    (Op.ROR, AddressMode.DIRECT_PAGE),
    (Op.ADC, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.PLA, AddressMode.IMPLIED),
    (Op.ADC, AddressMode.IMMEDIATE_M),
    (Op.ROR, AddressMode.IMPLIED_ACCUMULATOR),
    (Op.RTL, AddressMode.IMPLIED),
    (Op.JMP, AddressMode.ABSOLUTE_INDIRECT),
    (Op.ADC, AddressMode.ABSOLUTE),
    (Op.ROR, AddressMode.ABSOLUTE),
    (Op.ADC, AddressMode.ABSOLUTE_LONG),
    (Op.BVS, AddressMode.RELATIVE),
    (Op.ADC, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.ADC, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.ADC, AddressMode.STACK_RELATIVE_INDIRECT_INDEXED),
    (Op.STZ, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.ADC, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.ROR, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.ADC, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.SEI, AddressMode.IMPLIED),
    (Op.ADC, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.PLY, AddressMode.IMPLIED),
    (Op.TDC, AddressMode.IMPLIED),
    (Op.JMP, AddressMode.ABSOLUTE_INDEXED_INDIRECT),
    (Op.ADC, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.ROR, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.ADC, AddressMode.ABSOLUTE_INDEXED_LONG),
    (Op.BRA, AddressMode.RELATIVE),
    (Op.STA, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.BRL, AddressMode.RELATIVE_LONG),
    (Op.STA, AddressMode.STACK_RELATIVE),
    (Op.STY, AddressMode.DIRECT_PAGE),
    (Op.STA, AddressMode.DIRECT_PAGE),
    (Op.STX, AddressMode.DIRECT_PAGE),
    (Op.STA, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.DEY, AddressMode.IMPLIED),
    (Op.BIT, AddressMode.IMMEDIATE_M),
    (Op.TXA, AddressMode.IMPLIED),
    (Op.PHB, AddressMode.IMPLIED),
    (Op.STY, AddressMode.ABSOLUTE),
    (Op.STA, AddressMode.ABSOLUTE),
    (Op.STX, AddressMode.ABSOLUTE),
    (Op.STA, AddressMode.ABSOLUTE_LONG),
    (Op.BCC, AddressMode.RELATIVE),
    (Op.STA, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.STA, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.STA, AddressMode.STACK_RELATIVE_INDIRECT_INDEXED),
    (Op.STY, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.STA, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.STX, AddressMode.DIRECT_PAGE_INDEXED_Y),
    (Op.STA, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.TYA, AddressMode.IMPLIED),
    (Op.STA, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.TXS, AddressMode.IMPLIED),
    (Op.TXY, AddressMode.IMPLIED),
    (Op.STZ, AddressMode.ABSOLUTE),
    (Op.STA, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.STZ, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.STA, AddressMode.ABSOLUTE_INDEXED_LONG),
    (Op.LDY, AddressMode.IMMEDIATE_X),
    (Op.LDA, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.LDX, AddressMode.IMMEDIATE_X),
    (Op.LDA, AddressMode.STACK_RELATIVE),
    (Op.LDY, AddressMode.DIRECT_PAGE),
    (Op.LDA, AddressMode.DIRECT_PAGE),
    (Op.LDX, AddressMode.DIRECT_PAGE),
    (Op.LDA, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.TAY, AddressMode.IMPLIED),
    (Op.LDA, AddressMode.IMMEDIATE_M),
    (Op.TAX, AddressMode.IMPLIED),
    (Op.PLB, AddressMode.IMPLIED),
    (Op.LDY, AddressMode.ABSOLUTE),
    (Op.LDA, AddressMode.ABSOLUTE),
    (Op.LDX, AddressMode.ABSOLUTE),
    (Op.LDA, AddressMode.ABSOLUTE_LONG),
    (Op.BCS, AddressMode.RELATIVE),
    (Op.LDA, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.LDA, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.LDA, AddressMode.STACK_RELATIVE_INDIRECT_INDEXED),
    (Op.LDY, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.LDA, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.LDX, AddressMode.DIRECT_PAGE_INDEXED_Y),
    (Op.LDA, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.CLV, AddressMode.IMPLIED),
    (Op.LDA, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.TSX, AddressMode.IMPLIED),
    (Op.TYX, AddressMode.IMPLIED),
    (Op.LDY, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.LDA, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.LDX, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.LDA, AddressMode.ABSOLUTE_INDEXED_LONG),
    (Op.CPY, AddressMode.IMMEDIATE_X),
    (Op.CMP, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.REP, AddressMode.IMMEDIATE_8),
    (Op.CMP, AddressMode.STACK_RELATIVE),
    (Op.CPY, AddressMode.DIRECT_PAGE),
    (Op.CMP, AddressMode.DIRECT_PAGE),
    (Op.DEC, AddressMode.DIRECT_PAGE),
    (Op.CMP, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.INY, AddressMode.IMPLIED),
    (Op.CMP, AddressMode.IMMEDIATE_M),
    (Op.DEX, AddressMode.IMPLIED),
    (Op.WAI, AddressMode.IMPLIED),
    (Op.CPY, AddressMode.ABSOLUTE),
    (Op.CMP, AddressMode.ABSOLUTE),
    (Op.DEC, AddressMode.ABSOLUTE),
    (Op.CMP, AddressMode.ABSOLUTE_LONG),
    (Op.BNE, AddressMode.RELATIVE),
    (Op.CMP, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.CMP, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.CMP, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.PEI, AddressMode.PEI_DIRECT_PAGE_INDIRECT),
    (Op.CMP, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.DEC, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.CMP, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.CLD, AddressMode.IMPLIED),
    (Op.CMP, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.PHX, AddressMode.IMPLIED),
    (Op.STP, AddressMode.IMPLIED),
    (Op.JML, AddressMode.ABSOLUTE_INDIRECT_LONG),
    (Op.CMP, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.DEC, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.CMP, AddressMode.ABSOLUTE_INDEXED_LONG),
    (Op.CPX, AddressMode.IMMEDIATE_X),
    (Op.SBC, AddressMode.DIRECT_PAGE_INDEXED_INDIRECT),
    (Op.SEP, AddressMode.IMMEDIATE_8),
    (Op.SBC, AddressMode.STACK_RELATIVE),
    (Op.CPX, AddressMode.DIRECT_PAGE),
    (Op.SBC, AddressMode.DIRECT_PAGE),
    (Op.INC, AddressMode.DIRECT_PAGE),
    (Op.SBC, AddressMode.DIRECT_PAGE_INDIRECT_LONG),
    (Op.INX, AddressMode.IMPLIED),
    (Op.SBC, AddressMode.IMMEDIATE_M),
    (Op.NOP, AddressMode.IMPLIED),
    (Op.XBA, AddressMode.IMPLIED),
    (Op.CPX, AddressMode.ABSOLUTE),
    (Op.SBC, AddressMode.ABSOLUTE),
    (Op.INC, AddressMode.ABSOLUTE),
    (Op.SBC, AddressMode.ABSOLUTE_LONG),
    (Op.BEQ, AddressMode.RELATIVE),
    (Op.SBC, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED),
    (Op.SBC, AddressMode.DIRECT_PAGE_INDIRECT),
    (Op.SBC, AddressMode.STACK_RELATIVE_INDIRECT_INDEXED),
    (Op.PEA, AddressMode.STACK_ABSOLUTE),
    (Op.SBC, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.INC, AddressMode.DIRECT_PAGE_INDEXED_X),
    (Op.SBC, AddressMode.DIRECT_PAGE_INDIRECT_INDEXED_LONG),
    (Op.SED, AddressMode.IMPLIED),
    (Op.SBC, AddressMode.ABSOLUTE_INDEXED_Y),
    (Op.PLX, AddressMode.IMPLIED),
    (Op.XCE, AddressMode.IMPLIED),
    (Op.JSR, AddressMode.ABSOLUTE_INDEXED_INDIRECT),
    (Op.SBC, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.INC, AddressMode.ABSOLUTE_INDEXED_X),
    (Op.SBC, AddressMode.ABSOLUTE_INDEXED_LONG),
]
