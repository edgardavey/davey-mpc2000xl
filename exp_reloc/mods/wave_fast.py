"""Fast waveform (user request 2026-10-21): the TRIM / LOOP / ZONE / chop waveform appears several times sooner.

Stock (4E16:9EC4, called from the page tick): every sample of the sound is fetched (DMA, 4096 words per block into
7C00:03DE) and its min/max folded into the current column (245 columns); after loading each block the routine returns
until the next tick. A 10 s stereo sound took ~5.5 s (emulator).
Here:
  - step S: only every S-th sample is examined. S = the largest power of two <= samples-per-column / 8 (1..16), so
    every column still sees >= 8 samples; short sounds get S = 1 = stock behaviour;
  - blocks per tick: the routine returns only every S blocks, so a tick costs about the same CPU as stock
    (S times fewer samples per block) while the waveform finishes up to S times sooner.
Hooks: 4E16:9FCF (the 24 bytes that advance the buffer index and the column/total counters by 1) and 4E16:9FB1 (the
11 bytes after a block load: 'counter == 0 ? continue : return')."""
import os, struct, tempfile
from asm16 import assemble

LIN = 0x74a00                 # measured-free range 0x749A4-0x74CB1
SEG = LIN >> 4

SRC = r'''
.intel_syntax noprefix
.code16
start:
step_s:                        /* ax = S from the column width (32-bit samples*256 at ds:[0x8e64]:[0x8e62]) */
    mov ax, 16
    cmp word ptr [0x8e64], 0
    jne .Ls_done                /* >= 256 samples per column -> 16 */
    mov ax, word ptr [0x8e62]
    shr ax, 1
    shr ax, 1
    shr ax, 1
    shr ax, 1
    shr ax, 1
    shr ax, 1
    shr ax, 1
    shr ax, 1                   /* samples per column (0..255) */
    shr ax, 1
    shr ax, 1
    shr ax, 1                   /* / 8 */
    push cx
    mov cx, 1
.Ls_up:                         /* largest power of two <= ax, at least 1, at most 16 */
    cmp cx, 16
    jae .Ls_have
    push cx
    shl cx, 1
    cmp cx, ax
    pop cx
    ja .Ls_have
    shl cx, 1
    jmp .Ls_up
.Ls_have:
    mov ax, cx
    pop cx
.Ls_done:
    .byte 0xc3

advance:                        /* replaces 4E16:9FCF..9FE6 (ds = 582B; bx = sample, must survive) */
    push ax
    .byte 0xe8                  /* near call step_s (16-bit form; clang would emit 66 E8) */
    .word step_s - . - 2
    add word ptr [0x8e58], ax   /* buffer index */
    add byte ptr [0x8e67], al   /* column counter (in 1/256 units, as stock) */
    adc word ptr [0x8e68], 0
    add word ptr [0x8e5a], ax   /* samples consumed */
    adc word ptr [0x8e5c], 0
    pop ax
    .byte 0xcb

yield:                          /* replaces 4E16:9FB1..9FBB after a block load (es = 7C00): CF=1 continue, CF=0 return */
    cmp word ptr es:[0x3dc], 0
    je .Ly_go                   /* first column: always continue (stock) */
    push ax
    inc byte ptr cs:[BLOCKS]
    .byte 0xe8                  /* near call step_s (16-bit form; clang would emit 66 E8) */
    .word step_s - . - 2
    cmp byte ptr cs:[BLOCKS], al
    pop ax
    jb .Ly_go                   /* fewer than S blocks this tick: keep going */
    mov byte ptr cs:[BLOCKS], 0
    clc
    .byte 0xcb
.Ly_go:
    stc
    .byte 0xcb
blocks:
    .byte 0
    .balign 2, 0
    .word ADVANCE
    .word YIELD
'''


def source():
    consts = ''.join(f'.set {n.upper()}, {n} - start\n' for n in ('advance', 'yield', 'blocks'))
    return SRC.replace('start:\n', consts + 'start:\n', 1)


def apply(img):
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source())
    code = assemble(p); os.remove(p)
    img.put(LIN, code, 'wave_fast')
    advance, yld = struct.unpack('<HH', code[-4:])
    B = 0x4e160
    # 1) per-sample advance: inc [8E58] / add byte [8E67],1 / adc [8E68],0 / add [8E5A],1 / adc [8E5C],0  (24 bytes)
    old = bytes.fromhex('ff06588e' '8006678e01' '8316688e00' '83065a8e01' '83165c8e00')
    img.patch(B + 0x9fcf, old, bytes([0x9a]) + struct.pack('<HH', advance, SEG) + b'\x90' * (len(old) - 5))
    # 2) after a block load: cmp es:[3DC],0 / je 9FBC / jmp A14F  (11 bytes)  ->  lcall yield / jc 9FBB / jmp A14F / nop
    old = bytes.fromhex('26833edc0300' '7403' 'e99301')
    new = bytes([0x9a]) + struct.pack('<HH', yld, SEG) + bytes.fromhex('7203') + bytes([0xe9]) + struct.pack('<h', 0xa14f - 0x9fbb) + b'\x90'
    img.patch(B + 0x9fb1, old, new)
    return len(code)
