incsrc lorom.asm

org $8000
reset:
  rep #$30                      ; $008000
  jsr double_state_change       ; $008002
  lda #$FFFF                    ; $008005
  ldx #$FFFF                    ; $008008
.loop:
  jmp .loop                     ; $00800B

double_state_change:
  bcs .return2                  ; $00800E
.return1:
  rep #$20                      ; $008010
  rts                           ; $008012
.return2:
  rep #$10                      ; $008013
  rts                           ; $008015
