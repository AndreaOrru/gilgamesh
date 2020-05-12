incsrc lorom.asm

org $8000
reset:
  rep #$20                      ; $008000
  jsr stack_manipulation        ; $008002
.loop:
  jmp .loop                     ; $008005

stack_manipulation:
  pla                           ; $008008
  lda #$8004                    ; $008009
  pha                           ; $00800B
.return:
  rts                           ; $00800C
