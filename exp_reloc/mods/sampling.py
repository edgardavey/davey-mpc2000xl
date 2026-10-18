"""Sampling Mode (SAMPLE page, cursor on Mode, WINDOW): preset OFF / SP1200 (26.04 kHz, 12-bit) / S900 (30 kHz) or a custom
rate 8000-44100 Hz. After a recording finishes the new sound is resampled in place to the chosen rate.

The 1866-byte code block is vubeatz's Sampling Mode (module `lofi_window` of his MPC2000XL Updater 2, github.com/dariuszchynek),
used with his permission. It is taken unmodified from his Updater data (XOR patch at 0x77620 applied to the stock OS) or from a
local copy in blobs/sampling_mode_77620.bin, and must sit at linear 0x77620 (segment 0x7762).
Hooks (2 x 5 bytes): the SAMPLE-page screen-update call (0x48ad7, entry +0x0000) and the call that runs after a recording
finishes (0x48a20, entry +0x0198). Both hooks call the original routine themselves, so with preset OFF nothing changes.
Two fixes on top of the original:
1. The Sample Rate field printed garbage because DX held a stale value when the number was printed as a 32-bit value;
   a 6-byte stub clears DX first.
2. After a recording was processed, the KEEP or RETRY window came up with no text until a cursor key was pressed. The
   original called the stock message-box routine (0x35b0:0x2568, "processing") and never redraws the page afterwards, which
   leaves the OS in "message active" state. Verified by removing the call: the window text then appears at once. The
   "Processing..." indicator is now printed with the plain text command (int 0x8f, command 5) used for the version line,
   which leaves no state behind."""
import os

BLK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blobs', 'sampling_mode_77620.bin')
BLK_LIN = 0x77620
BLK_LEN = 1866
STOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'sys_stock', 'MPC2KXL.BIN')
VU_JSON = os.environ.get('VU_UPDATER_JSON', os.path.expanduser('~/Documents/CLAUDE/mpc-private-refs/vubeatz/MPC2000XL Updater 2.app/Contents/Resources/modular.json'))

def load_block():
    """vubeatz's Sampling Mode block: the local copy if present, else rebuilt from his Updater 2 data (lofi_window XOR stock)."""
    if os.path.exists(BLK):
        return open(BLK, 'rb').read()
    import base64, json
    stock = open(STOCK, 'rb').read()
    for m in json.load(open(VU_JSON))['modules']:
        if m['id'] == 'lofi_window':
            for p in m['patches']:
                if p.get('offset') == BLK_LIN and 'xor' in p:
                    x = base64.b64decode(p['xor'])
                    return bytes(a ^ b for a, b in zip(x, stock[BLK_LIN:BLK_LIN + len(x)]))[:BLK_LEN]
    raise SystemExit('Sampling Mode block not found: set VU_UPDATER_JSON to vubeatz Updater 2 modular.json')
STUB_OFF = 0x7c0                      # stub position inside the block's 64 KiB segment (physical 0x77de0, free)
NUM_CALL = 0x89                       # 'mov bx,0x508' (3 bytes) just before the number print 'int 0x90'
MSG_SITE = 0x1d7                      # 19 bytes: push/push/push/push/lcall 0x35b0:0x2568/add sp,8 (the stock message box)
MSG_OLD = bytes.fromhex('68193e' '6a12' '68193e' '680ae2' '9a6825b035' '83c408')
MSG_STUB = 0x800                      # physical 0x77e20, free
MSG_TEXT = b'Processing...' + b' ' * 13  # 26 columns: also wipes "Waiting for input signal..."


EXIT_SITE = 0x2b2                     # 'pop es; popa; retf': the only exit after the message box was shown
EXIT_OLD = bytes.fromhex('0761cb')
CLOSE_STUB = 0x800                    # physical 0x77e20
OFF_JMP = 0x1a5                       # 'jmp 0x2b4' (e9 0c 01): Sampling Mode OFF exits straight to the retf at 0x2b4
RETF_STUB = 0x830                     # physical 0x77e50: that retf, moved here because 0x2b2-0x2b4 now hold the jump to CLOSE_STUB


def apply(img):
    """Experimental line: the ORIGINAL black "processing" box stays (stock 35b0:2568). Its missing counterpart is added at
    the routine's exit: stock 3e19:0c22 (posts UI event 0x19, what stock pages call after their own long jobs) and a page
    redraw request, so the KEEP / RETRY window is drawn at once instead of staying blank."""
    blk = bytearray(load_block())
    assert len(blk) == 1866
    assert blk[NUM_CALL:NUM_CALL + 3] == bytes.fromhex('bb0805')
    rel = (STUB_OFF - (NUM_CALL + 3)) & 0xffff
    blk[NUM_CALL:NUM_CALL + 3] = bytes([0xe8, rel & 0xff, rel >> 8])
    assert bytes(blk[MSG_SITE:MSG_SITE + len(MSG_OLD)]) == MSG_OLD          # message box left as in the original
    assert bytes(blk[EXIT_SITE:EXIT_SITE + 3]) == EXIT_OLD
    rel2 = (CLOSE_STUB - (EXIT_SITE + 3)) & 0xffff
    blk[EXIT_SITE:EXIT_SITE + 3] = bytes([0xe9, rel2 & 0xff, rel2 >> 8])    # jmp close_stub
    img.put(BLK_LIN, bytes(blk), 'sampling block')
    stub = bytes.fromhex('bb0805' '31d2' 'c3')                              # mov bx,0x508 ; xor dx,dx ; ret
    img.put(BLK_LIN + STUB_OFF, stub, 'sampling rate-print fix')
    close = bytes.fromhex('1e'                                             # push ds   (all registers were saved by the routine's pusha)
                          'b82b58' '8ed8'                                   # mov ax,0x582b ; mov ds,ax
                          '9a220c193e'                                      # call far 3e19:0c22 (end of message state)
                          'b8e70f' '8ed8' 'c606630001'                      # mov ax,0xfe7 ; mov ds,ax ; mov byte [0x63],1 (redraw)
                          '1f' '07' '61' 'cb')                              # pop ds ; pop es ; popa ; retf (the original exit)
    img.put(BLK_LIN + CLOSE_STUB, close, 'sampling close + redraw')
    # the OFF path must still return immediately (2026-10-16 crash on real hardware: it landed inside the new jmp)
    assert bytes(img.d[BLK_LIN + OFF_JMP:BLK_LIN + OFF_JMP + 3]) == bytes.fromhex('e90c01')
    rel3 = (RETF_STUB - (OFF_JMP + 3)) & 0xffff
    img.d[BLK_LIN + OFF_JMP:BLK_LIN + OFF_JMP + 3] = bytes([0xe9, rel3 & 0xff, rel3 >> 8])
    img.put(BLK_LIN + RETF_STUB, b'\xcb', 'sampling OFF-path retf')
    img.patch(0x48ad7, bytes.fromhex('900ee8fe0f'), bytes.fromhex('9a00006277'))
    img.patch(0x48a20, bytes.fromhex('900ee8070e'), bytes.fromhex('9a98016277'))
    return len(blk)
