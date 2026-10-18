"""Program MONO (newer-MPC style): pads set to Voice overlap MONO choke each other, not only themselves.

Stock: when a MONO note starts, 35b0:2826(drum, note) kills the voices of the same drum playing the SAME note.
Here the MONO call site (35b0:26bc) goes to `pmono`, which kills voices of the same drum that play the same note
(stock behaviour) OR that are themselves MONO (voice slot byte +2 = overlap mode, 1 = MONO; measured 2026-10-17).
So: ALL -> MONO makes the whole program monophonic; one MONO pad among POLY pads behaves exactly as stock.
The two stock "mute assign" calls (26ec, 271c) are untouched. Voice slots: ds:0x9609 + v*20 (+0 drum, +1 note, +2 overlap)."""
import os, struct, tempfile
from asm16 import assemble

SRC = r'''
.intel_syntax noprefix
.code16
start:
    push bp
    mov bp, sp
    push si
    push di
    mov si, 31
    mov di, 0x9875                     /* voice 31 (ds = 0x582b, as at the stock call) */
.Lloop:
    mov al, byte ptr [di]
    cmp al, byte ptr [bp + 6]          /* same drum */
    jne .Lnext
    mov al, byte ptr [di + 1]
    cmp al, byte ptr [bp + 8]          /* same note: the stock MONO cut */
    je .Lkill
    cmp byte ptr [di + 2], 1           /* that voice is MONO too */
    jne .Lnext
    cmp al, 35                         /* and plays a real drum note */
    jb .Lnext
    cmp al, 98
    ja .Lnext
.Lkill:
    push si
    .byte 0x9a                         /* lcall 3e19:3a36  stock voice kill (si) */
    .word 0x3a36, 0x3e19
    add sp, 2
.Lnext:
    sub di, 20
    dec si
    jns .Lloop
    pop di
    pop si
    pop bp
    .byte 0xca                         /* retf 4: drops the caller's two pushed args (replaces its add sp,4) */
    .word 4
'''

def apply(img, lin):
    assert lin % 16 == 0
    seg = lin >> 4
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(SRC)
    code = assemble(p); os.remove(p)
    img.put(lin, code, 'prog_mono')
    # 35b0:26bc  call 2826 / add sp,4  ->  lcall seg:0000 / nop
    img.patch(0x35b00 + 0x26bc, bytes.fromhex('e8670183c404'), bytes([0x9a]) + struct.pack('<HH', 0, seg) + b'\x90')
    return len(code)
