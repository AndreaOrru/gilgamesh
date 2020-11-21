incsrc lorom.asm

org $8000
reset:
  jsr unknown                   ; $008000
.loop:
  bra .loop                     ; $008003

unknown:
  jmp ($9000)                   ; $008005

return:
  rts                           ; $008008

org $9000
  dw return
