incsrc lorom.asm

org $8000
reset:
  rep #$30                      ; $008000
  jsr double_state_change       ; $008002
  lda #$FFFF                    ; $008005
  ldx #$FFFF                    ; $008008
  jsr unknown_state             ; $00800B
  lda #$FFFF                    ; $00800E
  ldx #$FFFF                    ; $008011
.loop:
  jmp .loop                     ; $008014

double_state_change:
  bcs .return2                  ; $008017
.return1:
  rep #$20                      ; $008019
  rts                           ; $00801B
.return2:
  rep #$10                      ; $00801C
  rts                           ; $00801E

unknown_state:
  bcs .return2                  ; $00801F
.return1:
  jmp ($9000)                   ; $008021
.return2:
  rep #$10                      ; $008024
  rts                           ; $008026

org $9000
  dw unknown_state_return2      ; $009000
