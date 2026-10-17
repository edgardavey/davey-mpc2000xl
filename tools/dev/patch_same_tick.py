#!/usr/bin/env python3
"""Fix: overdubbing a REGIONS pad deleted an existing event of another region on the same tick.

The native overdub copy-through (0x64A8) treats an existing event as replaced when a newly
recorded note has the same note byte and the same 6-bit variation value (byte 3 & 0x3F).
REGIONS events share one source note and keep byte 3 at 0; the region is in byte 7
(0xF0 | region). So every region looked identical and the older event was dropped.
This adds a byte-7 compare when either event is a REGIONS event. Native events are unchanged.
Input must be the exact modded BIN; the output is a new file."""
import hashlib, struct, sys
IN_SHA = 'fc713e144a701866e168290cb076ecceffc8151ddf89bf9f5ddc0276ccedfb6e'
HOOK = 0x64bf
ORIG = bytes.fromhex('3a450475f28a5d0380e33f3ae375e8e82807c3')  # cmp al,[di+4] .. call 6BF9; ret
NEXT, DUP = 0x64b6, 0x64ce                                       # native: next pending entry / drop old
CAVE, SEG = 0x76dd0, 0x749b                                      # unused zeros in the REGIONS segment

def build(counters=None):
    """counters: CS offset of 3 test-only words (entries, native match, deletes)."""
    c, lab, fix = bytearray(), {}, []
    def op(*b): c.extend(b)
    def jcc(opc, name): op(opc, 0); fix.append((len(c) - 1, name))
    def far(ip): op(0xea, *struct.pack('<HH', ip, 0))
    def count(k):
        if counters is not None: op(0x2e, 0xff, 0x06, *struct.pack('<H', counters + 2 * k))
    count(0)
    op(0x3a, 0x45, 0x04); jcc(0x75, 'next')            # cmp al,[di+4]      ; same note?
    op(0x8a, 0x5d, 0x03, 0x80, 0xe3, 0x3f)             # mov bl,[di+3]; and bl,3Fh
    op(0x3a, 0xe3); jcc(0x75, 'next')                  # cmp ah,bl          ; same variation?
    count(1)
    op(0x50)                                           # push ax
    op(0x26, 0x8a, 0x64, 0x07, 0x80, 0xfc, 0xf0)       # mov ah,es:[si+7]; cmp ah,0F0h
    jcc(0x73, 'reg')                                   # existing is a REGIONS event
    op(0x8a, 0x65, 0x07, 0x80, 0xfc, 0xf0)             # mov ah,[di+7]; cmp ah,0F0h
    jcc(0x72, 'dup')                                   # neither is: native behaviour
    lab['reg'] = len(c)
    op(0x26, 0x8a, 0x64, 0x07, 0x3a, 0x65, 0x07)       # mov ah,es:[si+7]; cmp ah,[di+7]
    jcc(0x75, 'next_pop')                              # other region: keep the old event
    lab['dup'] = len(c)
    count(2)
    op(0x58); far(DUP)                                 # pop ax; drop the old event
    lab['next_pop'] = len(c); op(0x58)                 # pop ax
    lab['next'] = len(c); far(NEXT)                    # next pending entry
    for pos, name in fix:
        c[pos] = lab[name] - (pos + 1)
    return bytes(c)

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    test = '--count' in sys.argv
    d = bytearray(open(src, 'rb').read())
    assert hashlib.sha256(d).hexdigest() == IN_SHA, 'input is not the expected modded BIN'
    assert d[HOOK:HOOK + len(ORIG)] == ORIG, 'hook site differs'
    ip = CAVE - SEG * 16
    code = build(ip + 0x80 if test else None)
    assert not any(d[CAVE:CAVE + 0x86]), 'cave not empty'
    d[CAVE:CAVE + len(code)] = code
    d[HOOK:HOOK + 5] = bytes([0xea]) + struct.pack('<HH', ip, SEG)   # rest of the native code stays
    d[0x77ffe:0x78000] = struct.pack('<H', sum(w for (w,) in struct.iter_unpack('<H', d[:0x77ffe])) & 0xffff)
    open(dst, 'wb').write(d)
    print('wrote', dst, hashlib.sha256(d).hexdigest(), f'hook {HOOK:#x} -> {SEG:04x}:{ip:04x}', len(code), 'bytes')
