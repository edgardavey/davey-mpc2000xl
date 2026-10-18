"""Dark mode: every pixel byte the OS sends to the LCD is inverted (white on dark).

The LCD refresh routine (0x1abdc) has four inner loops, one per variant (plain / layered) and per LCD bank (port 0x62 / 0x102).
Each loop is rewritten IN PLACE with the same length and the same loop structure, so a refresh costs the stock number of
instructions plus one 'not al' per byte (the first version used a far call per byte; that made the refresh so slow that the
OS update (DO IT) never started on real hardware). The data byte is now fetched after the LCD-ready wait instead of before it,
which lets 'not al' fit exactly where 'mov al,ah' was.
"""
import struct

def _rel(frm_next, target): return struct.pack('<H', (target - frm_next) & 0xffff)

def _plain(start, ctl, data, wait):
    old = (bytes.fromhex('8a20') + b'\xba' + struct.pack('<H', ctl) + bytes.fromhex('ecd0e07403')
           + b'\xe8' + _rel(start + 0x0a + 3, wait) + bytes.fromhex('8ac4') + b'\xba' + struct.pack('<H', data)
           + bytes.fromhex('ee83c320e2e8'))
    new = (b'\xba' + struct.pack('<H', ctl) + bytes.fromhex('ecd0e07403')
           + b'\xe8' + _rel(start + 0x08 + 3, wait) + bytes.fromhex('8a00f6d0') + b'\xba' + struct.pack('<H', data)
           + bytes.fromhex('ee83c320e2e8'))
    return start, old, new

def _layered(start, ctl, data, wait):
    loads_ah = bytes.fromhex('8aa7a257' '0aa7225f' '32a7a266')
    loads_al = bytes.fromhex('8a87a257' '0a87225f' '3287a266')
    old = (loads_ah + b'\xba' + struct.pack('<H', ctl) + bytes.fromhex('ecd0e07403')
           + b'\xe8' + _rel(start + 0x0c + 0x08 + 3, wait) + bytes.fromhex('8ac4') + b'\xba' + struct.pack('<H', data)
           + bytes.fromhex('ee83c320e2de'))
    new = (b'\xba' + struct.pack('<H', ctl) + bytes.fromhex('ecd0e07403')
           + b'\xe8' + _rel(start + 0x08 + 3, wait) + loads_al + bytes.fromhex('f6d0') + b'\xba' + struct.pack('<H', data)
           + bytes.fromhex('ee83c320e2de'))
    return start, old, new

LOOPS = [_plain(0x1ac2a, 0x60, 0x62, 0x1aba5), _plain(0x1ac6a, 0x100, 0x102, 0x1abc1),
         _layered(0x1acbd, 0x60, 0x62, 0x1aba5), _layered(0x1ad07, 0x100, 0x102, 0x1abc1)]

def apply(img):
    for start, old, new in LOOPS:
        assert len(old) == len(new)
        img.patch(start, old, new)
