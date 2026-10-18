"""MUTE groups 1-8 (vubeatz has 1-4). The pad Mode byte takes values 4..11; the vubeatz trigger code already
handles any group value inside its range, so this widens the range checks and adds the MUTE 5-8 labels."""
import os, struct, tempfile
from asm16 import assemble

BASE = 0x600
SRC = r'''
.intel_syntax noprefix
.code16
.set BASE, %(BASE)d
start:
label8:
    cmp bl, 4
    jb .Lnative
    cmp bl, 11
    ja .Linvalid
    sub bl, 4
    shl bx, 1
    mov dx, word ptr cs:[bx + TAB]
    mov cx, @SEG@
    mov bx, 4
    .byte 0xcb
.Linvalid:
    xor bx, bx
.Lnative:
    shl bx, 2
    mov dx, word ptr [bx + 0x2bfe]
    mov cx, word ptr [bx + 0x2c00]
    .byte 0xcb
tab:
    .word S1, S2, S3, S4, S5, S6, S7, S8
s1: .asciz "MUTE 1"
s2: .asciz "MUTE 2"
s3: .asciz "MUTE 3"
s4: .asciz "MUTE 4"
s5: .asciz "MUTE 5"
s6: .asciz "MUTE 6"
s7: .asciz "MUTE 7"
s8: .asciz "MUTE 8"
    .balign 2, 0
'''
def source():
    consts = '.set TAB, tab - start + BASE\n' + ''.join(f'.set S{i}, s{i} - start + BASE\n' for i in range(1, 9))
    return (SRC % {'BASE': BASE}).replace('start:\n', consts + 'start:\n', 1)

def apply(img, lin):
    assert (lin - BASE) % 16 == 0
    seg = (lin - BASE) >> 4
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source().replace('@SEG@', str(seg)))
    code = assemble(p); os.remove(p)
    img.put(lin, code, 'mute8')
    # Mode field maximum 7 -> 11
    img.patch(0x5b044, bytes([0x07]), bytes([0x0b]))
    # vubeatz trigger checks: "cmp ...,7" -> 11
    # (0x75c38 is a check inside vubeatz REGIONS code: the patcher applies it only `when regions`; REGIONS is not in this line)
    img.patch(0x775c5, bytes.fromhex('80fa07'), bytes.fromhex('80fa0b'))
    # label routine: far jump to the 8-group version (function lived at 7700:0566)
    img.patch(0x77566, bytes.fromhex('80fb047218'), bytes([0xea]) + struct.pack('<HH', BASE, seg))
    return len(code)
