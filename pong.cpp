#include "snes.hpp"
#include "w65816.hpp"

Register A, X, Y, S, D;
uint32_t B = 0;
Flags P;
uint8_t mem[0x20000];

void reset();
void nmi_008199();
void sub_00822B();

void reset()
{
reset:
    // SEI();
    sub_00822B();

    // REP_imm(0x30);
    STZ_w(OAMADDL);
    // SEP_imm(0x30);
    LDX_imm_b(0x80);

loc_00800D:
    LDA_imm_b(0x0a);
    STA_b(OAMDATA);
    LDA_imm_b(0xf0);
    STA_b(OAMDATA);
    STA_b(OAMDATA);
    STA_b(OAMDATA);
    DEC_b(X.l);
    BNE(loc_00800D);

    LDX_imm_b(0x20);
    LDA_imm_b(0x55);

loc_008024:
    STA_b(OAMDATA);
    DEC_b(X.l);
    BNE(loc_008024);

    // REP_imm(0x30);
    // SEP_imm(0x20);
    STZ_b(CGADD);
    LDX_imm_w(0x2200);
    STX_w(DMAP0);
    LDX_imm_w(0x82e6);
    STX_w(A1T0L);
    LDA_imm_b(0x00);
    STA_b(A1B0);
    LDX_imm_w(0x0200);
    STX_w(DAS0);
    LDA_imm_b(0x01);
    STA_b(MDMAEN);  // DMA: $0082E6 -> CGRAM (512 bytes)
    LDA_imm_b(0x80);
    STA_b(VMAIN);
    LDX_imm_w(0x0000);
    STX_w(VMADDL);
    LDX_imm_w(0x1801);
    STX_w(DMAP0);
    LDX_imm_w(0x87a6);
    STX_w(A1T0L);
    LDA_imm_b(0x00);
    STA_b(A1B0);
    LDX_imm_w(0x0800);
    STX_w(DAS0);
    LDA_imm_b(0x01);
    STA_b(MDMAEN);  // DMA: $0087A6 -> VRAM (2048 bytes)
    LDA_imm_b(0x80);
    STA_b(VMAIN);
    LDX_imm_w(0x1000);
    STX_w(VMADDL);
    LDX_imm_w(0x1801);
    STX_w(DMAP0);
    LDX_imm_w(0x84e6);
    STX_w(A1T0L);
    LDA_imm_b(0x00);
    STA_b(A1B0);
    LDX_imm_w(0x02c0);
    STX_w(DAS0);
    LDA_imm_b(0x01);
    STA_b(MDMAEN);  // DMA: $0084E6 -> VRAM (704 bytes)
    LDA_imm_b(0x80);
    STA_b(VMAIN);
    LDX_imm_w(0x4000);
    STX_w(VMADDL);
    LDX_imm_w(0x1801);
    STX_w(DMAP0);
    LDX_imm_w(0x8fa6);
    STX_w(A1T0L);
    LDA_imm_b(0x00);
    STA_b(A1B0);
    LDX_imm_w(0x0680);
    STX_w(DAS0);
    LDA_imm_b(0x01);
    STA_b(MDMAEN);  // DMA: $008FA6 -> VRAM (1664 bytes)
    LDA_imm_b(0x22);
    STA_b(OBSEL);
    LDA_imm_b(0x11);
    STA_b(BGMODE);
    LDA_imm_b(0x00);
    STA_b(BG1SC);
    LDA_imm_b(0x01);
    STA_b(BG12NBA);
    LDA_imm_b(0x11);
    STA_b(TM);
    STZ_b(D + 0x0c);
    LDA_imm_b(0x05);
    STA_b(D + 0x04);
    LDA_imm_b(0xe6);
    STA_b(D + 0x06);
    LDA_imm_b(0x32);
    STA_b(D + 0x00);
    LDA_imm_b(0x40);
    STA_b(D + 0x01);
    LDA_imm_b(0x02);
    STA_b(D + 0x03);
    STA_b(D + 0x02);
    LDA_imm_b(0x0f);
    STA_b(INIDISP);
    LDA_imm_b(0x81);
    STA_b(NMITIMEN);
    // CLI();

loc_0080FE:
    LDA_b(D + 0x0c);
    CMP_imm_b(0x00);
    BEQ(loc_0080FE);

    LDA_b(D + 0x09);
    BIT_imm_b(0x04);
    BEQ(loc_00810E);

    INC_b(A.l);
    INC_b(A.l);

loc_00810E:
    BIT_imm_b(0x08);
    BEQ(loc_008116);

    DEC_b(A.l);
    DEC_b(A.l);

loc_008116:
    LDA_b(D + 0x0b);
    BIT_imm_b(0x04);
    BEQ(loc_008120);

    INC_b(A.l);
    INC_b(A.l);

loc_008120:
    BIT_imm_b(0x08);
    BEQ(loc_008128);

    DEC_b(A.l);
    DEC_b(A.l);

loc_008128:
    CLC();
    LDA_b(D + 0x00);
    ADC_b(D + 0x02);
    STA_b(D + 0x00);
    CLC();
    LDA_b(D + 0x01);
    ADC_b(D + 0x03);
    STA_b(D + 0x01);
    LDA_b(D + 0x00);
    CMP_imm_b(0x15);
    BCS(loc_008153);

    SEC();
    LDA_b(D + 0x05);
    SBC_imm_b(0x08);
    CMP_b(D + 0x01);
    BCS(loc_008153);

    CLC();
    ADC_imm_b(0x28);
    CMP_b(D + 0x01);
    BCC(loc_008153);

    SEC();
    LDA_imm_b(0x00);
    SBC_b(D + 0x02);
    STA_b(D + 0x02);

loc_008153:
    LDA_b(D + 0x00);
    CMP_imm_b(0xe6);
    BCC(loc_008170);

    SEC();
    LDA_b(D + 0x07);
    SBC_imm_b(0x08);
    CMP_b(D + 0x01);
    BCS(loc_008170);

    CLC();
    ADC_imm_b(0x28);
    CMP_b(D + 0x01);
    BCC(loc_008170);

    SEC();
    LDA_imm_b(0x00);
    SBC_b(D + 0x02);
    STA_b(D + 0x02);

loc_008170:
    LDA_b(D + 0x01);
    CMP_imm_b(0x06);
    BCS(loc_00817D);

    SEC();
    LDA_imm_b(0x00);
    SBC_b(D + 0x03);
    STA_b(D + 0x03);

loc_00817D:
    CMP_imm_b(0xd2);
    BCC(loc_008188);

    SEC();
    LDA_imm_b(0x00);
    SBC_b(D + 0x03);
    STA_b(D + 0x03);

loc_008188:
    LDA_b(HVBJOY);
    AND_imm_b(0x80);
    BNE(loc_008188);

loc_00818F:
    LDA_b(HVBJOY);
    AND_imm_b(0x80);
    BEQ(loc_00818F);

    goto loc_0080FE;
}

void nmi_008199()
{
nmi_008199:
    PHA_b();
    PHX_w();
    LDA_imm_b(0x80);
    AND_b(RDNMI);
    STZ_b(OAMADDL);
    STZ_b(OAMADDH);
    LDA_b(D + 0x00);
    STA_b(OAMDATA);
    LDA_b(D + 0x01);
    STA_b(OAMDATA);
    LDA_imm_b(0x08);
    STA_b(OAMDATA);
    LDA_imm_b(0x38);
    STA_b(OAMDATA);
    LDA_b(D + 0x04);
    STA_b(OAMDATA);
    LDA_b(D + 0x05);
    STA_b(OAMDATA);
    LDA_imm_b(0x00);
    STA_b(OAMDATA);
    LDA_imm_b(0x38);
    STA_b(OAMDATA);
    LDA_b(D + 0x06);
    STA_b(OAMDATA);
    LDA_b(D + 0x07);
    STA_b(OAMDATA);
    LDA_imm_b(0x00);
    STA_b(OAMDATA);
    LDA_imm_b(0x38);
    STA_b(OAMDATA);
    STZ_b(OAMADDL);
    LDA_imm_b(0x01);
    STA_b(OAMADDH);
    LDA_imm_b(0x68);
    STA_b(OAMDATA);
    LDA_imm_b(0x55);
    STA_b(OAMDATA);
    BEQ(loc_0081F6);

loc_0081F6:
    LDA_b(HVBJOY);
    AND_imm_b(0x01);
    BEQ(loc_0081F6);

loc_0081FD:
    LDA_b(HVBJOY);
    AND_imm_b(0x01);
    BNE(loc_0081FD);

    LDX_w(JOY1L);
    STX_w(D + 0x08);
    LDX_w(JOY2L);
    STX_w(D + 0x0a);
    LDA_b(D + 0x09);
    BIT_imm_b(0x10);
    BEQ(loc_00821B);

    LDA_b(D + 0x0c);
    INC_b(A.l);
    AND_imm_b(0x01);
    STA_b(D + 0x0c);

loc_00821B:
    LDA_b(D + 0x0b);
    BIT_imm_b(0x10);
    BEQ(loc_008228);

    LDA_b(D + 0x0c);
    INC_b(A.l);
    AND_imm_b(0x01);
    STA_b(D + 0x0c);

loc_008228:
    PLX_w();
    PLA_b();
    return;
}

void sub_00822B()
{
sub_00822B:
    CLC();
    // XCE();
    // REP_imm(0x30);
    // SEP_imm(0x20);
    LDA_imm_b(0x8f);
    STA_b(INIDISP);
    LDX_imm_w(0x0001);

loc_008239:
    STZ_b(B + 0x2100 + X);
    INC_w(X.w);
    CPX_imm_w(0x0015);
    BNE(loc_008239);

    LDA_imm_b(0x80);
    STA_b(VMAIN);
    STZ_b(VMADDL);
    STZ_b(VMADDH);
    STZ_b(VMDATAL);
    STZ_b(VMDATAH);
    STZ_b(M7SEL);
    STZ_b(M7A);
    LDA_imm_b(0x01);
    STA_b(M7A);
    STZ_b(M7B);
    STZ_b(M7B);
    STZ_b(M7C);
    STZ_b(M7C);
    STZ_b(M7D);
    STA_b(M7D);
    STZ_b(M7X);
    STZ_b(M7X);
    STZ_b(M7Y);
    STZ_b(M7Y);
    STZ_b(CGADD);
    STZ_b(CGDATA);
    STZ_b(CGDATA);
    STZ_b(W12SEL);
    STZ_b(W34SEL);
    STZ_b(WOBJSEL);
    STZ_b(WH0);
    STZ_b(WH1);
    STZ_b(WH2);
    STZ_b(WH3);
    STZ_b(WBGLOG);
    STZ_b(WOBJLOG);
    STZ_b(TM);
    STZ_b(TS);
    STZ_b(TMW);
    LDA_imm_b(0x30);
    STA_b(CGWSEL);
    STZ_b(CGADSUB);
    LDA_imm_b(0xe0);
    STA_b(COLDATA);
    STZ_b(SETINI);
    STZ_b(NMITIMEN);
    LDA_imm_b(0xff);
    STA_b(WRIO);
    STZ_b(WRMPYA);
    STZ_b(WRMPYB);
    STZ_b(WRDIVL);
    STZ_b(WRDIVH);
    STZ_b(WRDIVB);
    STZ_b(HTIMEL);
    STZ_b(HTIMEH);
    STZ_b(VTIMEL);
    STZ_b(VTIMEH);
    STZ_b(MDMAEN);
    STZ_b(HDMAEN);
    STZ_b(MEMSEL);
    return;
}

