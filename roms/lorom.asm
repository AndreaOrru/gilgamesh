arch 65816
lorom


;; Empty ROM.
org $008000
  fill $8000


;; Minimal ROM header.
org $00FFC0
title:
  db "TEST"

org $00FFD7
rom_size:
  db $05

org $00FFFC
reset_vector:
  dw $8000
