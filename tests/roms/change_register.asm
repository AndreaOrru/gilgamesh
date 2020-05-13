incsrc lorom.asm

org $8000
reset:
  clc                           ; $008000
  rep #$20                      ; $008001
  lda #$1234                    ; $008003
  sep #$20                      ; $008006
  lda $7E0000                   ; $008008
  lda #$FF                      ; $00800C
  rep #$20                      ; $00800E
  adc #$0100                    ; $008010
  sep #$20                      ; $008013
  adc #$01                      ; $008015
  rep #$20                      ; $008017
.loop:
  jmp .loop                     ; $008019
