"""Zone chop (prototype): a VU-style chop screen on the TRIM > ZONE page, with native output.

ZONE page, press F3 (ZONE) again: the chop screen opens over the normal ZONE page (waveform, St/End/Zone stay visible and editable).
  F1 BACK  discard, restore the zones found on entry
  F2 EVEN / CLEAN   redo the even split / start the lazy chop over
  F3 16 -> 8 -> 4 -> LAZY   even split, or LAZY: hit a pad to start, tap pads at each slice; the zones follow every tap
  F4 UNDO (LAZY)    take back the last tap
  F5 APPLY keep the chop and open the stock EDIT window (SLICE SOUND, Create new program) -> DO IT makes the sounds and a program
  TRIM page: a pad hit selects the sound on that pad (then plays it as stock); empty pads play the current sound
  F6 PLAY  hold to hear the current slice (WINDOW: keep the chop as plain zones, back to the ZONE page)
Native structures only: zone table ds:0x8e72, count 0xd7dc, current zone 0xd7dd; stock SLICE SOUND creates the sounds and program.
Replaces zone_lazy (both hook the pad event at 0x0a1b).
"""
import os, struct, tempfile
from asm16 import assemble

BASE = 0x100
T_CHOP = BASE + 0x00

SRC = r'''
.intel_syntax noprefix
.code16
.set BASE, 0x100
.set SEGV, @SEG@
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
tbl_chop:
    .byte 1,0,0,0,0
    .byte 0x02
    .word H_BACK, SEGV
    .byte 0x03
    .word H_F2, SEGV
    .byte 0x04
    .word H_MODE, SEGV
    .byte 0x05
    .word H_F4, SEGV
    .byte 0x06
    .word H_APPLY, SEGV
    .byte 0x07
    .word H_PLAY, SEGV
    .byte 0x87
    .word H_PLAYOFF, SEGV
    .byte 0x15
    .word H_DONE, SEGV
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
v_bak:   .fill 74, 1, 0
v_mode:  .byte 0
v_scr:   .byte 0
v_pz:    .byte 0
v_preq:  .byte 0
v_n:     .word 16
v_qh:    .word 0
v_ql:    .word 0
v_r:     .word 0
v_acc:   .word 0
v_dig:   .byte 0
v_dfld:  .word 0
v_lnote: .byte 0xff
v_tpad:  .fill 16, 1, 0xff

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
    push ds
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
    pop ds
    .byte 0xc3

/* ---------- pad hook, far-called from stock 0x0a1b (ds=0xfe7 there) ---------- */
pad_hook:
    pushf
    mov byte ptr cs:[V_LNOTE], al        /* last pad note, for the TRIM pad select (h_tpad) */
    cmp byte ptr cs:[V_SCR], 1
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
    push cx
    cmp byte ptr cs:[V_OPEN], 1          /* LAZY armed? */
    jne .Lph_prev
    cmp byte ptr cs:[V_RUN], 1
    je .Lph_tap
    cmp byte ptr cs:[V_CNT], 0           /* not running, nothing tapped yet: this pad starts the chop */
    je .Lph_req
.Lph_prev:                               /* preview: pad index (ah, 0..15) -> slice ah+1 */
    mov al, ah
    and al, 0x0f
    inc al
    mov byte ptr cs:[V_PZ], al
    mov byte ptr cs:[V_PREQ], 1
    jmp .Lph_end
.Lph_tap:
    mov cl, ah                           /* pad of this tap (all banks) */
    and cl, 0x3f
    mov ax, word ptr [0xb8a]
    sub ax, word ptr cs:[V_T0]
    xor bx, bx
    mov bl, byte ptr cs:[V_CNT]
    cmp ax, word ptr cs:[V_ENDMS]
    jae .Lph_end
    cmp bl, 16
    jae .Lph_end
    xor si, si                           /* each pad cuts only once per run: a pad already used (start pad included) is ignored */
.Lph_chk:
    cmp si, bx
    jae .Lph_new
    cmp byte ptr cs:[si+V_TPAD], cl
    je .Lph_end
    inc si
    jmp .Lph_chk
.Lph_new:
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
    mov byte ptr cs:[si+V_TPAD], cl
    shl si, 1
    mov word ptr cs:[si+V_TAPS], ax
    inc bl
    mov byte ptr cs:[V_CNT], bl
    mov byte ptr cs:[V_DIRTY], 1
    jmp .Lph_end
.Lph_req:
    mov cl, ah                           /* the start pad owns slice 1 */
    and cl, 0x3f
    mov byte ptr cs:[V_TPAD], cl
    mov byte ptr cs:[V_REQ], 1
.Lph_end:
    pop cx
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


/* ---------- entry: F3 (ZONE) pressed again on the ZONE page (table ds:0x27dc is the ZONE page's own); no sound = stock handler ---------- */
h_enter:
    pusha
    push ds
    push es
    mov ax, 0x582b
    mov ds, ax
    mov ax, 0xd71a
    cmp ax, word ptr [0xd7c2]
    jne .Le_ok
    mov ax, ds
    cmp ax, word ptr [0xd7c4]
    je .Le_stock
.Le_ok:
    mov si, 0x8e72
    mov di, offset V_BAK
    mov cx, 36
.Le_bk:
    mov ax, word ptr [si]
    mov word ptr cs:[di], ax
    add si, 2
    add di, 2
    loop .Le_bk
    mov ax, word ptr [0xd7dc]
    mov word ptr cs:[di], ax
    push ds
    FC 0x3e19, 0x39ee
    pop ds
    mov byte ptr cs:[V_RUN], 0
    mov byte ptr cs:[V_CNT], 0
    mov byte ptr cs:[V_REQ], 0
    mov al, byte ptr [0xd7dc]
    mov byte ptr cs:[V_MODE], 0
    mov word ptr cs:[V_N], 16
    cmp al, 16
    je .Le_mode
    mov byte ptr cs:[V_MODE], 1
    mov word ptr cs:[V_N], 8
    cmp al, 8
    je .Le_mode
    mov byte ptr cs:[V_MODE], 2
    mov word ptr cs:[V_N], 4
    cmp al, 4
    je .Le_mode
    mov byte ptr cs:[V_MODE], 3
.Le_mode:
    xor al, al
    cmp byte ptr cs:[V_MODE], 3
    jne .Le_arm
    mov al, 1
.Le_arm:
    mov byte ptr cs:[V_OPEN], al
    mov byte ptr cs:[V_SCR], 1
    DSNOW
    mov word ptr cs:[V_BEAT], ax
    push ds
    push offset T_CHOP_SEG
    push 0
    FC 0x3e19, 0x0724
    add sp, 4
    pop ds
    CALLN redraw
    pop es
    pop ds
    popa
    .byte 0xcb
.Le_stock:
    pop es
    pop ds
    popa
    .byte 0xea
    .word 0xcd38, 0x3e19

/* ds=582b: n even zones (n in V_N), stock layout: entry k = start of zone k, entry n+1 = end: entry(k+1) = floor(len*k/n), by running sums: B += q each step, rem += r, carry 1 when rem >= n */
even_zones:
    les di, dword ptr [0xd7c2]
    mov cx, word ptr cs:[V_N]
    mov ax, word ptr es:[di+0x30]
    xor dx, dx
    div cx
    mov word ptr cs:[V_QH], ax
    mov ax, word ptr es:[di+0x2e]
    div cx
    mov word ptr cs:[V_QL], ax
    mov word ptr cs:[V_R], dx
    mov word ptr cs:[V_ACC], 0
    xor ax, ax
    xor dx, dx
    mov word ptr [0x8e72], ax   /* entry 0 is unused by the stock page */
    mov word ptr [0x8e74], ax
    mov bx, 0x8e76              /* entry 1 = start of zone 1 = 0 */
    mov word ptr [bx], ax
    mov word ptr [bx+2], dx
    mov cx, word ptr cs:[V_N]   /* n steps */
.Lev_loop:
    add bx, 4
    add ax, word ptr cs:[V_QL]
    adc dx, word ptr cs:[V_QH]
    push ax
    mov ax, word ptr cs:[V_ACC]
    add ax, word ptr cs:[V_R]
    cmp ax, word ptr cs:[V_N]
    jb .Lev_nc
    sub ax, word ptr cs:[V_N]
    mov word ptr cs:[V_ACC], ax
    pop ax
    add ax, 1
    adc dx, 0
    jmp .Lev_st
.Lev_nc:
    mov word ptr cs:[V_ACC], ax
    pop ax
.Lev_st:
    mov word ptr [bx], ax
    mov word ptr [bx+2], dx
    loop .Lev_loop
    mov ax, word ptr cs:[V_N]
    mov byte ptr [0xd7dc], al
    mov byte ptr [0xd7dd], 1
    .byte 0xc3

/* ds=582b: one zone over the whole sound */
one_zone:
    les di, dword ptr [0xd7c2]
    xor ax, ax
    mov word ptr [0x8e72], ax
    mov word ptr [0x8e74], ax
    mov word ptr [0x8e76], ax
    mov word ptr [0x8e78], ax
    mov ax, word ptr es:[di+0x2e]
    mov word ptr [0x8e7a], ax
    mov ax, word ptr es:[di+0x30]
    mov word ptr [0x8e7c], ax
    mov byte ptr [0xd7dc], 1
    mov byte ptr [0xd7dd], 1
    .byte 0xc3

redraw:
    push ds
    mov ax, 0xfe7
    mov ds, ax
    mov byte ptr [0x63], 1
    pop ds
    .byte 0xc3

/* ds=582b: play the current zone (entry k .. entry k+1) of the current sound */
play_zone:
    push ds
    les di, dword ptr [0xd7c2]
    mov bl, byte ptr [0xd7dd]
    xor bh, bh
    shl bx, 2
    mov ax, word ptr [bx+0x8e72]
    mov dx, word ptr [bx+0x8e74]
    mov cx, word ptr [bx+0x8e76]
    mov si, word ptr [bx+0x8e78]
    sub cx, ax
    sbb si, dx
    jb .Lpz_out                          /* end before start: nothing to play */
    mov bx, cx
    or bx, si
    jz .Lpz_out                          /* empty zone */
    push 0x7f
    push si
    push cx
    push dx
    push ax
    push es
    push di
    FC 0x3e19, 0x3d2c
    add sp, 14
.Lpz_out:
    pop ds
    .byte 0xc3

stop_all:
    push ds
    FC 0x3e19, 0x39ee
    pop ds
    mov byte ptr cs:[V_RUN], 0
    .byte 0xc3

/* apply the current mode: 0/1/2 = 16/8/4 even zones, 3 = LAZY (one zone, pads armed) */
set_mode:
    CALLN stop_all
    mov byte ptr cs:[V_CNT], 0
    mov byte ptr cs:[V_REQ], 0
    cmp byte ptr cs:[V_MODE], 3
    je .Lsm_lazy
    mov byte ptr cs:[V_OPEN], 0
    mov bl, byte ptr cs:[V_MODE]
    xor bh, bh
    mov al, byte ptr cs:[bx+NTAB]
    xor ah, ah
    mov word ptr cs:[V_N], ax
    CALLN even_zones
    jmp redraw
.Lsm_lazy:
    CALLN one_zone
    DSNOW
    mov word ptr cs:[V_BEAT], ax
    mov byte ptr cs:[V_OPEN], 1
    jmp redraw
ntab: .byte 16, 8, 4

h_mode:
    ENTER
    mov al, byte ptr cs:[V_MODE]
    inc al
    and al, 3
    mov byte ptr cs:[V_MODE], al
    CALLN set_mode
    LEAVE

h_f2:                               /* EVEN (even modes: redo the split) / CLEAN (LAZY: start over) */
    ENTER
    CALLN set_mode
    LEAVE

h_f4:                               /* LAZY: UNDO the last tap */
    ENTER
    cmp byte ptr cs:[V_MODE], 3
    jne .Lf4_out
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
    push ds
    FC 0x3e19, 0x39ee
    pop ds
    pop ax
    mov byte ptr cs:[V_RUN], 0
    CALLN sp_start
    mov byte ptr cs:[V_DIRTY], 1
.Lu_out:
    jmp .Lf4_out

.Lf4_out:
    LEAVE

leave_chop:                         /* stop, disarm, keep a finished LAZY chop, back to the ZONE page */
    CALLN stop_all
    mov byte ptr cs:[V_OPEN], 0
    mov byte ptr cs:[V_SCR], 0
    cmp byte ptr cs:[V_MODE], 3
    jne .Llc_page
    cmp byte ptr cs:[V_CNT], 0
    je .Llc_page
    CALLN build_zones
.Llc_page:
    mov byte ptr [0xd7dd], 1
    push ds
    FC 0x3e19, 0xf1dc
    pop ds
    .byte 0xc3

h_done:                             /* WINDOW: leave, keep the chop as plain zones */
    ENTER
    CALLN leave_chop
    LEAVE

h_play:                             /* F6 held: play the current slice (as F6 PLAY X on the stock ZONE page) */
    ENTER
    CALLN stop_all
    CALLN play_zone
    LEAVE

h_playoff:                          /* F6 released */
    ENTER
    CALLN stop_all
    LEAVE

h_apply:                            /* keep the chop and open the stock Edit window exactly as F5 EDIT on the ZONE page does */
    ENTER
    CALLN leave_chop
    push ds
    FC 0x3e19, 0xf22a          /* the ZONE page's own F5 EDIT handler (table ds:0x2804, event 0x06): stock Edit window, SLICE SOUND */
    pop ds
    LEAVE

h_back:                             /* discard: restore the zones found on entry */
    ENTER
    CALLN stop_all
    mov byte ptr cs:[V_OPEN], 0
    mov byte ptr cs:[V_SCR], 0
    mov si, offset V_BAK
    mov di, 0x8e72
    mov cx, 36
.Lb_rs:
    mov ax, word ptr cs:[si]
    mov word ptr [di], ax
    add si, 2
    add di, 2
    loop .Lb_rs
    mov ax, word ptr cs:[si]
    mov word ptr [0xd7dc], ax
    push ds
    FC 0x3e19, 0xf1dc
    pop ds
    LEAVE

/* TRIM page, pad (event 0x37, al = velocity, ah = pad): select the sound on that pad, then play as stock.
   track drum (fe7:[430a]:[4854] + 0x5c0, 1..4) -> program (vector 0x5c + drum-1) -> sound of the last pad note (prog + 0x7de + 4*(note-35)).
   No sound on the pad, a release, or anything unexpected: plain stock behaviour (3e19:cd8e plays the current sound). */
h_tpad:
    ENTER
    or al, al
    je .Ltp_stock
    mov bx, 0xfe7
    mov es, bx
    mov di, word ptr es:[0x4854]
    mov es, word ptr es:[0x430a]
    mov bl, byte ptr es:[di+0x5c0]
    dec bl
    cmp bl, 3
    ja .Ltp_stock
    xor bh, bh
    add bx, 0x5c
    shl bx, 2
    xor cx, cx
    mov es, cx
    les si, dword ptr es:[bx]
    mov cx, es
    or cx, si
    je .Ltp_stock
    mov bl, byte ptr cs:[V_LNOTE]
    sub bl, 35
    cmp bl, 63
    ja .Ltp_stock
    xor bh, bh
    shl bx, 2
    mov ax, word ptr es:[si+bx+0x7de]
    mov dx, word ptr es:[si+bx+0x7e0]
    mov cx, ax
    or cx, dx
    je .Ltp_stock
    cmp ax, word ptr [0xd7c2]
    jne .Ltp_set
    cmp dx, word ptr [0xd7c4]
    je .Ltp_stock
.Ltp_set:
    mov word ptr [0xd7c2], ax
    mov word ptr [0xd7c4], dx
    push ds
    push dx
    push ax
    FC 0x3e19, 0xbfe6          /* the TRIM Snd field's own change callback (field record ds:0x1802 +0x22), as the stock field code calls it */
    add sp, 4
    pop ds
    push ds
    mov ax, 0xfe7
    mov ds, ax
    mov byte ptr [0x63], 1     /* full page redraw (as the sampling close fix) */
    pop ds
.Ltp_stock:
    pop es
    pop ds
    popa
    .byte 0xea                 /* jmp far 3e19:cd8e with the original registers (stock pad handler, returns to our caller) */
    .word 0xcd8e, 0x3e19

h_tick:
    ENTER
    push ds
    FC 0x4e16, 0x9ec4          /* the stock ZONE tick's only job: next step of the waveform calculation (it froze in the chop screen) */
    pop ds
    DSNOW
    mov word ptr cs:[V_BEAT], ax
    cmp byte ptr cs:[V_RUN], 1           /* lazy playback reached the end of the sound: tapping is over */
    jne .Lt_prev
    sub ax, word ptr cs:[V_T0]
    cmp ax, word ptr cs:[V_ENDMS]
    jb .Lt_prev
    mov byte ptr cs:[V_RUN], 0
    mov byte ptr cs:[V_DIRTY], 1
.Lt_prev:
    cmp byte ptr cs:[V_PREQ], 1
    jne .Lt_req0
    mov byte ptr cs:[V_PREQ], 0
    mov al, byte ptr cs:[V_PZ]
    cmp al, byte ptr [0xd7dc]
    ja .Lt_req0
    mov byte ptr [0xd7dd], al
    CALLN stop_all
    CALLN play_zone
    CALLN redraw
.Lt_req0:
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
    je .Lt_rd
    CALLN build_zones
    mov al, byte ptr [0xd7dc]
    mov byte ptr [0xd7dd], al
.Lt_rd:
    CALLN redraw
.Lt_out:
    LEAVE

/* ---------- screen: the stock ZONE page, then our header line and soft keys ---------- */
h_draw:
    ENTER
    mov al, byte ptr [0x8b2e]          /* SHIFT+cursor digit step of the focused field: the focus routines below reset it */
    mov byte ptr cs:[V_DIG], al
    mov ax, word ptr [0x8d58]
    mov word ptr cs:[V_DFLD], ax
    push word ptr [0x8d58]             /* field under the cursor */
    push ds
    FC 0x3e19, 0xf440          /* stock ZONE subpage refresh: cached St/End of the current zone (selects field 2) */
    pop ds
    pop bx
    cmp bx, 3                          /* only End (3) and Zone (4) are kept; anything else stays on St (2) */
    jb .Ld_fld
    cmp bx, 4
    ja .Ld_fld
    mov word ptr [0x8d58], bx          /* put the cursor back and let that field register itself */
    imul bx, bx, 0x2a
    push ds
    .byte 0xff, 0x9f, 0x86, 0x28       /* lcall [bx+0x2886]: the field's own focus routine */
    pop ds
.Ld_fld:
    mov ax, word ptr [0x8d58]          /* same field as before the redraw: give the digit step back */
    cmp ax, word ptr cs:[V_DFLD]
    jne .Ld_nodig
    mov al, byte ptr cs:[V_DIG]
    mov byte ptr [0x8b2e], al
.Ld_nodig:
    push ds
    FC 0x3e19, 0xf2cc          /* stock page draw: header, St/End/Zone, waveform with the current zone */
    pop ds
    int 0x8f
    .byte 0x14, 0, 0, 248, 9    /* clear the header row */
    mov al, byte ptr [0xd7dc]
    xor ah, ah
    mov cl, 10
    div cl
    add ax, 0x3030
    mov word ptr cs:[S_HDR+18], ax
    mov al, byte ptr cs:[V_CNT]
    xor ah, ah
    div cl
    add ax, 0x3030
    mov word ptr cs:[S_HDR+28], ax
    int 0x8f
    .byte 5, 0, 1
s_hdr:
    .asciz "ZONE CHOP   Zones:00   Taps:00         "
    int 0x8f
    .byte 0x19, 1, 1
    .asciz "BACK"
    cmp byte ptr cs:[V_MODE], 3
    je .Ld_lz
    int 0x8f
    .byte 0x19, 2, 1
    .asciz "EVEN"
    int 0x8f
    .byte 0x19, 4, 1
    .asciz " "
    cmp byte ptr cs:[V_MODE], 1
    je .Ld_8
    ja .Ld_4
    int 0x8f
    .byte 0x19, 3, 2
    .asciz "16"
    jmp .Ld_tail
.Ld_8:
    int 0x8f
    .byte 0x19, 3, 2
    .asciz "8"
    jmp .Ld_tail
.Ld_4:
    int 0x8f
    .byte 0x19, 3, 2
    .asciz "4"
    jmp .Ld_tail
.Ld_lz:
    int 0x8f
    .byte 0x19, 2, 1
    .asciz "CLEAN"
    int 0x8f
    .byte 0x19, 3, 2
    .asciz "LAZY"
    int 0x8f
    .byte 0x19, 4, 1
    .asciz "UNDO"
.Ld_tail:
    int 0x8f
    .byte 0x19, 5, 1
    .asciz "APPLY"
    int 0x8f
    .byte 0x19, 6, 1
    .asciz "PLAY"
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
    .word H_TPAD
    .word PAD_HOOK
    .word H_ENTER
'''

LABELS = ['v_endms','v_open','v_run','v_cnt','v_req','v_dirty','v_t0','v_beat','v_len','v_rate','v_prev','v_taps','v_bak','v_mode','v_n',
          'h_enter','h_back','h_f2','h_mode','h_f4','h_apply','h_done','h_play','h_playoff','h_draw','h_tick','pad_hook','s_hdr','ntab','v_qh','v_ql','v_r','v_acc','v_scr','v_pz','v_preq','v_dig','v_dfld','v_lnote','h_tpad','v_tpad']

def source(seg):
    consts = ''.join(f'.set {l.upper()}, {l} - start + BASE\n' for l in LABELS)
    consts += '.set T_CHOP_SEG, %d\n' % ((seg * 16 + T_CHOP) >> 4)
    return SRC.replace('.set SEGV, @SEG@\n', '.set SEGV, %d\n' % seg + consts, 1)

def apply(img, lin):
    """place the module at linear `lin` (code starts there), segment = (lin - BASE) / 16"""
    assert (lin - BASE) % 16 == 0
    seg = (lin - BASE) >> 4
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source(seg))
    code = assemble(p); os.remove(p)
    img.put(lin, code, 'zone_chop')
    tpad, pad, enter = struct.unpack('<HHH', code[-6:])
    # 1) pad events: stock `mov es,[430a]; mov di,[4854]` at 0x0a1b -> far call to pad_hook (+3 nops)
    img.patch(0x0a1b, bytes.fromhex('8e060a438b3e5448'), bytes([0x9a]) + struct.pack('<HH', pad, seg) + b'\x90\x90\x90')
    # 2) ZONE page key table (ds:0x27dc), event 0x04 (F3): 3e19:cd38 -> h_enter (falls back to cd38 when there is no sound)
    img.patch(0x582b0 + 0x27dc + 5 + 2 * 5, bytes.fromhex('0438cd193e'), bytes([0x04]) + struct.pack('<HH', enter, seg))
    # 3) TRIM page key table (ds:0x178e), event 0x37 (pads): 3e19:cd8e -> h_tpad (pad selects its sound, then plays as stock)
    img.patch(0x582b0 + 0x17a7, bytes.fromhex('378ecd193e'), bytes([0x37]) + struct.pack('<HH', tpad, seg))
    return len(code)
