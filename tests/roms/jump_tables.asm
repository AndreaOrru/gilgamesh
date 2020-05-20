incsrc lorom.asm

org $8000
reset:
  jsr (.jumptable,x)            ; $008000
.loop:
  jmp .loop                     ; $008003
.jumptable:
  dw $8100                      ; $008005
  dw $8200                      ; $008007

org $8100
x0:
  rts                           ; $008100

org $8200
x1:
  rts                           ; $008200
