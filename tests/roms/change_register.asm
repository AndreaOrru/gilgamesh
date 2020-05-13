incsrc lorom.asm

org $8000
reset:
  rep #$20                      ; $008000
  lda #$1234                    ; $008002
  sep #$20                      ; $008005
  lda $7E0000                   ; $008007
  lda #$FF                      ; $00800B
  rep #$20                      ; $00800D
.loop:
  jmp .loop                     ; $00800F
