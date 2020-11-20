incsrc lorom.asm

org $8000
reset:
  jsr unknown                   ; $008000
.loop:
  jmp .loop                     ; $008003

unknown:
  brk                           ; $008006
