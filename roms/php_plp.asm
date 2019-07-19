incsrc lorom.asm

org $8000
reset:
  sep #$20                      ; $008000
  jsr php_plp                   ; $008002
  lda #$12                      ; $008005
.loop:
  jmp .loop                     ; $008007

php_plp:
  php                           ; $00800A
  rep #$20                      ; $00800B
  lda #$3456                    ; $00800D
  plp                           ; $008010
  rts                           ; $008011
