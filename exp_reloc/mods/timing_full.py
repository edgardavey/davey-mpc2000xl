"""Full Timing list (user request 2026-10-22, replaces timing_q4's slot swap): Timing / Note value gets 1/4 and 1/4(3)
as two NEW values; every stock value, 1/32(3) included, keeps its number and its behaviour.

  0 OFF  1 1/8  2 1/8(3)  3 1/16  4 1/16(3)  5 1/32  6 1/32(3)  7 1/4  8 1/4(3)

Stored at the sequencer settings byte 2275:0717 (saved in .ALL files). Every reader found (watchpoints + a scan for
[0717] / es:[si+7] accesses, 2026-10-22) goes through a 9-entry table here instead of its 7-byte stock table:
  0:4DF2     grid in ticks (xlat 0FE7:4833)          -> GRID
  267B:8AAD  grid in ticks (xlat 2275:21F3)          -> GRID
  0:4E20, 0:7F50  swing range ([bx + 0FE7:483A])     -> SWING (swing stays 1/8 and 1/16 only, as stock)
  267B:3480  shift-timing cap (xlat 2275:12D3)       -> CAP (half the grid minus one)
  1A9B:105A  list text (INT 8F list op): the list pointer 2275:0F31 is answered from LIST below; any other list
             is drawn exactly as before
  four field set-ups (mov dx,6 before INT 7D/7E)     -> maximum 8
The stock tables and the stock list are left untouched.
Disk: the setting is saved in .ALL files (the file starts with RAM 2275:0000-0F05), and a stock OS divides by the
grid while recording: a value 7/8 in a file would stop a stock unit with "Error at 0000:5BCD" (measured 2026-10-22).
So .ALL files stay stock-safe:
  SAVE (1A9B-area code at linear 0x1F6C2): the header is written with 1/4 -> 1/8 and 1/4(3) -> 1/8(3), RAM is put back
       right after; before the file is closed (0x1F6E9) an 8-byte trailer "DAVEYTC"+value is appended (1/4, 1/4(3) only)
  LOAD (0x1DA99, after the last sequence): 8 more bytes are read; "DAVEYTC"+7|8 with the matching 1/8|1/8(3) in the
       header restores 1/4 | 1/4(3). A stock OS reads the file as 1/8 | 1/8(3) and never reads the trailer."""
import os, struct, tempfile
from asm16 import assemble

LIN = 0x74a90                 # measured-free range 0x749A4-0x74CB1 (wave_fast ends at 0x74A90)
SEG = LIN >> 4
GRID = [1, 48, 32, 24, 16, 12, 8, 96, 64]          # 96 PPQN
SWING = [0, 24, 0, 12, 0, 0, 0, 0, 0]
CAP = [g // 2 - 1 if g > 1 else 0 for g in GRID]     # stock: 0, 23, 15, 11, 7, 5, 3
NAMES = ['OFF', '1/8', '1/8(3)', '1/16', '1/16(3)', '1/32', '1/32(3)', '1/4', '1/4(3)']
MAXV = len(NAMES) - 1

SRC = r'''
.intel_syntax noprefix
.code16
start:
clamp:                         /* bx = value 0..8 (anything else -> 0 = OFF) */
    mov bh, 0
    cmp bl, %(MAXV)d
    jbe .Lc_ok
    mov bl, 0
.Lc_ok:
    .byte 0xc3
grid0:                         /* 0:4DF2, es:si = settings: al = grid, bx = 0x4833 (as the stock xlat leaves it) */
    mov bl, byte ptr es:[si + 7]
    .byte 0xe8
    .word clamp - . - 2
    mov al, byte ptr cs:[bx + GRID_T]
    mov bx, 0x4833
    .byte 0xcb
swing:                         /* 0:4E20 and 0:7F50: bx = value, al = swing range */
    mov bl, byte ptr es:[si + 7]
    .byte 0xe8
    .word clamp - . - 2
    mov al, byte ptr cs:[bx + SWING_T]
    mov bl, byte ptr es:[si + 7]
    .byte 0xcb
cap:                           /* 267B:3480, ds = 2275: al = shift cap, bx = 0x12D3 */
    mov bl, byte ptr [0x717]
    .byte 0xe8
    .word clamp - . - 2
    mov al, byte ptr cs:[bx + CAP_T]
    mov bx, 0x12d3
    .byte 0xcb
grid2:                         /* 267B:8AAD, ds = 2275: al = grid, bx = 0x21F3 */
    mov bl, byte ptr [0x717]
    .byte 0xe8
    .word clamp - . - 2
    mov al, byte ptr cs:[bx + GRID_T]
    mov bx, 0x21f3
    .byte 0xcb
disp:                          /* 1A9B:105A list op: es = dx = caller ds, es:di = value, es:si = list (width byte + entries) */
    mov al, byte ptr es:[di]
    cmp si, 0x0f31
    jne .Ld_go
    cmp dx, 0x2275
    jne .Ld_go
    mov dx, cs                 /* the Timing list: ours (the stub restores dx and es afterwards) */
    mov si, offset LIST_T
.Ld_go:
    push es
    mov es, dx
    mov ah, byte ptr es:[si]
    pop es
    inc si
    push ax
    mul ah
    add si, ax
    pop ax
    .byte 0xcb
grid_t:
    .byte %(GRID)s
swing_t:
    .byte %(SWING)s
cap_t:
    .byte %(CAP)s
list_t:
    .byte 7
    .ascii "%(LIST)s"

/* ---- .ALL files (ds = 2275 in both routines) ---- */
save_hdr:                      /* replaces 'mov si,0 / mov cx,0F06 / mov bl,9 / int 91' (es = ds): CF as int 91 */
    mov al, byte ptr [0x717]
    mov byte ptr cs:[V_SAVED], al
    cmp al, 7
    jb .Lsh_w
    cmp al, %(MAXV)d
    ja .Lsh_w
    sub al, 6                  /* 1/4 -> 1/8, 1/4(3) -> 1/8(3) in the file */
    mov byte ptr [0x717], al
.Lsh_w:
    mov si, 0
    mov cx, 0x0f06
    mov bl, 9
    int 0x91
    push ax
    mov al, byte ptr cs:[V_SAVED]
    mov byte ptr [0x717], al   /* mov: CF from int 91 survives */
    pop ax
    .byte 0xcb
save_tail:                     /* replaces 'mov bl,0A / int 91 / push cs' before the close */
    pop word ptr cs:[V_RIP]
    pop word ptr cs:[V_RCS]
    push word ptr cs:[V_RCS]   /* the 'push cs' this call replaces */
    push word ptr cs:[V_RCS]
    push word ptr cs:[V_RIP]
    mov al, byte ptr cs:[V_SAVED]
    cmp al, 7
    jb .Lst_close
    cmp al, %(MAXV)d
    ja .Lst_close
    mov byte ptr cs:[TRAIL + 7], al
    push es
    push cs
    pop es
    mov si, offset TRAIL
    mov cx, 8
    mov bl, 9
    int 0x91                   /* a failed trailer write only loses 1/4 on reload */
    pop es
.Lst_close:
    mov byte ptr cs:[V_SAVED], 0
    mov bl, 0x0a
    int 0x91
    .byte 0xcb
load_tail:                     /* replaces 'mov word [0710],0' after the last sequence is read */
    mov word ptr [0x710], 0
    pusha
    push es
    push cs
    pop es
    mov di, offset TBUF
    mov cx, 8
    xor al, al
.Llt_clr:
    mov byte ptr cs:[di], al
    inc di
    loop .Llt_clr
    mov di, offset TBUF
    mov cx, 8
    mov bl, 6
    int 0x91
    jc .Llt_out
    mov si, offset TRAIL
    mov di, offset TBUF
    mov cx, 7
.Llt_cmp:
    mov al, byte ptr cs:[si]
    cmp al, byte ptr cs:[di]
    jne .Llt_out
    inc si
    inc di
    loop .Llt_cmp
    mov al, byte ptr cs:[TBUF + 7]
    cmp al, 7
    jb .Llt_out
    cmp al, %(MAXV)d
    ja .Llt_out
    mov ah, al
    sub ah, 6
    cmp byte ptr [0x717], ah   /* header still says the matching 1/8 | 1/8(3) */
    jne .Llt_out
    mov byte ptr [0x717], al
.Llt_out:
    pop es
    popa
    .byte 0xcb
trail:
    .ascii "DAVEYTC"
    .byte 0
tbuf:
    .byte 0, 0, 0, 0, 0, 0, 0, 0
v_saved:
    .byte 0
    .balign 2, 0
v_rip:
    .word 0
v_rcs:
    .word 0
    .word GRID0, SWING, CAP, GRID2, DISP, SAVE_HDR, SAVE_TAIL, LOAD_TAIL
'''


def source():
    sub = {'MAXV': MAXV, 'GRID': ', '.join(map(str, GRID)), 'SWING': ', '.join(map(str, SWING)), 'CAP': ', '.join(map(str, CAP)),
           'LIST': ''.join(n.ljust(7) for n in NAMES)}
    consts = ''.join(f'.set {n.upper()}, {n} - start\n' for n in ('grid0', 'swing', 'cap', 'grid2', 'disp', 'grid_t', 'swing_t', 'cap_t', 'list_t', 'save_hdr', 'save_tail', 'load_tail', 'trail', 'tbuf', 'v_saved', 'v_rip', 'v_rcs'))
    return (SRC % sub).replace('start:\n', consts + 'start:\n', 1)


def far(off):
    return bytes([0x9a]) + struct.pack('<HH', off, SEG)


def apply(img):
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source())
    code = assemble(p); os.remove(p)
    img.put(LIN, code, 'timing_full')
    grid0, swing, cap, grid2, disp, save_hdr, save_tail, load_tail = struct.unpack('<8H', code[-16:])
    # readers
    img.patch(0x04df2, bytes.fromhex('268a4407' 'bb3348' 'd7'), far(grid0) + b'\x90' * 3)
    for a in (0x04e20, 0x07f50):
        img.patch(a, bytes.fromhex('268a5c07' 'b700' '8a873a48'), far(swing) + b'\x90' * 5)
    img.patch(0x267b0 + 0x3480, bytes.fromhex('a01707' 'bbd312' 'd7'), far(cap) + b'\x90' * 2)
    img.patch(0x267b0 + 0x8aad, bytes.fromhex('a01707' 'bbf321' 'd7'), far(grid2) + b'\x90' * 2)
    # list op 1A9B:105A..106A: push dx / lcall disp / call 07C1 / pop dx / mov es,dx / ret
    old = bytes.fromhex('268a05' '268a24' '46' '50' 'f6e4' '03f0' '58' 'e857f7' 'c3')
    stub = b'\x52' + far(disp) + b'\xe8' + struct.pack('<h', 0x07c1 - (0x1060 + 3)) + b'\x5a\x8e\xc2\xc3'
    img.patch(0x1a9b0 + 0x105a, old, stub + b'\x90' * (len(old) - len(stub)))
    # field maximum: mov cx,ds / mov si,0717 / mov bl,0 / mov bh,n / mov dx,6 / mov di,.. / int 7D|7E
    for a in (0x273fe, 0x29b66, 0x2b996, 0x2f089):
        i = img.d.index(bytes.fromhex('ba0600'), a, a + 12)
        img.patch(i, bytes.fromhex('ba0600'), bytes([0xba, MAXV, 0]))
    # .ALL save / load
    img.patch(0x1f6c2, bytes.fromhex('be0000' 'b9060f' 'b309' 'cd91'), far(save_hdr) + b'\x90' * 5)
    img.patch(0x1f6e9, bytes.fromhex('b30a' 'cd91' '0e'), far(save_tail))
    img.patch(0x1da99, bytes.fromhex('c70610070000'), far(load_tail) + b'\x90')
    return len(code)


if __name__ == '__main__':
    assert len(NAMES) == len(GRID) == len(SWING) == len(CAP) and all(len(n) <= 7 for n in NAMES)
    assert CAP[:7] == [0, 23, 15, 11, 7, 5, 3] and GRID[:7] == [1, 48, 32, 24, 16, 12, 8]    # = the stock tables
    print(source())
