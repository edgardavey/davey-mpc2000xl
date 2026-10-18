.intel_syntax noprefix
.code16
.set D_OFF, data - start
start:
    mov ax, offset D_OFF
    cmp byte ptr cs:[D_OFF], 3
    jb done
    .byte 0x9a
    .word 0x3a36, 0x3e19
    .byte 0xea
    .word 0x25ac, 0x35b0
done:
    retf
data: .byte 1,2,3
