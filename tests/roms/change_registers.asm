incsrc lorom.asm

org $8000
reset:
  rep #$20                      ; $008000
  lda #$1234                    ; $008002
  pha                           ; $008005
  clc                           ; $008006
  adc #$0003                    ; $008007
  sei                           ; $00800A
  sbc #$0002                    ; $00800B
  lda $7E0000                   ; $00800E
  pla                           ; $008012

  sep #$10                      ; $008013
  ldx #$91                      ; $008015
  tax                           ; $008017

.loop:
  jmp .loop                     ; $008018
