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

LIN = 0x75e60                 # measured-free range 0x75CE6-0x761E1 (after prog_mono 0x75E00-0x75E4F)
SEG = LIN >> 4
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
    .balign 2, 0
    .word NAME_PUSH, DRAW_SEL, FLD_SEL, DOIT_SEL, TAIL_HOOK, KEEP_EXIT, REC_KEEP, RETRY_EXIT
    .ascii "SLEND"
'''
LABELS = ('name_push', 'draw_sel', 'fld_sel', 'doit_sel', 'tail_hook', 'keep_exit', 'rec_keep', 'v_keep', 'v_from', 'v_name', 'v_orig', 'retry_exit', 'names_t', 's_spn', 's_s9n', 's_spr', 's_s9r', 'v_rip', 'v_rcs', 'v_rate', 'v_mode', 'v_copy')


def source():
    consts = ''.join(f'.set {n.upper()}, {n} - start\n' for n in LABELS)
    return (SRC % {'SP1200': SP1200, 'S900': S900}).replace('start:\n', consts + 'start:\n', 1)


def far(off):
    return bytes([0x9a]) + struct.pack('<HH', off, SEG)


def apply(img):
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(source())
    code = assemble(p); os.remove(p)
    assert code.endswith(b'SLEND'), 'export table / end marker missing'
    name_push, draw_sel, fld_sel, doit_sel, tail_hook, keep_exit, rec_keep, retry_exit = struct.unpack('<8H', code[-21:-5])
    assert code[doit_sel] == 0xe8 and code[name_push:name_push + 3] == bytes.fromhex('2e8f06'), 'exports do not point at their routines'
    img.put(LIN, code, 'sound_lofi')
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
    return len(code)


if __name__ == '__main__':
    print(source())
