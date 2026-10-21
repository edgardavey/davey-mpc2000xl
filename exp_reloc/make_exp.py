#!/usr/bin/env python3
"""EXPERIMENTAL line (separate from build_os/, release/ and the patcher): VU base without REGIONS / VU lazy chop /
EB16 delay, plus the DAVEY chop screen, MUTE 1-8 and Sampling Mode, all placed outside program-slot RAM.

Guards (any failure stops the build):
  - input is the exact stock OS 1.20 (sha 100e3375...)
  - not one byte may change in 0x70000-0x741AF (program slots 18-24 at runtime)
  - every new code/data byte must lie inside a range proven free by the write-coverage run (FREE below)
  - placed areas must be empty before placement and must not overlap each other
  - checksum recomputed at 0x77FFE, boot region 0x78000-0x7FFFF unchanged
usage: make_exp.py out.BIN"""
import hashlib, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'patcher')); sys.path.insert(0, os.path.join(HERE, 'mods'))
import engine
STOCK = os.path.join(ROOT, 'build_os', 'sys_stock', 'MPC2KXL.BIN')
STOCK_SHA = '100e3375b45072c209ffa2b1dbaecbf740c8c4ea29162827ac11cc6bf9cc7bab'
VUB = ['tune', 'transpose', 'mute', 'param_copy', 'hpf', 'input_thru', 'format', 'double_stop', 'step_move']
PROGRAM_RAM = (0x70000, 0x741B0)
# measured free (never written at runtime, empty after the VU base) - filled in from exp_reloc/cov results
FREE = [(0x749a4, 0x74cb1), (0x74cf1, 0x74ef5), (0x74efe, 0x75a77), (0x75a7e, 0x75ce0), (0x75ce6, 0x761e1), (0x761ec, 0x762f3),
        (0x762fd, 0x76540), (0x76dcb, 0x77000),
        (0x77619, 0x77ffe)]   # Sampling Mode block + its own variables 0x77d50-0x77dcf (written only by the sampling run) + free tail
# measured 2026-10-16 by exp_reloc/cov/coverage.py on exp_reloc/base/vub_noregions_sampling.BIN, 18 suites incl. 24 programs
PLACE = {'zone_chop': 0x74f00, 'mute8': 0x75cf0, 'prog_mono': 0x75e00}      # module -> linear address

class Img:
    def __init__(self, d):
        self.d = bytearray(d); self.used = []
    def _check(self, lin, n, what):
        a, b = lin, lin + n
        assert not (a < PROGRAM_RAM[1] and b > PROGRAM_RAM[0]), f'{what}: touches program RAM {a:#x}-{b:#x}'
        assert any(f0 <= a and b <= f1 for f0, f1 in FREE), f'{what}: {a:#x}-{b:#x} is not inside a measured-free range'
        for u0, u1, w in self.used: assert b <= u0 or a >= u1, f'{what} overlaps {w}'
        assert not any(self.d[a:b]), f'{what}: area not empty'
        self.used.append((a, b, what))
    def put(self, lin, data, what):
        self._check(lin, len(data), what); self.d[lin:lin + len(data)] = data
    def patch(self, lin, old, new):
        assert len(old) == len(new)
        assert not (lin < PROGRAM_RAM[1] and lin + len(new) > PROGRAM_RAM[0]), f'patch {lin:#x} in program RAM'
        assert bytes(self.d[lin:lin + len(old)]) == old, f'unexpected bytes at {lin:#x}: {bytes(self.d[lin:lin + len(old)]).hex()}'
        self.d[lin:lin + len(new)] = new

def build(out):
    stock = open(STOCK, 'rb').read(); assert hashlib.sha256(stock).hexdigest() == STOCK_SHA
    base, rep = engine.build(engine.load_data(), stock, VUB)
    img = Img(base)
    import sampling, zone_chop, mute8, prog_mono, timing_q4, mute_all, wave_fast
    sizes = {'sampling': sampling.apply(img), 'zone_chop': zone_chop.apply(img, PLACE['zone_chop']),
             'prog_mono': prog_mono.apply(img, PLACE['prog_mono']),     # EXP4 (2026-10-17): MONO pads choke each other
             'timing_q4': timing_q4.apply(img),                           # EXP8 (2026-10-20): 1/32(3) -> 1/4
             'mute_all': mute_all.apply(img),                             # EXP8: ASSIGN Mode -> WINDOW -> ALL FOR BANK/PROGRAM
             'wave_fast': wave_fast.apply(img)}                           # EXP11: faster waveform
    if '--mute8' in sys.argv: sizes['mute8'] = mute8.apply(img, PLACE['mute8'])     # EXP2 default: Mute 1-4 only (user choice 2026-10-16)
    d = img.d
    assert d[PROGRAM_RAM[0]:PROGRAM_RAM[1]] == stock[PROGRAM_RAM[0]:PROGRAM_RAM[1]], 'program RAM area changed'
    d[0x77ffe:0x78000] = struct.pack('<H', sum(w for (w,) in struct.iter_unpack('<H', d[:0x77ffe])) & 0xffff)
    assert d[0x78000:] == stock[0x78000:] and len(d) == 0x80000
    open(out, 'wb').write(d)
    print('wrote', out, hashlib.sha256(d).hexdigest()[:16], 'vub:', rep['modules'], 'placed:', [(w, hex(a), b - a) for a, b, w in img.used])

if __name__ == '__main__':
    build([a for a in sys.argv[1:] if not a.startswith('--')][0])
