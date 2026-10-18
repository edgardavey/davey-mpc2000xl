"""OTHER > VER. page: our own routine prints the version text ("1.2 DAVEY"); everything else on the page is stock.
The stock 21-byte block does: int 0xda with AL=1 (draws the stock date line) and prints "1.2". Ours keeps the int 0xda call exactly
as is (AL=1, so the stock date line is still drawn) and prints a longer version text at the same position."""
import os, struct, tempfile
from asm16 import assemble

BASE = 0x680
VERSION = '1.2 DAVEY'          # printed after "Operating system:" at the stock position (room for about 13 characters)

SRC = r'''
.intel_syntax noprefix
.code16
start:
ver_draw:
    mov al, 1
    mov cl, 0xa2
    mov ch, 0x0a
    int 0xda
    int 0x8f
    .byte 5, 0xa2, 0x0a
    .asciz "%(V)s"
    .byte 0xcb
    .balign 2, 0
'''
def source(version=None):
    return SRC % {'V': version or VERSION}

def apply(img):
    version = getattr(img, 'version', None) or VERSION
    assert len(version) <= 13
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source(version))
    code = assemble(p); os.remove(p)
    img.next = max(img.next, BASE)
    off = img.place(code, align=2)
    assert off == BASE
    old = bytes.fromhex('b001b1a2b50acdda' 'cd8f05a20a' '312e3220202020' '00')
    new = bytes([0x9a]) + struct.pack('<HH', off, 0x7000) + b'\x90' * (len(old) - 5)
    img.patch(0x30e36, old, new)
