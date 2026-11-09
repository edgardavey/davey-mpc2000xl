#!/usr/bin/env python3
"""make_floppy.py OUT.img FILE [FILE...]   (1.44 MB FAT12, files in the root, in the order given)

Pure Python, any OS (replaces the macOS-only make_floppy.sh). Volume label MPCDISK.
FILE can carry a timestamp:  NAME@YYYY-MM-DDTHH:MM  (gold_floppy needs MPC2KXL.BIN stamped 2004-11-11 15:11).
Names must fit 8.3 (the MPC shows them upper-case)."""
import os, struct, sys, datetime

SEC, TOTAL, FATSEC, ROOT = 512, 2880, 9, 224
FAT_AT, ROOT_AT = 1, 1 + 2 * FATSEC
DATA_AT = ROOT_AT + ROOT * 32 // SEC


def fat12_set(fat, n, v):
    i = n * 3 // 2
    if n & 1: fat[i] = (fat[i] & 0x0F) | ((v & 0x0F) << 4); fat[i + 1] = v >> 4
    else: fat[i] = v & 0xFF; fat[i + 1] = (fat[i + 1] & 0xF0) | (v >> 8)


def dos_time(t): return (t.hour << 11) | (t.minute << 5) | (t.second // 2)
def dos_date(t): return ((t.year - 1980) << 9) | (t.month << 5) | t.day


def build(files, label='MPCDISK'):
    """files: [(name83, bytes, datetime)] -> 1474560 bytes"""
    img = bytearray(TOTAL * SEC)
    img[0:3] = b'\xEB\x3C\x90'; img[3:11] = b'DAVEYMPC'
    struct.pack_into('<HBHBHHBHHHII', img, 11, SEC, 1, 1, 2, ROOT, TOTAL, 0xF0, FATSEC, 18, 2, 0, 0)
    struct.pack_into('<BBBI11s8s', img, 36, 0, 0, 0x29, 0x4D504344, label.ljust(11).encode(), b'FAT12   ')
    img[510:512] = b'\x55\xAA'
    fat = bytearray(FATSEC * SEC); fat[0:3] = b'\xF0\xFF\xFF'
    root = bytearray(ROOT * 32); now = datetime.datetime(2026, 1, 1)
    root[0:11] = label.ljust(11).encode(); root[11] = 0x08
    struct.pack_into('<HH', root, 22, dos_time(now), dos_date(now))
    nxt, slot = 2, 1
    for name, data, ts in files:
        base, _, ext = name.upper().partition('.')
        if len(base) > 8 or len(ext) > 3 or slot >= ROOT: sys.exit('bad name or too many files: ' + name)
        n = max(1, -(-len(data) // SEC))
        if nxt - 2 + n > TOTAL - DATA_AT: sys.exit('disk full at ' + name)
        e = slot * 32
        root[e:e + 11] = (base.ljust(8) + ext.ljust(3)).encode(); root[e + 11] = 0x20
        struct.pack_into('<HHHHHHHHI', root, e + 12, 0, 0, dos_date(ts), 0, 0, dos_time(ts), dos_date(ts), nxt, len(data))
        for k in range(n):
            fat12_set(fat, nxt + k, 0xFFF if k == n - 1 else nxt + k + 1)
        off = (DATA_AT + nxt - 2) * SEC; img[off:off + len(data)] = data
        nxt += n; slot += 1
    for k in range(2): img[(FAT_AT + k * FATSEC) * SEC:(FAT_AT + (k + 1) * FATSEC) * SEC] = fat
    img[ROOT_AT * SEC:ROOT_AT * SEC + len(root)] = root
    return bytes(img)


def main(argv):
    if len(argv) < 3: sys.exit(__doc__)
    files = []
    for a in argv[2:]:
        p, _, ts = a.partition('@')
        t = datetime.datetime.fromisoformat(ts) if ts else datetime.datetime.fromtimestamp(os.path.getmtime(p))
        files.append((os.path.basename(p), open(p, 'rb').read(), t))
    open(argv[1], 'wb').write(build(files)); print('Wrote', argv[1])


if __name__ == '__main__': main(sys.argv)
