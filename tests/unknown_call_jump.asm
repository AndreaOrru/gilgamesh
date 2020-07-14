incsrc lorom.asm

org $FFEA
  dw nmi

org $8000
reset:
  jmp ($9000)                   ; $008000
nmi:
  ldx #$00                      ; $008003
  jsr ($9000,x)                 ; $008005

org $9000
  dw loop                       ; $009000
loop:
  bra loop                      ; $009002
