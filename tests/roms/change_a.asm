incsrc lorom.asm

org $8000
reset:
  rep #$20                      ; $008000
  lda #$1234                    ; $008002
  clc                           ; $008005
  adc #$0003                    ; $008006
  sei                           ; $008009
  sbc #$0002                    ; $00800A
  lda $7E0000                   ; $00800D
.loop:
  jmp .loop                     ; $008010
