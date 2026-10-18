"""Sampling Mode (SAMPLE page, cursor on Mode, WINDOW): preset OFF / SP1200 (26.04 kHz, 12-bit) / S900 (30 kHz) or a custom
rate 8000-44100 Hz. After a recording finishes the new sound is resampled in place to the chosen rate.

The 1866-byte code block comes from a community-built MPC2000XL OS found online (open source / DIY project, no licence text);
it is stored unmodified in blobs/sampling_mode_77620.bin and must sit at linear 0x77620 (segment 0x7762).
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
STUB_OFF = 0x7c0                      # stub position inside the block's 64 KiB segment (physical 0x77de0, free)
NUM_CALL = 0x89                       # 'mov bx,0x508' (3 bytes) just before the number print 'int 0x90'
MSG_SITE = 0x1d7                      # 19 bytes: push/push/push/push/lcall 0x35b0:0x2568/add sp,8 (the stock message box)
MSG_OLD = bytes.fromhex('68193e' '6a12' '68193e' '680ae2' '9a6825b035' '83c408')
MSG_STUB = 0x800                      # physical 0x77e20, free
MSG_TEXT = b'Processing...' + b' ' * 13  # 26 columns: also wipes "Waiting for input signal..."


def apply(img):
    blk = bytearray(open(BLK, 'rb').read())
    assert len(blk) == 1866
    assert not any(img.d[BLK_LIN:BLK_LIN + len(blk)]), 'sampling block area not empty'
    assert blk[NUM_CALL:NUM_CALL + 3] == bytes.fromhex('bb0805')
    rel = (STUB_OFF - (NUM_CALL + 3)) & 0xffff
    blk[NUM_CALL:NUM_CALL + 3] = bytes([0xe8, rel & 0xff, rel >> 8])
    assert bytes(blk[MSG_SITE:MSG_SITE + len(MSG_OLD)]) == MSG_OLD
    rel2 = (MSG_STUB - (MSG_SITE + 3)) & 0xffff
    blk[MSG_SITE:MSG_SITE + len(MSG_OLD)] = bytes([0xe8, rel2 & 0xff, rel2 >> 8]) + b'\x90' * (len(MSG_OLD) - 3)
    img.d[BLK_LIN:BLK_LIN + len(blk)] = blk
    msg = b'\xcd\x8f\x05\x00\x32' + MSG_TEXT + b'\x00\xc3'      # int 0x8f: print string at x=0,y=50 ; ret
    assert not any(img.d[BLK_LIN + MSG_STUB:BLK_LIN + MSG_STUB + len(msg)])
    img.d[BLK_LIN + MSG_STUB:BLK_LIN + MSG_STUB + len(msg)] = msg
    stub = bytes.fromhex('bb0805' '31d2' 'c3')                 # mov bx,0x508 ; xor dx,dx ; ret
    assert not any(img.d[BLK_LIN + STUB_OFF:BLK_LIN + STUB_OFF + len(stub)])
    img.d[BLK_LIN + STUB_OFF:BLK_LIN + STUB_OFF + len(stub)] = stub
    img.patch(0x48ad7, bytes.fromhex('900ee8fe0f'), bytes.fromhex('9a00006277'))
    img.patch(0x48a20, bytes.fromhex('900ee8070e'), bytes.fromhex('9a98016277'))
