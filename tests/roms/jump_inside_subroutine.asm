incsrc lorom.asm

org $8000
reset:
  sep #$20                      ; $008000
  jsr subroutine1               ; $008002
  lda #$1234                    ; $008005

  sep #$20                      ; $008008
  jsr subroutine2               ; $00800A
  lda #$1234                    ; $00800D
.loop:
  jmp .loop                     ; $008010

subroutine1:
  rep #$20                      ; $008013
  rts                           ; $008015

subroutine2:
  jmp subroutine1               ; $008016
