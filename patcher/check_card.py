#!/usr/bin/env python3
"""Read-only: does this disk/card meet what the MPC2000XL BOOT LOADER requires to find MPC2KXL.BIN?
Rules are taken from the boot program's disassembly (boot code 0x2860-0x29a8):
 LBA0 must end 55 AA. It is either a FAT boot sector itself, or an MBR whose partition 1-4 has a start LBA; the partition boot sector is then read.
 A FAT boot sector starts with EB or E9 and has 'FAT12' or 'FAT16' at offset 0x36 and (16-bit total sectors at 0x13 == 0 or MBR type 4).
Then the file MPC2KXL.BIN (8.3 'MPC2KXL BIN') must be in the root directory.
usage: sudo python3 check_card.py /dev/rdiskN      (or a disk image file)"""
import struct, sys

def check(read):                       # read(lba) -> 512 bytes
    out = []
    s0 = read(0)
    if s0[510:512] != b'\x55\xaa': return ['FAIL LBA0 has no 55AA signature']
    def fat_ok(b):
        return b[0] in (0xEB, 0xE9) and b[0x36:0x3B] in (b'FAT12', b'FAT16')
    base = 0
    if fat_ok(s0): out.append('ok   LBA0 is a FAT boot sector (no partition table)'); b = s0
    else:
        base = None
        for i in range(4):
            e = s0[0x1BE + 16 * i: 0x1BE + 16 * i + 16]; start = struct.unpack('<I', e[8:12])[0]
            if start and fat_ok(read(start)): base = start; out.append('ok   partition %d (type 0x%02x) starts at LBA %d' % (i + 1, e[4], start)); break
        if base is None: return out + ['FAIL no partition with a FAT12/FAT16 boot sector (EB/E9 jump and FAT12/FAT16 at 0x36)']
        b = read(base)
    if b[0x36:0x3B] == b'FAT16' and struct.unpack('<H', b[0x13:0x15])[0] != 0 and s0[0x1C2] != 4:   # FAT12 has no such test in the loader
        out.append('WARN 16-bit total sectors != 0 and MBR type != 4: the loader rejects this layout')
    bps, spc, rsv, nfat, rootn = struct.unpack('<HBHBH', b[11:19]); fatsz = struct.unpack('<H', b[22:24])[0]
    out.append('info bytes/sector %d, sectors/cluster %d (cluster %d KiB), root entries %d' % (bps, spc, bps * spc // 1024, rootn))
    if bps != 512: out.append('WARN bytes per sector is not 512')
    root = base + rsv + nfat * fatsz
    for n in range((rootn * 32 + 511) // 512):
        sec = read(root + n)
        for k in range(0, 512, 32):
            if sec[k:k + 11] == b'MPC2KXL BIN': return out + ['ok   MPC2KXL.BIN found in the root directory, %d bytes' % struct.unpack('<I', sec[k + 28:k + 32])[0]]
    return out + ['FAIL MPC2KXL.BIN not found in the root directory (8.3 name MPC2KXL.BIN)']

def selftest():
    img = bytearray(512 * 400)
    bs = bytearray(512); bs[0:3] = b'\xeb\x3c\x90'; bs[11:13] = struct.pack('<H', 512); bs[13] = 4; bs[14:16] = struct.pack('<H', 1)
    bs[16] = 2; bs[17:19] = struct.pack('<H', 16); bs[22:24] = struct.pack('<H', 4); bs[0x36:0x3E] = b'FAT16   '; bs[510:512] = b'\x55\xaa'
    mbr = bytearray(512); mbr[0x1BE + 4] = 6; mbr[0x1BE + 8:0x1BE + 12] = struct.pack('<I', 8); mbr[510:512] = b'\x55\xaa'
    img[0:512] = mbr; img[8 * 512:9 * 512] = bs
    root = 8 + 1 + 2 * 4; ent = bytearray(32); ent[0:11] = b'MPC2KXL BIN'; ent[28:32] = struct.pack('<I', 524288)
    img[root * 512:root * 512 + 32] = ent
    r = check(lambda l: bytes(img[l * 512:l * 512 + 512]))
    assert r[-1].startswith('ok   MPC2KXL.BIN'), r
    img[root * 512:root * 512 + 11] = b'XXXXXXXX BIN'
    assert check(lambda l: bytes(img[l * 512:l * 512 + 512]))[-1].startswith('FAIL MPC2KXL.BIN not found')
    img[510:512] = b'\x00\x00'; assert check(lambda l: bytes(img[l * 512:l * 512 + 512]))[0].startswith('FAIL LBA0')
    print('self-test ok')

if __name__ == '__main__':
    if len(sys.argv) < 2: selftest(); sys.exit()
    f = open(sys.argv[1], 'rb')
    def rd(l): f.seek(l * 512); return f.read(512)
    print('\n'.join(check(rd)))
