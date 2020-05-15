incsrc lorom.asm

org $8000
reset:
  jsl stack_manipulation        ; $008000
.loop:
  jmp .loop                     ; $008004

stack_manipulation:
  rep #$20                      ; $008007
  pla                           ; $008009
  sep #$20                      ; $00800A
  pla                           ; $00800C

  lda #$00                      ; $00800D
  pha                           ; $00800F
  rep #$20                      ; $008010
  lda #$8004                    ; $008012
  pha                           ; $008015
.return:
  rtl                           ; $008016
