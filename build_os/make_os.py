#!/usr/bin/env python3
"""Build the combined OS from the stable VUBEATZ+overdub-fix BIN by applying independent patch modules.
usage: make_os.py out.BIN [module ...]   (no modules = all)"""
import hashlib, os, struct, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm16 import assemble
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'archive', 'stable_overdub_fix_2026-10-07', 'MPC2KXL_overdub_fix.BIN')
BASE_SHA = '1b98ca5671effb5f1cefebb7aa88bcb293f9173d2b8f9f14b0073cfde7c499d5'
NEW_SEG, NEW_LIN = 0x7000, 0x70000          # our code segment (free flash/RAM image area)

class Image:
    def __init__(self):
        self.d = bytearray(open(BASE, 'rb').read())
        assert hashlib.sha256(self.d).hexdigest() == BASE_SHA
        self.next = 0                       # next free offset in the new segment
    def place(self, code, align=2):
        self.next = (self.next + align - 1) & ~(align - 1)
        off = self.next
        assert not any(self.d[NEW_LIN+off:NEW_LIN+off+len(code)]), 'new-segment area not empty'
        self.d[NEW_LIN+off:NEW_LIN+off+len(code)] = code
        self.next += len(code)
        return off
    def patch(self, lin, old, new):
        assert bytes(self.d[lin:lin+len(old)]) == old, f'unexpected bytes at {lin:#x}: {bytes(self.d[lin:lin+len(old)]).hex()}'
        assert len(old) == len(new)
        self.d[lin:lin+len(new)] = new
    def finish(self, out):
        self.d[0x77ffe:0x78000] = struct.pack('<H', sum(w for (w,) in struct.iter_unpack('<H', self.d[:0x77ffe])) & 0xffff)
        open(out, 'wb').write(self.d)
        print('wrote', out, hashlib.sha256(self.d).hexdigest()[:16], 'new code', self.next, 'bytes')

ALL = ['zone_lazy', 'mute8', 'version2', 'sampling', 'date']
def build(out, mods, version=None):
    img = Image()
    img.version = version
    for m in mods:
        mod = __import__('mod_' + m)
        mod.apply(img)
        print('applied', m)
    img.finish(out)

if __name__ == '__main__':
    args = sys.argv[1:]
    version = None
    if '--version' in args:
        i = args.index('--version'); version = args[i + 1]; del args[i:i + 2]
    out, mods = args[0], args[1:] or ALL
    build(out, mods, version)
