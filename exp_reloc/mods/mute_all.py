"""Mute group for the whole bank or program (user request 2026-10-20): PROGRAM > ASSIGN, cursor on Mode:, WINDOW ->
vubeatz's own "ALL FOR: BANK / PROGRAM" window, which copies this pad's Mode (NORMAL, SIMULT, VEL SW, DCY SW, MUTE n)
to the 16 pads of the bank or all 64 notes of the program.

How (all inside vubeatz's param-copy segment 0x7700, code in a measured-free gap at 0x77E60):
  - his field table (cs:0x434, 8-byte entries {note-record offset, size, min, max, label}) covers PARAMS fields 2..8;
    a 9th entry for Mode (note record byte 0 = Mode, the byte his mute-group code reads) lives here, id 9;
  - his lookup (cs:0x1B8) jumps here first: id 9 -> our entry, anything else -> his original code (unchanged behaviour);
  - the ASSIGN page's WINDOW key (page table ds:0x2BEE) goes to h_win: cursor on Mode (field 6) -> his ALL flow at cs:0x1DC
    with id 9 (the only PARAMS dependency in his entry is reading the field id from [0x8D66], which we replace); any other
    field -> the stock WINDOW handler 3E19:FF70, untouched;
  - his close path (cs:0x385, lcall 4E16:055A = back to PARAMS) returns to ASSIGN (3E19:FBF0, as PARAMS > F1 does) for id 9."""
import os, struct, tempfile
from asm16 import assemble

LIN = 0x77e60                 # free gap after the Sampling Mode block, before 0x77f00 (patcher mute8)
SEG = 0x7700                  # vubeatz param-copy segment
BASE = LIN - SEG * 16         # 0x0e60
ID = 9                        # PARAMS fields are 2..8 ([0x8d66]); 9 is never a PARAMS field

SRC = r'''
.intel_syntax noprefix
.code16
start:
entry:
    .byte 0, 1                 /* note record offset 0 (Mode), 1 byte */
    .word 0, 11                /* NORMAL .. MUTE 8 (MUTE 5-8 only exist with the Mute 1-8 option) */
    .word LABEL
lookup:                        /* vubeatz cs:0x1B8 jumps here; ax = field id */
    cmp ax, %(ID)d
    jne .Lorig
    mov si, offset ENTRY
    clc
    ret
.Lorig:                        /* his original lookup, byte for byte */
    sub ax, 2
    cmp ax, 6
    ja .Lbad
    shl ax, 3
    mov si, 0x434
    add si, ax
    clc
    ret
.Lbad:
    stc
    ret
h_win:                         /* ASSIGN page WINDOW (page key table ds:0x2BEE): Mode field -> ALL window, else stock */
    push ds
    push 0x582b
    pop ds
    cmp word ptr [0x8d5e], 6   /* ASSIGN field under the cursor; 6 = Mode */
    pop ds
    je .Lmode
    .byte 0xea                 /* any other field: the stock WINDOW handler, untouched */
    .word 0xff70, 0x3e19
.Lmode:
    .byte 0x9a                 /* what the stock handler runs before any field window (stops preview playback) */
    .word 0xff96, 0x3e19
h_mall:
    pusha
    push ds
    push es
    push 0x582b
    pop ds
    mov byte ptr cs:[0x4d9], 0
    mov ax, %(ID)d
    .byte 0xe9                 /* jmp cs:0x1DC: his entry continues (mov cs:[0x4d0],ax; lookup; ...; pop es/ds/popa/retf) */
    .word 0x1dc - (. - start + %(BASE)d) - 2
back:                          /* replaces his 'lcall 4E16:055A' at cs:0x385 (close: return to the page) */
    cmp word ptr cs:[0x4d0], %(ID)d
    je .Lassign
    .byte 0x9a
    .word 0x055a, 0x4e16       /* PARAMS, as before */
    ret
.Lassign:
    .byte 0x9a
    .word 0xfbf0, 0x3e19       /* ASSIGN page itself (what PARAMS F1 calls; 3E19:FF02 can open the DRUM-select prompt) */
    ret
label:
    .byte 0x02, 0x07, 0x1c, 0x10
    .ascii "Parameter: MODE"
    .byte 0, 0
'''


def source():
    consts = ''.join(f'.set {n.upper()}, {n} - start + {BASE}\n' for n in ('entry', 'label'))
    return (SRC % {'ID': ID, 'BASE': BASE}).replace('start:\n', consts + 'start:\n', 1)


def apply(img):
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source())
    code = assemble(p); os.remove(p)
    img.put(LIN, code, 'mute_all')
    lookup = BASE + 8                                                     # entry is 8 bytes, lookup follows
    h_win = BASE + code.index(bytes([0x1e, 0x68, 0x2b, 0x58, 0x1f, 0x83, 0x3e, 0x5e, 0x8d, 0x06]))   # push ds/push 0x582b/pop ds/cmp [0x8d5e],6
    j = code.index(bytes([0x2e, 0x83, 0x3e, 0xd0, 0x04, ID]))            # back starts with cmp word cs:[0x4d0], ID
    back = BASE + j
    # 1) his lookup -> ours (near jmp at cs:0x1B8)
    img.patch(SEG * 16 + 0x1b8, bytes.fromhex('83e802'), bytes([0xe9]) + struct.pack('<h', lookup - (0x1b8 + 3)))
    # 2) his close path -> ours (near call at cs:0x385 + 2 nops)
    img.patch(SEG * 16 + 0x385, bytes.fromhex('9a5a05164e'), bytes([0xe8]) + struct.pack('<h', back - (0x385 + 3)) + b'\x90\x90')
    # 3) ASSIGN page key table: WINDOW (event 0x15 at ds:0x2BEE) -> h_win. The per-field slot ds:0x2CB4+i*0x2A is NOT
    #    used: it is also the field's value-changed callback (the first version hooked it and disturbed vubeatz's state)
    img.patch(0x582b0 + 0x2bee, bytes.fromhex('1570ff193e'), bytes([0x15]) + struct.pack('<HH', h_win, SEG))
    return len(code)

