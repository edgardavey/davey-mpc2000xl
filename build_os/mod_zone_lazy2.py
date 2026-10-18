"""Zone lazy chop v2 (prototype): same entry as zone_lazy, but no window covers the ZONE page: a one-line strip shows the tap count,
the zone table is rebuilt on every tap so the waveform highlight follows the chop, CLOSE restores the zones it found.

Zone lazy chop: TRIM > ZONE > OPEN WINDOW on "Zone:" gets an F6 LAZY button.

Play the sample, tap pads where each slice should start; DO IT writes the taps into the stock zone table
(so the stock SLICE SOUND turns them into pads). Written against the stock OS interfaces only:
  - zone table at ds:0x8e72 (B[0]=0, B[k]=start of zone k, B[n+1]=sound length), count ds:0xd7dc, current zone ds:0xd7dd
  - current sound far pointer ds:0xd7c2 (length dword at +0x2e, sample rate word at +0x38)
  - stock services: 3e19:0724 register window events, 3e19:0bd4 window frame, 3e19:3d2c play a range,
    3e19:39ee stop all voices, 3e19:f1dc redraw the zone page, int 0x8f inline text/labels
  - millisecond counter 0xfe7:0xb8a
"""
import os, struct, tempfile
from asm16 import assemble

BASE = 0x100            # module offset inside the 0x7000 segment (16-byte aligned, > 0x7f so disp16 is always used)
SEG = 0x7000
T_ZONE = BASE + 0x00    # event tables are paragraph aligned so they can be addressed as seg:0
T_LAZY = BASE + 0x30

SRC = r'''
.intel_syntax noprefix
.code16
.set BASE, %(BASE)d
.set SEGV, 0x7000
.macro FC seg, off
    .byte 0x9a
    .word \off, \seg
.endm
.macro CALLN target
    .byte 0xe8
    .word \target - . - 2
.endm
.macro ENTER
    pusha
    push ds
    push es
    mov ax, 0x582b
    mov ds, ax
.endm
.macro LEAVE
    pop es
    pop ds
    popa
    .byte 0xcb
.endm
.macro DSNOW         /* ax = millisecond counter */
    push ds
    mov ax, 0xfe7
    mov ds, ax
    mov ax, word ptr [0xb8a]
    pop ds
.endm

start:
tbl_zone:
    .byte 1,0,0,0,0
    .byte 0x05
    .word 0xf9d2, 0x3e19
    .byte 0x06
    .word 0xf9e0, 0x3e19
    .byte 0x32
    .word H_ZDRAW, SEGV
    .byte 0x15
    .word 0xf9d2, 0x3e19
    .byte 0x07
    .word H_ZOPEN, SEGV
    .byte 0,0,0,0,0
    .balign 16, 0
tbl_lazy:
    .byte 1,0,0,0,0
    .byte 0x04
    .word H_UNDO, SEGV
    .byte 0x05
    .word H_CLOSE, SEGV
    .byte 0x06
    .word H_DOIT, SEGV
    .byte 0x07
    .word H_PLAY, SEGV
    .byte 0x15
    .word H_CLOSE, SEGV
    .byte 0x32
    .word H_DRAW, SEGV
    .byte 0x33
    .word H_TICK, SEGV
    .byte 0,0,0,0,0
    .balign 16, 0

/* ---------- state (lives in this segment; the OS image runs from RAM) ---------- */
v_open:  .byte 0
v_run:   .byte 0
v_cnt:   .byte 0
v_req:   .byte 0
v_dirty: .byte 0
v_pad:   .byte 0
v_t0:    .word 0
v_endms: .word 0xffff
v_beat:  .word 0
v_len:   .long 0
v_rate:  .word 0
v_prev:  .long 0
v_taps:  .fill 16, 2, 0
v_bak:   .fill 70, 1, 0

/* ms (ax) * rate (bx) / 1000 -> dx:ax */
conv:
    mul bx
    mov bx, ax
    mov ax, dx
    xor dx, dx
    mov cx, 1000
    div cx
    xchg ax, bx
    div cx
    mov dx, bx
    .byte 0xc3

/* es:di = sound -> ax = length in ms (capped at 65535) */
calc_endms:
    mov ax, word ptr es:[di+0x2e]
    mov dx, word ptr es:[di+0x30]
    mov bx, word ptr es:[di+0x38]
    or bx, bx
    je .Lce_cap
    cmp dx, bx
    jae .Lce_cap
    div bx
    mov si, dx
    mov cx, 1000
    mul cx
    or dx, dx
    jne .Lce_cap
    push ax
    mov ax, si
    mul cx
    div bx
    pop cx
    add ax, cx
    jc .Lce_cap
    .byte 0xc3
.Lce_cap:
    mov ax, 0xffff
    .byte 0xc3

/* ds=582b. Play the current sound from offset ax (ms); t0 = now - offset; run=1 */
sp_start:
    push ax
    les di, dword ptr [0xd7c2]
    CALLN calc_endms
    mov word ptr cs:[V_ENDMS], ax
    mov bx, sp
    mov ax, word ptr ss:[bx]
    mov bx, word ptr es:[di+0x38]
    CALLN conv
    mov cx, word ptr es:[di+0x2e]
    mov si, word ptr es:[di+0x30]
    sub cx, ax
    sbb si, dx
    jb .Lsp_done
    push 0x7f
    push si
    push cx
    push dx
    push ax
    push es
    push di
    DSNOW
    mov bx, sp
    sub ax, word ptr ss:[bx+14]
    mov word ptr cs:[V_T0], ax
    FC 0x3e19, 0x3d2c
    add sp, 14
    mov byte ptr cs:[V_RUN], 1
.Lsp_done:
    add sp, 2
    .byte 0xc3

/* ---------- pad hook, far-called from stock 0x0a1b (ds=0xfe7 there) ---------- */
pad_hook:
    pushf
    cmp byte ptr cs:[V_OPEN], 1
    jne .Lph_pass
    or cl, cl
    je .Lph_pass
    push ax
    mov ax, word ptr [0xb8a]
    sub ax, word ptr cs:[V_BEAT]
    cmp ax, 300
    pop ax
    ja .Lph_pass
    push ax
    push bx
    push si
    cmp byte ptr cs:[V_RUN], 1
    jne .Lph_req
    mov ax, word ptr [0xb8a]
    sub ax, word ptr cs:[V_T0]
    xor bx, bx
    mov bl, byte ptr cs:[V_CNT]
    cmp ax, word ptr cs:[V_ENDMS]
    jae .Lph_end
    cmp bl, 16
    jae .Lph_end
    or bl, bl
    je .Lph_store
    mov si, bx
    dec si
    shl si, 1
    mov si, word ptr cs:[si+V_TAPS]
    push ax
    sub ax, si
    cmp ax, 25
    pop ax
    jb .Lph_end
.Lph_store:
    mov si, bx
    shl si, 1
    mov word ptr cs:[si+V_TAPS], ax
    inc bl
    mov byte ptr cs:[V_CNT], bl
    mov byte ptr cs:[V_DIRTY], 1
    jmp .Lph_end
.Lph_req:
    mov byte ptr cs:[V_REQ], 1
.Lph_end:
    pop si
    pop bx
    pop ax
    popf
    add sp, 4
    .byte 0xea
    .word 0x0a1a, 0x0000
.Lph_pass:
    popf
    mov es, word ptr [0x430a]
    mov di, word ptr [0x4854]
    .byte 0xcb

/* ---------- zone window: draw (adds LAZY on F6) and open ---------- */
h_zdraw:
    push ds
    mov ax, 0x582b
    mov ds, ax
    FC 0x3e19, 0xf994
    int 0x8f
    .byte 0x19, 6, 1
    .asciz "LAZY"
    pop ds
    .byte 0xcb

h_zopen:
    ENTER
    mov ax, 0xd71a
    cmp ax, word ptr [0xd7c2]
    jne .Lzo_ok
    mov ax, ds
    cmp ax, word ptr [0xd7c4]
    je .Lzo_out
.Lzo_ok:
    mov byte ptr cs:[V_RUN], 0
    mov byte ptr cs:[V_CNT], 0
    mov byte ptr cs:[V_REQ], 0
    mov byte ptr cs:[V_DIRTY], 0
    DSNOW
    mov word ptr cs:[V_BEAT], ax
    mov byte ptr cs:[V_OPEN], 1
    push ds
    pop es
    mov si, 0x8e72
    mov di, V_BAK
    mov cx, 34
.Lzo_bk:
    mov ax, word ptr [si]
    mov word ptr cs:[di], ax
    add si, 2
    add di, 2
    loop .Lzo_bk
    mov ax, word ptr [0xd7dc]
    mov word ptr cs:[di], ax
    FC 0x3e19, 0xf9d2          /* close the stock "Number of zones" window first: the ZONE page is what shows underneath */
    push %(SEG_LAZY)d
    push 0
    FC 0x3e19, 0x0724
    add sp, 4
.Lzo_out:
    LEAVE

/* ---------- lazy chop window ---------- */
h_draw:
    ENTER
    mov al, byte ptr cs:[V_CNT]
    xor ah, ah
    mov cl, 10
    div cl
    add al, 0x30
    add ah, 0x30
    mov byte ptr cs:[S_DIG], al
    mov byte ptr cs:[S_DIG+1], ah
    FC 0x3e19, 0xf2cc          /* draw the ZONE page itself (header, St/End/Zone, waveform with the current zone) */
    int 0x8f
    .byte 5, 0, 1
s_line3:
    .asciz "LAZY Taps:00  pad/PLAY starts, tap=slice "
    int 0x8f
    .byte 0x19, 1, 1
    .asciz " "
    int 0x8f
    .byte 0x19, 2, 1
    .asciz " "
    int 0x8f
    .byte 0x19, 3, 1
    .asciz "UNDO"
    int 0x8f
    .byte 0x19, 4, 2
    .asciz "CLOSE"
    int 0x8f
    .byte 0x19, 5, 1
    .asciz "DO IT"
    int 0x8f
    .byte 0x19, 6, 1
    .asciz "PLAY"
    LEAVE
s_title:
    .asciz "Lazy chop"

h_tick:
    ENTER
    DSNOW
    mov word ptr cs:[V_BEAT], ax
    cmp byte ptr cs:[V_REQ], 1
    jne .Lt_dirty
    mov byte ptr cs:[V_REQ], 0
    cmp byte ptr cs:[V_RUN], 1
    je .Lt_dirty
    xor ax, ax
    CALLN sp_start
    cmp byte ptr cs:[V_RUN], 1
    jne .Lt_dirty
    mov byte ptr cs:[V_CNT], 1
    mov word ptr cs:[V_TAPS], 0
    mov byte ptr cs:[V_DIRTY], 1
.Lt_dirty:
    cmp byte ptr cs:[V_DIRTY], 1
    jne .Lt_out
    mov byte ptr cs:[V_DIRTY], 0
    cmp byte ptr cs:[V_CNT], 0
    je .Lt_redraw
    CALLN build_zones
    mov al, byte ptr [0xd7dc]
    mov byte ptr [0xd7dd], al
.Lt_redraw:
    push ds
    mov ax, 0xfe7
    mov ds, ax
    mov byte ptr [0x63], 1
    pop ds
.Lt_out:
    LEAVE

h_play:
    ENTER
    FC 0x3e19, 0x39ee
    mov byte ptr cs:[V_RUN], 0
    mov byte ptr cs:[V_CNT], 0
    xor ax, ax
    CALLN sp_start
    mov byte ptr cs:[V_DIRTY], 1
    LEAVE

h_undo:
    ENTER
    mov al, byte ptr cs:[V_CNT]
    or al, al
    je .Lu_out
    dec al
    mov byte ptr cs:[V_CNT], al
    xor bx, bx
    xor ax, ax
    mov bl, byte ptr cs:[V_CNT]
    or bl, bl
    je .Lu_go
    dec bx
    shl bx, 1
    mov ax, word ptr cs:[bx+V_TAPS]
.Lu_go:
    push ax
    FC 0x3e19, 0x39ee
    pop ax
    mov byte ptr cs:[V_RUN], 0
    CALLN sp_start
    mov byte ptr cs:[V_DIRTY], 1
.Lu_out:
    LEAVE

h_close:
    ENTER
    FC 0x3e19, 0x39ee
    mov byte ptr cs:[V_RUN], 0
    mov byte ptr cs:[V_OPEN], 0
    mov si, V_BAK
    mov di, 0x8e72
    mov cx, 34
.Lc_rs:
    mov ax, word ptr cs:[si]
    mov word ptr [di], ax
    add si, 2
    add di, 2
    loop .Lc_rs
    mov ax, word ptr cs:[si]
    mov word ptr [0xd7dc], ax
    FC 0x3e19, 0xf1dc
    LEAVE

h_doit:
    ENTER
    FC 0x3e19, 0x39ee
    mov byte ptr cs:[V_RUN], 0
    mov byte ptr cs:[V_OPEN], 0
    CALLN build_zones
    mov byte ptr [0xd7dd], 1
    FC 0x3e19, 0xf1dc
    LEAVE

/* ds=582b: zone table from the taps so far (B[0]=0 .. B[n]=length), count at d7dc */
build_zones:
    les di, dword ptr [0xd7c2]
    mov ax, word ptr es:[di+0x2e]
    mov word ptr cs:[V_LEN], ax
    mov ax, word ptr es:[di+0x30]
    mov word ptr cs:[V_LEN+2], ax
    mov ax, word ptr es:[di+0x38]
    mov word ptr cs:[V_RATE], ax
    xor ax, ax
    mov word ptr [0x8e72], ax
    mov word ptr [0x8e74], ax
    mov word ptr cs:[V_PREV], ax
    mov word ptr cs:[V_PREV+2], ax
    mov bx, 0x8e76
    xor si, si
    xor bp, bp
.Ld_loop:
    mov al, byte ptr cs:[V_CNT]
    xor ah, ah
    cmp si, ax
    jae .Ld_end
    mov di, si
    shl di, 1
    mov ax, word ptr cs:[di+V_TAPS]
    push bx
    mov bx, word ptr cs:[V_RATE]
    CALLN conv
    pop bx
    cmp dx, word ptr cs:[V_LEN+2]
    ja .Ld_end
    jb .Ld_inrange
    cmp ax, word ptr cs:[V_LEN]
    jae .Ld_end
.Ld_inrange:
    or bp, bp
    je .Ld_take
    cmp dx, word ptr cs:[V_PREV+2]
    jb .Ld_skip
    ja .Ld_take
    cmp ax, word ptr cs:[V_PREV]
    jbe .Ld_skip
.Ld_take:
    mov word ptr [bx], ax
    mov word ptr [bx+2], dx
    mov word ptr cs:[V_PREV], ax
    mov word ptr cs:[V_PREV+2], dx
    add bx, 4
    inc bp
.Ld_skip:
    inc si
    jmp .Ld_loop
.Ld_end:
    or bp, bp
    jne .Ld_have
    mov word ptr [bx], 0
    mov word ptr [bx+2], 0
    add bx, 4
    inc bp
.Ld_have:
    mov ax, word ptr cs:[V_LEN]
    mov word ptr [bx], ax
    mov ax, word ptr cs:[V_LEN+2]
    mov word ptr [bx+2], ax
    mov ax, bp
    mov byte ptr [0xd7dc], al
    .byte 0xc3
    .balign 2, 0
    .word PAD_HOOK
'''

LABELS = ['v_endms','v_open','v_run','v_cnt','v_req','v_dirty','v_t0','v_beat','v_len','v_rate','v_prev','v_taps',
          'h_zdraw','h_zopen','h_draw','h_tick','h_play','h_undo','h_close','h_doit','pad_hook','s_title','s_line3','v_bak']

def source():
    consts = ''.join(f'.set {l.upper()}, {l} - start + BASE\n' for l in LABELS)
    consts += '.set S_DIG, s_line3 - start + BASE + 10\n'
    src = SRC % {'BASE': BASE, 'SEG_LAZY': (0x70000 + T_LAZY) >> 4}
    # constants must be defined before use: place right after .set BASE line
    return src.replace('.set SEGV, 0x7000\n', '.set SEGV, 0x7000\n' + consts, 1)

def apply(img):
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source())
    code = assemble(p); os.remove(p)
    assert BASE >= img.next, 'module offset collides'
    img.next = BASE
    off = img.place(code, align=16)
    assert off == BASE
    # --- locate entry points by assembling symbol offsets: recompute from labels via a second tiny pass is avoided;
    # entry offsets are exported by the assembler through the constants table below (parsed from the source order).
    pad = struct.unpack('<H', code[-2:])[0]
    # 1) "Number of zones" window: use our event table (stock one + F6 LAZY)
    img.patch(0x4db0c, bytes.fromhex('1e68ec2a90'), bytes([0x68]) + struct.pack('<H', (0x70000 + T_ZONE) >> 4) + bytes([0x6a, 0x00]))
    # 2) pad events: stock `mov es,[430a]; mov di,[4854]` at 0x0a1b -> far call to pad_hook (+3 nops)
    img.patch(0x0a1b, bytes.fromhex('8e060a438b3e5448'), bytes([0x9a]) + struct.pack('<HH', pad, SEG) + b'\x90\x90\x90')
