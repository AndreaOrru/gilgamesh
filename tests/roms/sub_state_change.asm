incsrc lorom.asm

org $8000
reset:
  sep #$30                      ; $008000
  jsr state_change              ; $008002
  lda #$1234                    ; $008005
  ldx #$1234                    ; $008008
.loop:
  jmp .loop                     ; $00800B

state_change:
  rep #$30                      ; $00800E
  rts                           ; $008010
