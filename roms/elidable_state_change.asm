incsrc lorom.asm

org $8000
reset:
  sep #$20                      ; $008000
  jsr elidable_state_change     ; $008002
  lda #$78                      ; $008005
.loop:
  jmp .loop                     ; $008007

elidable_state_change:
  bcs .branch                   ; $00800A
  lda #$12                      ; $00800C
.branch:
  rep #$20                      ; $00800E
  lda #$3456                    ; $008010
  sep #$20                      ; $008013
  rts                           ; $008015
