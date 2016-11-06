#ifndef __W65816_HPP
#define __W65816_HPP

#include <cstdint>

#define alwaysinline  inline __attribute__((always_inline))


struct Flags
{
    bool n = 0;
    bool v = 0;
    bool m = 0;
    bool x = 0;
    bool d = 0;
    bool i = 0;
    bool z = 0;
    bool c = 0;

    inline operator unsigned() const
    {
        return (n << 7) + (v << 6) + (m << 5) + (x << 4)
             + (d << 3) + (i << 2) + (z << 1) + (c << 0);
    }

    inline auto operator=(uint8_t data) -> unsigned
    {
        n = data & 0x80; v = data & 0x40; m = data & 0x20; x = data & 0x10;
        d = data & 0x08; i = data & 0x04; z = data & 0x02; c = data & 0x01;
        return data;
    }
};

struct Register
{
    union
    {
        uint16_t w;
        struct { uint8_t l, h; };
    };

    Register(uint16_t w = 0) : w(w) {}

    inline operator unsigned() const { return w; }
    inline auto operator   = (unsigned i) -> unsigned { return w   = i; }
    inline auto operator  |= (unsigned i) -> unsigned { return w  |= i; }
    inline auto operator  ^= (unsigned i) -> unsigned { return w  ^= i; }
    inline auto operator  &= (unsigned i) -> unsigned { return w  &= i; }
    inline auto operator <<= (unsigned i) -> unsigned { return w <<= i; }
    inline auto operator >>= (unsigned i) -> unsigned { return w >>= i; }
    inline auto operator  += (unsigned i) -> unsigned { return w  += i; }
    inline auto operator  -= (unsigned i) -> unsigned { return w  -= i; }
    inline auto operator  *= (unsigned i) -> unsigned { return w  *= i; }
    inline auto operator  /= (unsigned i) -> unsigned { return w  /= i; }
    inline auto operator  %= (unsigned i) -> unsigned { return w  %= i; }
};

struct uint24_t
{
    uint32_t d : 24;

    inline operator unsigned() const { return d; }
    inline auto operator   = (unsigned i) -> unsigned { return d = (     i) & 0xFFFFFF; }
    inline auto operator  |= (unsigned i) -> unsigned { return d = (d  | i) & 0xFFFFFF; }
    inline auto operator  ^= (unsigned i) -> unsigned { return d = (d  ^ i) & 0xFFFFFF; }
    inline auto operator  &= (unsigned i) -> unsigned { return d = (d  & i) & 0xFFFFFF; }
    inline auto operator <<= (unsigned i) -> unsigned { return d = (d << i) & 0xFFFFFF; }
    inline auto operator >>= (unsigned i) -> unsigned { return d = (d >> i) & 0xFFFFFF; }
    inline auto operator  += (unsigned i) -> unsigned { return d = (d  + i) & 0xFFFFFF; }
    inline auto operator  -= (unsigned i) -> unsigned { return d = (d  - i) & 0xFFFFFF; }
    inline auto operator  *= (unsigned i) -> unsigned { return d = (d  * i) & 0xFFFFFF; }
    inline auto operator  /= (unsigned i) -> unsigned { return d = (d  / i) & 0xFFFFFF; }
    inline auto operator  %= (unsigned i) -> unsigned { return d = (d  % i) & 0xFFFFFF; }
} __attribute__((packed));


extern Register A, X, Y, S, D;
extern uint32_t B;
extern Flags P;
extern uint8_t mem[];


alwaysinline uint8_t& mem_b(uint32_t i)
{
    int bank = i >> 16;

    if (bank >= 0x7E && bank <= 0x7F)
        return mem[i - 0x7E0000];
    else if (bank >= 0x00 && bank <= 0x01)
        return mem[i];

    // TODO: Raise an exception.
    return mem[0xFFFE];
}

alwaysinline uint16_t& mem_w(uint32_t i)
{
    int bank = i >> 16;

    if (bank >= 0x7E && bank <= 0x7F)
        return *((uint16_t*)&mem[i - 0x7E0000]);
    else if (bank >= 0x00 && bank <= 0x01)
        return *((uint16_t*)&mem[i]);

    // TODO: Raise an exception.
    return *((uint16_t*)&mem[0xFFFE]);
}

alwaysinline uint24_t& mem_l(uint32_t i)
{
    int bank = i >> 16;

    if (bank >= 0x7E && bank <= 0x7F)
        return *((uint24_t*)&mem[i - 0x7E0000]);
    else if (bank >= 0x00 && bank <= 0x01)
        return *((uint24_t*)&mem[i]);

    // TODO: Raise an exception.
    return *((uint24_t*)&mem[0xFFFE]);
}

#define BCS(l)  if  (P.c) goto l
#define BCC(l)  if (!P.c) goto l
#define BEQ(l)  if  (P.z) goto l
#define BNE(l)  if (!P.z) goto l
#define BMI(l)  if  (P.n) goto l
#define BPL(l)  if (!P.n) goto l
#define BVS(l)  if  (P.v) goto l
#define BVC(l)  if (!P.v) goto l

alwaysinline void ADC_imm_b(uint8_t v)
{
    int result;

    if (!P.d)
        result = A.l + v + P.c;
    else
    {
        result = (A.l & 0x0F) + (v & 0x0F) + (P.c << 0);
        if (result > 0x09) result += 0x06;
        P.c = result > 0x0F;
        result = (A.l & 0xF0) + (v & 0xF0) + (P.c << 4) + (result & 0x0F);
    }

    P.v = ~(A.l ^ v) & (A.l ^ result) & 0x80;
    if (P.d && result > 0x9F) result += 0x60;
    P.c = result > 0xFF;
    P.n = result & 0x80;
    P.z = (uint8_t)result == 0;

    A.l = result;
}
alwaysinline void ADC_b(uint32_t i) { ADC_imm_b(mem_b(i)); }

alwaysinline void ADC_imm_w(uint16_t v)
{
    int result;

    if (!P.d)
        result = A.w + v + P.c;
    else
    {
        result = (A.w & 0x000F) + (v & 0x000F) + (P.c <<  0);
        if (result > 0x0009) result += 0x0006;
        P.c = result > 0x000F;
        result = (A.w & 0x00F0) + (v & 0x00F0) + (P.c <<  4) + (result & 0x000F);
        if (result > 0x009F) result += 0x0060;
        P.c = result > 0x00FF;
        result = (A.w & 0x0F00) + (v & 0x0F00) + (P.c <<  8) + (result & 0x00FF);
        if (result > 0x09FF) result += 0x0600;
        P.c = result > 0x0FFF;
        result = (A.w & 0xF000) + (v & 0xF000) + (P.c << 12) + (result & 0x0FFF);
    }

    P.v = ~(A.w ^ v) & (A.w ^ result) & 0x8000;
    if (P.d && result > 0x9FFF) result += 0x6000;
    P.c = result > 0xFFFF;
    P.n = result & 0x8000;
    P.z = (uint16_t)result == 0;

    A.w = result;
}
alwaysinline void ADC_w(uint32_t i) { ADC_imm_w(mem_w(i)); }

alwaysinline void AND_imm_b(uint8_t v)
{
    A.l &= v;
    P.n = A.l & 0x80;
    P.z = A.l == 0;
}
alwaysinline void AND_b(uint32_t i) { AND_imm_b(mem_b(i)); }

alwaysinline void AND_imm_w(uint16_t v)
{
    A.w &= v;
    P.n = A.w & 0x8000;
    P.z = A.w == 0;
}
alwaysinline void AND_w(uint32_t i) { AND_imm_w(mem_w(i)); }

alwaysinline void BIT_imm_b(uint8_t v)
{
    P.n = v & 0x80;
    P.v = v & 0x40;
    P.z = (v & A.l) == 0;
}
alwaysinline void BIT_b(uint32_t i) { BIT_imm_b(mem_b(i)); }

alwaysinline void BIT_imm_w(uint16_t v)
{
    P.n = v & 0x8000;
    P.v = v & 0x4000;
    P.z = (v & A.w) == 0;
}
alwaysinline void BIT_w(uint32_t i) { BIT_imm_w(mem_w(i)); }

alwaysinline void CMP_imm_b(uint8_t v)
{
    int r = A.l - v;
    P.n = r & 0x80;
    P.z = (uint8_t)r == 0;
    P.c = r >= 0;
}
alwaysinline void CMP_b(uint32_t i) { CMP_imm_b(mem_b(i)); }

alwaysinline void CMP_imm_w(uint16_t v)
{
    int r = A.w - v;
    P.n = r & 0x8000;
    P.z = (uint16_t)r == 0;
    P.c = r >= 0;
}
alwaysinline void CMP_w(uint32_t i) { CMP_imm_w(mem_w(i)); }

alwaysinline void CPX_imm_b(uint8_t v)
{
    int r = X.l - v;
    P.n = r & 0x80;
    P.z = (uint8_t)r == 0;
    P.c = r >= 0;
}
alwaysinline void CPX_b(uint32_t i) { CPX_imm_b(mem_b(i)); }

alwaysinline void CPX_imm_w(uint16_t v)
{
    int r = X.w - v;
    P.n = r & 0x8000;
    P.z = (uint16_t)r == 0;
    P.c = r >= 0;
}
alwaysinline void CPX_w(uint32_t i) { CPX_imm_w(mem_w(i)); }

alwaysinline void CPY_imm_b(uint8_t v)
{
    int r = Y.l - v;
    P.n = r & 0x80;
    P.z = (uint8_t)r == 0;
    P.c = r >= 0;
}
alwaysinline void CPY_b(uint32_t i) { CPY_imm_b(mem_b(i)); }

alwaysinline void CPY_imm_w(uint16_t v)
{
    int r = Y.w - v;
    P.n = r & 0x8000;
    P.z = (uint16_t)r == 0;
    P.c = r >= 0;
}
alwaysinline void CPY_w(uint32_t i) { CPY_imm_w(mem_w(i)); }

alwaysinline void EOR_imm_b(uint8_t v)
{
    A.l ^= v;
    P.n = A.l & 0x80;
    P.z = A.l == 0;
}
alwaysinline void EOR_b(uint32_t i) { EOR_imm_b(mem_b(i)); }

alwaysinline void EOR_imm_w(uint16_t v)
{
    A.w ^= v;
    P.n = A.w & 0x8000;
    P.z = A.w == 0;
}
alwaysinline void EOR_w(uint32_t i) { EOR_imm_w(mem_w(i)); }

alwaysinline void LDA_imm_b(uint8_t v)
{
    A.l = v;
    P.n = A.l & 0x80;
    P.z = A.l == 0;
}
alwaysinline void LDA_b(uint32_t i) { LDA_imm_b(mem_b(i)); }

alwaysinline void LDA_imm_w(uint16_t v)
{
    A.w = v;
    P.n = A.w & 0x8000;
    P.z = A.w == 0;
}
alwaysinline void LDA_w(uint32_t i) { LDA_imm_w(mem_w(i)); }

alwaysinline void LDX_imm_b(uint8_t v)
{
    X.l = v;
    P.n = X.l & 0x80;
    P.z = X.l == 0;
}
alwaysinline void LDX_b(uint32_t i) { LDX_imm_b(mem_b(i)); }

alwaysinline void LDX_imm_w(uint16_t v)
{
    X.w = v;
    P.n = X.w & 0x8000;
    P.z = X.w == 0;
}
alwaysinline void LDX_w(uint32_t i) { LDX_imm_w(mem_w(i)); }

alwaysinline void LDY_imm_b(uint8_t v)
{
    Y.l = v;
    P.n = Y.l & 0x80;
    P.z = Y.l == 0;
}
alwaysinline void LDY_b(uint32_t i) { LDY_imm_b(mem_b(i)); }

alwaysinline void LDY_imm_w(uint16_t v)
{
    Y.w = v;
    P.n = Y.w & 0x8000;
    P.z = Y.w == 0;
}
alwaysinline void LDY_w(uint32_t i) { LDY_imm_w(mem_w(i)); }

alwaysinline void ORA_imm_b(uint8_t v)
{
    A.l |= v;
    P.n = A.l & 0x80;
    P.z = A.l == 0;
}
alwaysinline void ORA_b(uint32_t i) { ORA_imm_b(mem_b(i)); }

alwaysinline void ORA_imm_w(uint16_t v)
{
    A.w |= v;
    P.n = A.w & 0x8000;
    P.z = A.w == 0;
}
alwaysinline void ORA_w(uint32_t i) { ORA_imm_w(mem_w(i)); }

alwaysinline void SBC_imm_b(uint8_t v)
{
    int result;
    v ^= 0xFF;

    if (!P.d) {
        result = A.l + v + P.c;
    } else {
        result = (A.l & 0x0F) + (v & 0x0F) + (P.c << 0);
        if (result <= 0x0F) result -= 0x06;
        P.c = result > 0x0F;
        result = (A.l & 0xF0) + (v & 0xF0) + (P.c << 4) + (result & 0x0F);
    }

    P.v = ~(A.l ^ v) & (A.l ^ result) & 0x80;
    if (P.d && result <= 0xFF) result -= 0x60;
    P.c = result > 0xFF;
    P.n = result & 0x80;
    P.z = (uint8_t)result == 0;

    A.l = result;
}
alwaysinline void SBC_b(uint32_t i) { SBC_imm_b(mem_b(i)); }

alwaysinline void SBC_imm_w(uint16_t v)
{
    int result;
    v ^= 0xFFFF;

    if (!P.d) {
        result = A.w + v + P.c;
    } else {
        result = (A.w & 0x000F) + (v & 0x000F) + (P.c <<  0);
        if (result <= 0x000F) result -= 0x0006;
        P.c = result > 0x000F;
        result = (A.w & 0x00F0) + (v & 0x00F0) + (P.c <<  4) + (result & 0x000F);
        if (result <= 0x00FF) result -= 0x0060;
        P.c = result > 0x00FF;
        result = (A.w & 0x0F00) + (v & 0x0F00) + (P.c <<  8) + (result & 0x00FF);
        if (result <= 0x0FFF) result -= 0x0600;
        P.c = result > 0x0FFF;
        result = (A.w & 0xF000) + (v & 0xF000) + (P.c << 12) + (result & 0x0FFF);
    }

    P.v = ~(A.w ^ v) & (A.w ^ result) & 0x8000;
    if (P.d && result <= 0xFFFF) result -= 0x6000;
    P.c = result > 0xFFFF;
    P.n = result & 0x8000;
    P.z = (uint16_t)result == 0;

    A.w = result;
}
alwaysinline void SBC_w(uint32_t i) { SBC_imm_w(mem_w(i)); }

alwaysinline void INC_b(uint8_t& v)
{
    v++;
    P.n = v & 0x80;
    P.z = v == 0;
}
alwaysinline void INC_b(uint32_t i) { INC_b(mem_b(i)); }

alwaysinline void INC_w(uint16_t& v)
{
    v++;
    P.n = v & 0x8000;
    P.z = v == 0;
}
alwaysinline void INC_w(uint32_t i) { INC_w(mem_w(i)); }

alwaysinline void DEC_b(uint8_t& v)
{
    v--;
    P.n = v & 0x80;
    P.z = v == 0;
}
alwaysinline void DEC_b(uint32_t i) { DEC_b(mem_b(i)); }

alwaysinline void DEC_w(uint16_t& v)
{
    v--;
    P.n = v & 0x8000;
    P.z = v == 0;
}
alwaysinline void DEC_w(uint32_t i) { DEC_w(mem_w(i)); }

alwaysinline void ASL_b(uint8_t& v)
{
    P.c = v & 0x80;
    v <<= 1;
    P.n = v & 0x80;
    P.z = v == 0;
}
alwaysinline void ASL_b(uint32_t i) { ASL_b(mem_b(i)); }

alwaysinline void ASL_w(uint16_t& v)
{
    P.c = v & 0x8000;
    v <<= 1;
    P.n = v & 0x8000;
    P.z = v == 0;
}
alwaysinline void ASL_w(uint32_t i) { ASL_w(mem_w(i)); }

alwaysinline void LSR_b(uint8_t& v)
{
    P.c = v & 1;
    v >>= 1;
    P.n = v & 0x80;
    P.z = v == 0;
}
alwaysinline void LSR_b(uint32_t i) { LSR_b(mem_b(i)); }

alwaysinline void LSR_w(uint16_t& v)
{
    P.c = v & 1;
    v >>= 1;
    P.n = v & 0x8000;
    P.z = v == 0;
}
alwaysinline void LSR_w(uint32_t i) { LSR_w(mem_w(i)); }

alwaysinline void ROL_b(uint8_t& v)
{
    unsigned carry = (unsigned)P.c;
    P.c = v & 0x80;
    v = (v << 1) | carry;
    P.n = v & 0x80;
    P.z = v == 0;
}
alwaysinline void ROL_b(uint32_t i) { ROL_b(mem_b(i)); }

alwaysinline void ROL_w(uint16_t& v)
{
    unsigned carry = (unsigned)P.c;
    P.c = v & 0x8000;
    v = (v << 1) | carry;
    P.n = v & 0x8000;
    P.z = v == 0;
}
alwaysinline void ROL_w(uint32_t i) { ROL_w(mem_w(i)); }

alwaysinline void ROR_b(uint8_t& v)
{
    unsigned carry = (unsigned)P.c << 7;
    P.c = v & 1;
    v = carry | (v >> 1);
    P.n = v & 0x80;
    P.z = v == 0;
}
alwaysinline void ROR_b(uint32_t i) { ROR_b(mem_b(i)); }

alwaysinline void ROR_w(uint16_t& v)
{
    unsigned carry = (unsigned)P.c << 15;
    P.c = v & 1;
    v = carry | (v >> 1);
    P.n = v & 0x8000;
    P.z = v == 0;
}
alwaysinline void ROR_w(uint32_t i) { ROR_w(mem_w(i)); }

alwaysinline void TRB_b(uint8_t& v)
{
    P.z = (v & A.l) == 0;
    v &= ~A.l;
}
alwaysinline void TRB_b(uint32_t i) { TRB_b(mem_b(i)); }

alwaysinline void TRB_w(uint16_t& v)
{
    P.z = (v & A.w) == 0;
    v &= ~A.w;
}
alwaysinline void TRB_w(uint32_t i) { TRB_w(mem_w(i)); }

alwaysinline void TSB_b(uint8_t& v)
{
    P.z = (v & A.l) == 0;
    v |= A.l;
}
alwaysinline void TSB_b(uint32_t i) { TSB_b(mem_b(i)); }

alwaysinline void TSB_w(uint16_t& v)
{
    P.z = (v & A.w) == 0;
    v |= A.w;
}
alwaysinline void TSB_w(uint32_t i) { TSB_w(mem_w(i)); }

alwaysinline void XBA()
{
    A.l ^= A.h;
    A.h ^= A.l;
    A.l ^= A.h;
    P.n = (A.l & 0x80);
    P.z = (A.l == 0);
}

alwaysinline void T_b(Register& from, Register& to) {
    to.l = from.l;
    P.n = (to.l & 0x80);
    P.z = (to.l == 0);
}

alwaysinline void T_w(Register& from, Register& to) {
    to.w = from.w;
    P.n = (to.w & 0x8000);
    P.z = (to.w == 0);
}

alwaysinline void TAX_b() { T_b(A, X); }
alwaysinline void TAX_w() { T_w(A, X); }
alwaysinline void TAY_b() { T_b(A, Y); }
alwaysinline void TAY_w() { T_w(A, Y); }
alwaysinline void TXA_b() { T_b(X, A); }
alwaysinline void TXA_w() { T_w(X, A); }
alwaysinline void TYA_b() { T_b(Y, A); }
alwaysinline void TYA_w() { T_w(Y, A); }
alwaysinline void TXY_b() { T_b(X, Y); }
alwaysinline void TXY_w() { T_w(X, Y); }
alwaysinline void TYX_b() { T_b(Y, X); }
alwaysinline void TYX_w() { T_w(Y, X); }
alwaysinline void TSX_b() { T_b(S, X); }
alwaysinline void TSX_w() { T_b(S, X); }
alwaysinline void TCD()   { T_w(A, D); }
alwaysinline void TDC()   { T_w(D, A); }

alwaysinline void TCS()
{
    S.w = A.w;
}

alwaysinline void TXS()
{
    S.w = X.w;
}

alwaysinline void PHA_b() { mem_b(S.w--) = A.l; }
alwaysinline void PHA_w() { mem_b(S.w--) = A.h; mem_b(S.w--) = A.l; }
alwaysinline void PHX_b() { mem_b(S.w--) = X.l; }
alwaysinline void PHX_w() { mem_b(S.w--) = X.h; mem_b(S.w--) = X.l; }
alwaysinline void PHY_b() { mem_b(S.w--) = Y.l; }
alwaysinline void PHY_w() { mem_b(S.w--) = Y.h; mem_b(S.w--) = Y.l; }
alwaysinline void PLA_b() { A.l = mem_b(++S.w); }
alwaysinline void PLA_w() { A.l = mem_b(++S.w); A.h = mem_b(++S.w); }
alwaysinline void PLX_b() { X.l = mem_b(++S.w); }
alwaysinline void PLX_w() { X.l = mem_b(++S.w); X.h = mem_b(++S.w); }
alwaysinline void PLY_b() { Y.l = mem_b(++S.w); }
alwaysinline void PLY_w() { Y.l = mem_b(++S.w); Y.h = mem_b(++S.w); }

alwaysinline void PHD()
{
    mem_b(S.w--) = D.h;
    mem_b(S.w--) = D.l;
}

alwaysinline void PHB()
{
    mem_b(S.w--) = B >> 16;
}

// NOTE: Modified form with parameters.
alwaysinline void PHK(uint8_t b)
{
    mem_b(S.w--) = b;
}

// NOTE: Modified form with parameters.
alwaysinline void PHP(bool m, bool x)
{
    P.m = m;
    P.x = x;
    mem_b(S.w--) = P;
}

alwaysinline void PLD()
{
    D.l = mem_b(++S.w);
    D.h = mem_b(++S.w);
    P.n = (D.w & 0x8000);
    P.z = (D.w == 0);
}

alwaysinline void PLB()
{
    B = mem_b(++S.w) << 16;
    P.n = (B & 0x800000);
    P.z = (B == 0);
}

alwaysinline void PLP()
{
    P = mem_b(++S.w);
    if (P.x)
    {
        X.h = 0x00;
        Y.h = 0x00;
    }
}

alwaysinline void PEA(uint16_t i)
{
    mem_b(S.w--) = i >> 8;
    mem_b(S.w--) = i & 0xFF;
}

alwaysinline void PEI(uint8_t i)
{
    mem_b(S.w--) = mem_b(D + i + 1);
    mem_b(S.w--) = mem_b(D + i);
}

alwaysinline void CLC() { P.c = 0; }
alwaysinline void CLD() { P.d = 0; }
alwaysinline void CLV() { P.v = 0; }
alwaysinline void SEC() { P.c = 1; }
alwaysinline void SED() { P.d = 1; }

alwaysinline void STA_b(uint32_t i) { mem_b(i) = A.l; }
alwaysinline void STA_w(uint32_t i) { mem_w(i) = A.w; }
alwaysinline void STZ_b(uint32_t i) { mem_b(i) = 0;   }
alwaysinline void STZ_w(uint32_t i) { mem_w(i) = 0;   }
alwaysinline void STX_b(uint32_t i) { mem_b(i) = X.l; }
alwaysinline void STX_w(uint32_t i) { mem_w(i) = X.w; }
alwaysinline void STY_b(uint32_t i) { mem_b(i) = Y.l; }
alwaysinline void STY_w(uint32_t i) { mem_w(i) = Y.w; }


#endif
