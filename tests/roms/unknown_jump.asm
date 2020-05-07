incsrc lorom.asm

org $8000
reset:
  rep #$20                      ; $008000
  jsr unknown                   ; $008002
  lda #$FFFF                    ; $008005
.loop:
  jmp .loop                     ; $008008

unknown:
  jmp ($9000)                   ; $00800B
.return:
  rts                           ; $00800E

org $9000
  dw unknown_return             ; $009000
