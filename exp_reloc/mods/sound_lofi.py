"""Sampling Mode on any sound (user request 2026-10-23, EXP14): TRIM > F5 EDIT gets four entries after the stock list
    SP1200 > NEW SOUND   S900 > NEW SOUND   (copy named in 'New name:', processed; the original is untouched)
    SP1200 > REPLACE     S900 > REPLACE     (the current sound itself, no undo, like stock REVERSE)
The processing is vubeatz's Sampling Mode code (module 'sampling', block 7762): entry 7762:019D processes the sound
whose header is at far [8B4A] in place, with its own "processing" box; its mode/rate (cs:0730/0736) are set for the
call and put back, so the SAMPLE page setting for recordings does not change.

Stock Edit window (all ds = 582B), index [8D4C], list = far ptrs at 25DC (0..8; 8 = SLICE SOUND, ZONE only):
our entries are effective indexes E 9..12. On TRIM the list max is 7 and index 8+ maps to E = index + 1 (skipping
SLICE); on ZONE the max is 8 and E = index.
  3E19:EF8E/EF94  list max 8/7 -> 12/11; from TRIM the window always opens at DISCARD (stock, 3E19:EB43)
  3E19:ED82       list text  (push far [E*4+25DC])           -> name_push
  3E19:ED9D       per-entry drawing (switch on E, 0..8)       -> draw_sel: NEW = SECTION's 'New name:', REPLACE = REVERSE's text
  3E19:EFB0       per-entry cursor fields (same switch)       -> fld_sel
  3E19:EC15       DO IT (switch on E, > 7 = SLICE)            -> doit_sel: ours run here and leave through the stock tail
                  3E19:ED0A (error box / select the result [98AA] / waveform cache / redraw)
  3E19:ED52       end of every DO IT: back to the page, then (NEW SOUND only) the stock KEEP or RETRY window
                  (3E19:BA9C): 'Name for new sound', hit a pad = 'Assign to note', KEEP/RETRY/PLAY
  3E19:BB77/BB0E  KEEP/RETRY exits -> back to TRIM/ZONE ([8D52]) instead of the SAMPLE page, only when opened here
  3E19:A8B0       the recording path's call of BA9C clears that flag (a real recording's KEEP stays stock)"""
import os, struct, tempfile
from asm16 import assemble

LIN = 0x75e60                 # unit A: measured-free range 0x75CE6-0x761E1 (after prog_mono 0x75E00-0x75E4F)
SEG = LIN >> 4
LIN_B = 0x76300               # unit B (Edit window drawing: Sound / Rate rows), measured-free 0x762FD-0x76540
SEG_B = LIN_B >> 4
LIN_C = 0x76dd0               # unit C (Rate field, Edit window pad event, window record), measured-free 0x76DCB-0x77000
SEG_C = LIN_C >> 4
RATES = (8000, 11025, 12000, 16000, 18000, 20000, 22050, 24000, 26040, 28000, 30000, 32000, 36000, 40000, 44100)
SP1200, S900 = 26040, 30000   # target rates for 44.1 kHz sounds (VU's presets)

SRC = r'''
.intel_syntax noprefix
.code16
.macro FC seg, off
    .byte 0x9a
    .word \off, \seg
.endm
start:
eff:                           /* ax = effective entry E from [8D4C] (ds = 582B) */
    mov ax, word ptr [0x8d4c]
    cmp ax, 8
    jb .Le_out
    cmp word ptr [0x8d52], 0xf1dc /* opened from ZONE (SLICE SOUND listed)? */
    jne .Le_trim
    cmp word ptr [0x8d54], 0x3e19
    je .Le_out
.Le_trim:
    inc ax
.Le_out:
    .byte 0xc3
mapped:                        /* ax = the stock entry whose screen ours borrow: NEW -> 2 SECTION, REPLACE -> 6 REVERSE */
    .byte 0xe8
    .word eff - . - 2
    cmp ax, 9
    jb .Lm_out
    cmp ax, 11
    mov ax, 2
    jb .Lm_out
    mov ax, 6
.Lm_out:
    .byte 0xc3

draw_sel:                      /* replaces 'mov ax,[8D4C] / cmp ax,8' */
    .byte 0xe8
    .word mapped - . - 2
    cmp ax, 8
    .byte 0xcb
fld_sel:                       /* replaces 'mov ax,[8D4C] / dec ax / dec ax' (the je's after it use the flags) */
    .byte 0xe8
    .word mapped - . - 2
    dec ax
    dec ax
    .byte 0xcb
eff_f:                         /* far-callable eff for units B and C */
    .byte 0xe8
    .word eff - . - 2
    .byte 0xcb

name_push:                     /* replaces 'mov bx,[8D4C] / shl bx,2 / push [bx+25DE] / push [bx+25DC]' */
    pop word ptr cs:[V_RIP]
    pop word ptr cs:[V_RCS]
    .byte 0xe8
    .word eff - . - 2
    cmp ax, 9
    jae .Ln_ours
    mov bx, ax
    shl bx, 1
    shl bx, 1
    push word ptr [bx + 0x25de]
    push word ptr [bx + 0x25dc]
    jmp .Ln_ret
.Ln_ours:
    sub ax, 9
    mov bx, ax
    shl bx, 1
    push cs
    push word ptr cs:[bx + NAMES_T]
.Ln_ret:
    push word ptr cs:[V_RCS]
    push word ptr cs:[V_RIP]
    .byte 0xcb

doit_sel:                      /* replaces 'mov ax,[8D4C] / cmp ax,7' before 'ja SLICE' */
    .byte 0xe8
    .word eff - . - 2
    cmp ax, 9
    jae .Ld_ours
    cmp ax, 7
    .byte 0xcb
.Ld_ours:
    add sp, 4                  /* we leave through the stock tail, not back to the switch */
    push es
    mov bx, 0x7762             /* VU Sampling Mode block: save the recording setting, set ours */
    mov es, bx
    mov bl, byte ptr es:[0x730]
    mov byte ptr cs:[V_MODE], bl
    mov bx, word ptr es:[0x736]
    mov word ptr cs:[V_RATE], bx
    mov bl, 1                  /* E 9, 11 = SP1200; 10, 12 = S900 */
    mov cx, %(SP1200)d
    test al, 1
    jnz .Ld_mode
    mov bl, 2
    mov cx, %(S900)d
.Ld_mode:
    mov byte ptr es:[0x730], bl
    mov bx, word ptr cs:[V_RIDX]   /* Rate field: 0 = the preset, else the chosen rate */
    or bx, bx
    jz .Ld_norate
    shl bx, 1
    mov cx, word ptr cs:[bx + RATES_T - 2]
.Ld_norate:
    mov byte ptr cs:[V_COPY], 0
    cmp ax, 11
    jae .Ld_target
    mov byte ptr cs:[V_COPY], 1
.Ld_target:
    les bx, dword ptr [0x98a6] /* the sound the window works on */
    mov dx, word ptr es:[bx + 0x38]   /* its rate: VU's code assumes 44.1 kHz, scale the target by 44100/rate */
    mov ax, 0xac44
    cmp dx, cx
    jb .Ld_rate                /* sound already below the target rate: no decimation (44100) */
    mov ax, cx
    push dx
    mov cx, 0xac44
    mul cx
    pop cx
    div cx                     /* target*44100/rate <= 44100: no overflow */
.Ld_rate:
    push es
    mov cx, 0x7762
    mov es, cx
    mov word ptr es:[0x736], ax
    pop es
    mov word ptr cs:[V_ORIG], bx   /* the original, for RETRY */
    mov word ptr cs:[V_ORIG + 2], es
    cmp byte ptr cs:[V_COPY], 1
    jne .Ld_replace
    push ds                    /* stock COPY SOUND (as SOUND > COPY > DO IT): out = ds:98AA, src, name = ds:8FCB */
    push 0x8fcb
    push es
    push bx
    push ds
    push 0x98aa
    FC 0x3e19, 0x23c6
    add sp, 12
    mov cx, ax
    or cx, dx
    jnz .Ld_done               /* stock error (memory full, name used ...): shown by the tail, nothing processed */
    jmp .Ld_process
.Ld_replace:
    mov word ptr [0x98aa], bx
    mov word ptr [0x98ac], es
.Ld_process:
    push word ptr [0x8b4a]
    push word ptr [0x8b4c]
    mov ax, word ptr [0x98aa]
    mov word ptr [0x8b4a], ax
    mov ax, word ptr [0x98ac]
    mov word ptr [0x8b4c], ax
    FC 0x7762, 0x019d          /* process in place (keeps all registers, ds) */
    pop word ptr [0x8b4c]
    pop word ptr [0x8b4a]
    mov al, byte ptr cs:[V_COPY]
    mov byte ptr cs:[V_KEEP], al   /* NEW SOUND: offer the stock KEEP or RETRY window once the Edit window has closed */
    xor ax, ax
    xor dx, dx
.Ld_done:
    mov bx, 0x7762
    mov es, bx
    mov bl, byte ptr cs:[V_MODE]
    mov byte ptr es:[0x730], bl
    mov bx, word ptr cs:[V_RATE]
    mov word ptr es:[0x736], bx
    pop es
    .byte 0xea                 /* stock DO IT tail: si:[bp-2] = result, flags 3 (waveform cache, refresh) */
    .word 0xed0a, 0x3e19

tail_hook:                     /* replaces 'push cs / call F08C' at the end of every Edit DO IT (ds = 582B) */
    .byte 0xff, 0x1e           /* lcall [8D52]: back to the page the Edit window came from (what F08C does) */
    .word 0x8d52
    cmp byte ptr cs:[V_KEEP], 1
    jne .Lt_out
    mov byte ptr cs:[V_KEEP], 0
    mov byte ptr cs:[V_FROM], 1
    push si                    /* BA9C makes the name 'unique' and counts the copy itself: keep the name from 'New name:' */
    push bx
    push es
    les bx, dword ptr [0xd7c2]
    mov si, 0
.Lt_save:
    mov al, byte ptr es:[bx + si + 0x12]
    mov byte ptr cs:[si + V_NAME], al
    inc si
    cmp si, 16
    jb .Lt_save
    FC 0x3e19, 0xba9c          /* stock KEEP or RETRY for the current sound (= the processed copy): name, pad -> note, PLAY */
    les bx, dword ptr [0xd7c2]
    mov si, 0
.Lt_back:
    mov al, byte ptr cs:[si + V_NAME]
    mov byte ptr es:[bx + si + 0x12], al
    inc si
    cmp si, 16
    jb .Lt_back
    pop es
    pop bx
    pop si
.Lt_out:
    .byte 0xcb
retry_exit:                    /* after RETRY deleted the current sound (the copy): the original becomes current again */
    cmp byte ptr cs:[V_FROM], 1
    jne keep_exit
    push ax
    mov ax, word ptr cs:[V_ORIG]
    mov word ptr [0xd7c2], ax
    mov ax, word ptr cs:[V_ORIG + 2]
    mov word ptr [0xd7c4], ax
    pop ax
keep_exit:                     /* replaces 'push cs / call A5F2' after KEEP (ds = 582B) */
    cmp byte ptr cs:[V_FROM], 1
    jne .Lk_stock
    mov byte ptr cs:[V_FROM], 0
    FC 0x3e19, 0x39ee          /* stop the preview voice, as A5F2 does */
    .byte 0xff, 0x1e           /* back to TRIM / ZONE instead of the SAMPLE page */
    .word 0x8d52
    .byte 0xcb
.Lk_stock:
    FC 0x3e19, 0xa5f2
    .byte 0xcb
rec_keep:                      /* replaces 'push cs / call BA9C' after a recording: a real recording's KEEP exits as stock */
    mov byte ptr cs:[V_FROM], 0
    FC 0x3e19, 0xba9c
    .byte 0xcb
names_t:
    .word S_SPN, S_S9N, S_SPR, S_S9R
s_spn: .asciz "SP1200 \x0c NEW SOUND"
s_s9n: .asciz "S900 \x0c NEW SOUND"
s_spr: .asciz "SP1200 \x0c REPLACE"
s_s9r: .asciz "S900 \x0c REPLACE"
v_rip:  .word 0
v_rcs:  .word 0
v_rate: .word 0
v_mode: .byte 0
v_copy: .byte 0
v_keep: .byte 0
v_from: .byte 0
v_name: .fill 16, 1, 0x20
    .balign 2, 0
v_orig: .word 0, 0
v_ridx: .long 0                /* Rate field value (0 = preset, 1.. = rates_t) */
rates_t: .word %(RATES)s
    .balign 2, 0
    .word NAME_PUSH, DRAW_SEL, FLD_SEL, DOIT_SEL, TAIL_HOOK, KEEP_EXIT, REC_KEEP, RETRY_EXIT, EFF_F, V_RIDX, RATES_T
    .ascii "SLEND"
'''
LABELS = ('name_push', 'draw_sel', 'fld_sel', 'doit_sel', 'tail_hook', 'keep_exit', 'rec_keep', 'v_keep', 'v_from', 'v_name', 'v_orig', 'retry_exit', 'names_t', 's_spn', 's_s9n', 's_spr', 's_s9r', 'v_rip', 'v_rcs', 'v_rate', 'v_mode', 'v_copy', 'eff_f', 'v_ridx', 'rates_t')



MACROS = r"""
.intel_syntax noprefix
.code16
.macro FC seg, off
    .byte 0x9a
    .word \off, \seg
.endm
"""

SRC_B = MACROS + r"""
start:
prt:                           /* bx = string (cs), ax = y, cx = x: stock 3E19:0988 (x, y, far string) */
    push cs
    push bx
    push ax
    push cx
    FC 0x3e19, 0x0988
    add sp, 8
    .byte 0xc3
psk:                           /* bx = label (cs), cx = soft key 1..5: stock 35B0:253C(key, style, far label) */
    push cs
    push bx
    mov ax, 1
    push ax
    push cx
    FC 0x35b0, 0x253c
    add sp, 8
    .byte 0xc3
mksname:                       /* v_sname = the current sound's name (16 chars + NUL) */
    push es
    les bx, dword ptr [0xd7c2]
    xor si, si
.Lmn:
    mov al, byte ptr es:[bx + si + 0x12]
    mov byte ptr cs:[si + V_SNAME], al
    inc si
    cmp si, 16
    jb .Lmn
    mov byte ptr cs:[V_SNAME + 16], 0
    pop es
    .byte 0xc3
mkrate:                        /* ax = E; v_rtxt = "26040 Hz (preset)" / "22050 Hz" */
    push es
    mov bx, A_SEG
    mov es, bx
    mov bx, word ptr es:[A_RIDX]
    or bx, bx
    jnz .Lmr_tab
    mov cx, %(SP1200)d
    test al, 1
    jnz .Lmr_go
    mov cx, %(S900)d
    jmp .Lmr_go
.Lmr_tab:
    shl bx, 1
    mov cx, word ptr es:[bx + A_RATES - 2]
.Lmr_go:
    mov ax, cx
    xor si, si
    mov bx, 10
.Lmr_dv:
    xor dx, dx
    div bx
    push dx
    inc si
    or ax, ax
    jnz .Lmr_dv
    mov di, offset V_RTXT
.Lmr_st:
    pop ax
    add al, 48
    mov byte ptr cs:[di], al
    inc di
    dec si
    jnz .Lmr_st
    mov byte ptr cs:[di], 32
    mov byte ptr cs:[di + 1], 72
    mov byte ptr cs:[di + 2], 122
    add di, 3
    mov byte ptr cs:[di], 0
    cmp word ptr es:[A_RIDX], 0
    jne .Lmr_end
    mov si, offset S_PRE
.Lmr_cp:
    mov al, byte ptr cs:[si]
    mov byte ptr cs:[di], al
    inc si
    inc di
    or al, al
    jnz .Lmr_cp
.Lmr_end:
    pop es
    .byte 0xc3

draw_tail:                     /* replaces 'push cs / call 9E5A' ending the Edit window's drawing (ds = 582B); our rows first, 9E5A draws the field highlight */
    pusha
    push es
    FC A_SEG, A_EFFF
    cmp ax, 9
    jb .Ldt_out
    mov di, ax
    .byte 0xe8
    .word mksname - . - 2
    cmp di, 11
    jb .Ldt_new
    mov bx, offset S_BLANK     /* REPLACE: the stock two-line text is replaced by our rows */
    mov ax, 0x17
    mov cx, 0x2b
    .byte 0xe8
    .word prt - . - 2
    mov bx, offset S_BLANK
    mov ax, 0x21
    mov cx, 0x2b
    .byte 0xe8
    .word prt - . - 2
    mov bx, offset S_SOUND
    mov ax, 0x15
    mov cx, 0x13
    .byte 0xe8
    .word prt - . - 2
    mov bx, offset V_SNAME
    mov ax, 0x15
    mov cx, 0x31
    .byte 0xe8
    .word prt - . - 2
    mov bx, offset S_NOUNDO
    mov ax, 0x29
    mov cx, 0x13
    .byte 0xe8
    .word prt - . - 2
    jmp .Ldt_rate
.Ldt_new:
    mov bx, offset S_SOUND     /* NEW SOUND: the source sound under the Rate row */
    mov ax, 0x29
    mov cx, 0x13
    .byte 0xe8
    .word prt - . - 2
    mov bx, offset V_SNAME
    mov ax, 0x29
    mov cx, 0x31
    .byte 0xe8
    .word prt - . - 2
.Ldt_rate:
    mov ax, di
    .byte 0xe8
    .word mkrate - . - 2
    mov bx, offset S_RATE
    mov ax, 0x1f
    mov cx, 0x13
    .byte 0xe8
    .word prt - . - 2
    mov bx, offset V_RTXT
    mov ax, 0x1f
    mov cx, 0x31
    .byte 0xe8
    .word prt - . - 2
    mov bx, offset S_RM        /* F1 / F3 change the Rate */
    mov cx, 1
    .byte 0xe8
    .word psk - . - 2
    mov bx, offset S_RP
    mov cx, 3
    .byte 0xe8
    .word psk - . - 2
.Ldt_out:
    pop es
    popa
    FC 0x3e19, 0x9e5a
    .byte 0xcb
s_blank: .asciz "                            "
s_sound: .asciz "Snd:"
s_rate:  .asciz "Rate:"
s_noundo: .asciz "No undo!  Hit a pad to pick"
s_pre:   .asciz " (preset)"
s_rm:    .asciz "RATE-"
s_rp:    .asciz "RATE+"
v_sname: .fill 17, 1, 0
v_rtxt:  .fill 24, 1, 0
    .balign 2, 0
    .word DRAW_TAIL
    .ascii "BEND"
"""
LABELS_B = ('s_rm', 's_rp', 'draw_tail', 's_blank', 's_sound', 's_rate', 's_noundo', 's_pre', 'v_sname', 'v_rtxt')

SRC_C = MACROS + r"""
start:
open_win:                      /* replaces 'push ds / push 2606 / call 0724' (install the Edit window record): ours has the pad and F1/F3 events */
    pop word ptr cs:[V_OIP]
    pop word ptr cs:[V_OCS]
    push cs
    mov ax, offset REC
    push ax
    FC 0x3e19, 0x0724
    push word ptr cs:[V_OCS]   /* the stock 'add sp,4' removes our two argument words */
    push word ptr cs:[V_OIP]
    .byte 0xcb
rate_dn:                       /* Edit window F1: Rate - (preset <- 8000 <- ...) */
    pusha
    push ds
    push es
    mov cx, 0xffff
    jmp .Lr_go
rate_up:                       /* Edit window F3: Rate + */
    pusha
    push ds
    push es
    mov cx, 1
.Lr_go:
    mov bx, 0x582b
    mov ds, bx
    FC A_SEG, A_EFFF
    cmp ax, 9
    jb .Lr_out
    mov ax, A_SEG
    mov es, ax
    mov bx, word ptr es:[A_RIDX]
    add bx, cx
    cmp bx, 0xffff
    je .Lr_out
    cmp bx, %(NR)d
    ja .Lr_out
    mov word ptr es:[A_RIDX], bx
    FC 0x3e19, 0xed5c          /* redraw the window */
.Lr_out:
    pop es
    pop ds
    popa
    .byte 0xcb
pad_sel:                       /* Edit window event 0x37 (pad): al = velocity, ah = pad. Our entries only (E >= 9, opened from TRIM) */
    pusha
    push ds
    push es
    or al, al
    je .Lp_out
    mov dl, ah
    mov bx, 0x582b
    mov ds, bx
    FC A_SEG, A_EFFF
    cmp ax, 9
    jb .Lp_out
    cmp word ptr [0x8d52], 0xf1dc
    jne .Lp_trim
    cmp word ptr [0x8d54], 0x3e19
    je .Lp_out
.Lp_trim:
    mov bx, 0xfe7              /* drum track -> program -> the pad's sound (as the TRIM pad select) */
    mov es, bx
    mov di, word ptr es:[0x4854]
    mov es, word ptr es:[0x430a]
    mov bl, byte ptr es:[di + 0x5c0]
    dec bl
    cmp bl, 3
    ja .Lp_out
    xor bh, bh
    add bx, 0x5c
    shl bx, 1
    shl bx, 1
    xor cx, cx
    mov es, cx
    les si, dword ptr es:[bx]
    mov cx, es
    or cx, si
    je .Lp_out
    mov bl, dl
    and bl, 0x3f
    xor bh, bh
    shl bx, 1
    shl bx, 1
    mov ax, word ptr es:[si + bx + 0x7de]
    mov dx, word ptr es:[si + bx + 0x7e0]
    mov cx, ax
    or cx, dx
    je .Lp_out
    mov word ptr [0xd7c2], ax  /* the pad's sound becomes the sound this window works on */
    mov word ptr [0xd7c4], dx
    mov word ptr [0x98a6], ax
    mov word ptr [0x98a8], dx
    mov word ptr [0x8d4e], ax
    mov word ptr [0x8d50], dx
    mov cx, ax
    add cx, 0x12
    push dx                    /* 'New name:' proposal from this sound (what the window does on opening) */
    push cx
    push ds
    mov ax, 0x8fcb
    push ax
    FC 0x3e19, 0xa346
    add sp, 8
    push ds                    /* TRIM page: Snd field change callback */
    push word ptr [0xd7c4]
    push word ptr [0xd7c2]
    FC 0x3e19, 0xbfe6
    add sp, 4
    pop ds
    FC 0x3e19, 0x39ee
    les di, dword ptr [0xd7c2] /* audition: play the whole sound */
    mov cx, word ptr es:[di + 0x2e]
    mov si, word ptr es:[di + 0x30]
    mov ax, 0x7f
    push ax
    push si
    push cx
    xor ax, ax
    push ax
    push ax
    push es
    push di
    FC 0x3e19, 0x3d2c
    add sp, 14
    FC 0x3e19, 0xed5c          /* redraw the window */
.Lp_out:
    pop es
    pop ds
    popa
    .byte 0xcb
v_oip: .word 0
v_ocs: .word 0
rec:                           /* the stock Edit window record 582B:2606 (event table) + F1, F3, pad (0x37) events */
    .byte %(REC)s
    .byte 0x02
    .word RATE_DN, %(SEGC)d
    .byte 0x04
    .word RATE_UP, %(SEGC)d
    .byte 0x37
    .word PAD_SEL, %(SEGC)d
    .byte 0, 0, 0, 0, 0
    .balign 2, 0
    .word OPEN_WIN
    .ascii "CEND"
"""
LABELS_C = ('open_win', 'rate_dn', 'rate_up', 'pad_sel', 'v_oip', 'v_ocs', 'rec')


def _assemble(src, consts):
    cs = ''.join(f'.set {k}, {v}\n' for k, v in consts.items())
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(src.replace('start:\n', cs + 'start:\n', 1))
    code = assemble(p); os.remove(p)
    return code


def build_units(rec):
    """assemble A, B, C (B and C refer to A, A refers to C: two passes, same sizes) -> (codeA, codeB, codeC, exports)"""
    labA = {n.upper(): f'{n} - start' for n in LABELS}
    labB = {n.upper(): f'{n} - start' for n in LABELS_B}
    labC = {n.upper(): f'{n} - start' for n in LABELS_C}
    fmt = {'SP1200': SP1200, 'S900': S900, 'RATES': ', '.join(map(str, RATES)), 'NR': len(RATES), 'REC': ', '.join(f'0x{b:02x}' for b in rec), 'SEGC': SEG_C}
    ex = {'A_EFFF': 0x1234, 'A_RIDX': 0x1234, 'A_RATES': 0x1234, 'A_SEG': SEG, 'SEG_C': SEG_C}
    for _ in range(2):
        a = _assemble(SRC % fmt, {**labA, **ex, 'SEG_C': SEG_C})
        b = _assemble(SRC_B % fmt, {**labB, **ex})
        c = _assemble(SRC_C % fmt, {**labC, **ex})
        assert a.endswith(b'SLEND') and b.endswith(b'BEND') and c.endswith(b'CEND'), 'export table / end marker missing'
        ea = struct.unpack('<11H', a[-27:-5]); (db,) = struct.unpack('<H', b[-6:-4]); (ec,) = struct.unpack('<H', c[-6:-4])
        ex = {'A_EFFF': ea[8], 'A_RIDX': ea[9], 'A_RATES': ea[10], 'A_SEG': SEG, 'SEG_C': SEG_C}
    return (a, b, c), ea, db, ec


def far(off, seg=SEG):
    return bytes([0x9a]) + struct.pack('<HH', off, seg)


def apply(img):
    rec = bytes(img.d[0x582b0 + 0x2606:0x582b0 + 0x2606 + 30])
    assert rec.hex() == '01000000' '00' '03e2eb193e' '05d4eb193e' '06f6eb193e' '325ced193e' '15d4eb193e', 'Edit window record differs from stock'
    (a, b, c), ea, db, ec = build_units(rec)
    name_push, draw_sel, fld_sel, doit_sel, tail_hook, keep_exit, rec_keep, retry_exit = ea[:8]
    open_win = ec
    assert a[doit_sel] == 0xe8 and a[name_push:name_push + 3] == bytes.fromhex('2e8f06'), 'exports do not point at their routines'
    img.put(LIN, a, 'sound_lofi')
    img.put(LIN_B, b, 'sound_lofi B')
    img.put(LIN_C, c, 'sound_lofi C')
    B = 0x3e190
    img.patch(B + 0xef8e, bytes.fromhex('b80800'), bytes.fromhex('b80c00'))       # list max from ZONE: 8 -> 12
    img.patch(B + 0xef94, bytes.fromhex('b80700'), bytes.fromhex('b80b00'))       # list max from TRIM: 7 -> 11
    img.patch(B + 0xed82, bytes.fromhex('8b1e4c8d' 'c1e302' 'ffb7de25' 'ffb7dc25'), far(name_push) + b'\x90' * 10)
    img.patch(B + 0xed9d, bytes.fromhex('a14c8d' '3d0800'), far(draw_sel) + b'\x90')
    img.patch(B + 0xefb0, bytes.fromhex('a14c8d' '4848'), far(fld_sel))
    img.patch(B + 0xec15, bytes.fromhex('a14c8d' '3d0700'), far(doit_sel) + b'\x90')
    # NEW SOUND -> stock KEEP or RETRY window; its exits go back to TRIM/ZONE when it was opened from here
    img.patch(B + 0xed52, bytes.fromhex('900ee83503'), far(tail_hook))
    img.patch(B + 0xbb77, bytes.fromhex('900ee876ea'), far(keep_exit))
    img.patch(B + 0xbb0e, bytes.fromhex('900ee8dfea'), far(retry_exit))
    img.patch(B + 0xa8b0, bytes.fromhex('900ee8e711'), far(rec_keep))
    # EXP15: Rate field + Sound row (drawing), next field after 'New name:', the window record with the pad event
    img.patch(B + 0xef70, bytes.fromhex('900ee8e5ae'), far(db, SEG_B))
    img.patch(B + 0xebbc, bytes.fromhex('1e680626' '900ee85f1b'), far(open_win, SEG_C) + b'\x90' * 4)
    return len(a) + len(b) + len(c)


if __name__ == '__main__':
    print(SRC % {'SP1200': SP1200, 'S900': S900, 'RATES': '0', 'NR': 0, 'REC': '0', 'SEGC': 0})
