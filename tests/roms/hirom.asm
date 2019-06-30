arch 65816
hirom

;; Empty ROM.
org $C08000
  fill $8000


;; Minimal ROM header.
org $C0FFC0
title:
  db "TEST"

;; HiROM.
org $C0FFD6
rom_type:
  db $21

;; 2048 bytes.
org $C0FFD7
rom_size:
  db $01

org $C0FFEA
nmi_vector:
  dw $0000

org $C0FFFC
reset_vector:
  dw $8000
