#!/usr/bin/env python3
"""Tests for the EXPERIMENTAL relocation build. usage: test_exp.py BUILD.BIN [test ...]
  gate_update   restore by update with the ORIGINAL file: prompt, Loading, flash-erase step equal the original's
  gate_boot     restore by boot-from-disk with the ORIGINAL on disk
  chop          chop screen: entry, 16/8/4/LAZY, EVEN, lazy taps, UNDO, BACK restores, DONE keeps, APPLY -> SLICE SOUND -> program
  sampling      SP1200 resample vs model + black box shown while processing + KEEP text without a cursor key; S900 completes
  prog24        24 programs, then chop + pad hits + MUTE page, then restore by update (the program-RAM bug scenario)
  use_restore   chop and sampling used, then restore by update
Every test writes snapshots to test_log/runs/exp_<test>/; results go to exp_reloc/test_result.json."""
import os, sys, re, json, threading
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'build_os', 'suite'))
import phases as P, harness as H
GOLD = os.path.join(ROOT, 'floppy', 'gold_floppy.img')                                   # funky.img + the ORIGINAL Akai MPC2KXL.BIN
REF = os.path.join(ROOT, 'test_log', 'runs', 'mx_ref', 'mx_ref', 'snap')
REFBOOT = os.path.join(ROOT, 'test_log', 'runs', 'exp_ref_boot', 'stock', 'snap')     # made by: test_exp.py --make-refs
UPDATE = ['press main', 'wait 1', 'down shift', 'up shift', 'wait 0.3', 'press n3', 'wait 0.3', 'down shift', 'up shift', 'wait 2.5',
          'press plus', 'wait 0.5', 'press plus', 'wait 0.5', 'press plus', 'wait 1.5', 'press f6', 'wait 3', 'snap', 'press f5', 'wait 3', 'snap',
          'wait 12', 'snap', 'wait 25', 'snap', 'exit']
POKE = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] emu.register_frame_done(function() '
        'local t=manager.machine.time:as_double() if t>0.3 and t<3 then sp:write_u8(0x35cf,0x22) sp:write_u8(0x35d0,0xe0) end end)')
BOOT_LINES = [POKE, 'wait 2', 'snap', 'wait 40', 'snap', 'exit']
R = {}
DARK = os.environ.get('DARK') == '1'          # build under test has dark mode: screens drawn by OUR OS are inverted

def diff(a, b): return ImageChops.difference(a, b).point(lambda v: 255 if v > 60 else 0).getbbox()
def L(p): return Image.open(p).convert('L')
def LO(p): im = L(p); return ImageChops.invert(im) if DARK else im      # a screen drawn by the build under test
def snaps(d): s = sorted(os.listdir(d + '/snap')) if os.path.isdir(d + '/snap') else []; return [d + '/snap/' + x for x in s]
def log(d, pre): return [l for l in H.log_text(d).split('\n') if l.startswith(pre)]
def healthy(d): h = H.health(d, []); return h['finished'] and not h['lua_errors']
def update_ok(d):
    """last 4 snaps = prompt, Loading, Loading, flash-erase step; compared with the untouched original (free-memory strip x>=230 ignored)"""
    s = snaps(d)[-4:]; r = sorted(os.listdir(REF))[3:7]
    if len(s) < 4: return False
    return all(not diff(LO(a).crop((0, 0, 230, 60)), L(os.path.join(REF, b)).crop((0, 0, 230, 60))) for a, b in zip(s, r))

def chop_enter(): return P.shift_key('n5') + ['wait 1.5', 'press f3', 'wait 1.5', 'press f3', 'wait 1.5']     # TRIM -> ZONE -> chop screen
ZD = P.ZD

def t_gate_update():
    d = H.run('exp_gate_update', ['wait 28'] + UPDATE, 'exp', GOLD, 200, sound=False)
    R['gate: restore by update (prompt / Loading / flash-erase step = original)'] = healthy(d) and update_ok(d)
def t_gate_boot():
    d = H.run('exp_gate_boot', BOOT_LINES, 'exp', GOLD, 120, sound=False)
    s = snaps(d); r = sorted(os.listdir(REFBOOT))
    ok = healthy(d) and len(s) == 2 and all(not diff(L(a), L(os.path.join(REFBOOT, b))) for a, b in zip(s, r[:2]))
    R['gate: restore by boot-from-disk (loader + original OS main page)'] = ok

def t_chop():
    Lc = P.boot() + P.load_first_file(35) + chop_enter() + ['snap', P.T(ZD, 'c16')]
    Lc += ['press f3', 'wait 1', 'snap', P.T(ZD, 'c8'), 'press f3', 'wait 1', 'snap', P.T(ZD, 'c4'), 'press f3', 'wait 1', 'snap', P.T(ZD, 'clazy')]
    Lc += ['wait 0.5'] + P.taps(P.FUNKY_CUTS[:6]) + ['wait 0.2', 'snap', 'wait 2', 'snap', P.T(ZD, 'ctaps')]
    Lc += ['press f4', 'wait 1', 'snap', P.T(ZD, 'cundo')]                                    # UNDO the last tap
    Lc += ['press window', 'wait 1.5', 'snap', P.T(ZD, 'cdone')]                              # WINDOW keeps the chop
    Lc += ['press f3', 'wait 1.5', 'press f3', 'wait 1', 'snap', 'press f1', 'wait 1.5', 'snap', P.T(ZD, 'cback')]   # change to 16, BACK restores
    Lc += ['press f3', 'wait 1.5', 'press f5', 'wait 2', 'snap', 'press f5', 'wait 12', 'snap', P.T(ZD, 'capply')]   # APPLY -> Edit window -> DO IT
    Lc += P.shift_key('n6') + ['wait 1.5', 'press f1', 'wait 1.5', 'snap', 'press main', 'wait 1'] + ['tap pad1 0', 'wait 0.6', 'tap pad2 0', 'wait 0.6', 'tap pad5 0', 'wait 1', 'snap', 'exit']
    d = H.run('exp_chop', Lc, 'exp', 'floppy/funky.img', 400, sound=False)
    z = {l.split()[1]: l for l in log(d, 'ZONES')}
    def n(tag): m = re.search(r'n=(\d+)', z.get(tag, '')); return int(m.group(1)) if m else -1
    def B(tag): m = re.search(r'B=([\d ]+)', z.get(tag, '')); return [int(x) for x in m.group(1).split()] if m else []
    ev = lambda k: [114286 * i // k for i in range(k + 1)]
    R['chop: entry keeps 16 even, F3 gives 8 and 4 even (stock split)'] = n('c16') == 16 and B('c8')[1:10] == ev(8) and B('c4')[1:6] == ev(4)
    R['chop: LAZY: start tap + 6 cut taps -> 7 zones, UNDO removes one'] = n('ctaps') == 7 and n('cundo') == 6
    R['chop: WINDOW keeps the chop; BACK restores what was there on entry'] = n('cdone') == 6 and n('cback') == 6 and B('cback') == B('cdone')
    R['chop: run healthy (no Lua errors, all screens)'] = healthy(d) and len(snaps(d)) == 14
    R['chop: screens to review by eye'] = d + '/snap'

def t_sampling():
    N = 4096; O = 300000; RLEN = 445424
    HOOK = ('lua local d=manager.machine.devices[":dsp"].spaces["l6028"] local sp=manager.machine.devices[":maincpu"].spaces["program"] local done=false local dumped=false '
            'emu.register_frame_done(function() local st=sp:read_u16(0x77d62) '
            'if st==2 and not done then done=true '
            ' for i=0,%d do d:write_u16((0x12680+%d+i)*2,(0x0007+i*13)&0xffff) d:write_u16((0x12680+%d+%d+i)*2,(0x1001+i*7)&0xffff) end print("INJECTED") manager.machine.video:snapshot() end '
            'if st==1 and done and not dumped then dumped=true local a={} local b={} '
            ' for i=0,%d do a[#a+1]=string.format("%%04x",d:read_u16((0x12680+%d+i)*2)) b[#b+1]=string.format("%%04x",d:read_u16((0x12680+%d+%d+i)*2)) end '
            ' print("OUTL "..table.concat(a," ")) print("OUTR "..table.concat(b," ")) end end)') % (N - 1, O, RLEN, O, N - 1, O, RLEN, O)
    def run(tag, keys, wait):
        Ls = ['wait 28', 'down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press right', 'wait 1', 'press window', 'wait 1.5'] + keys + \
             ['press f5', 'wait 2', HOOK, 'press f6', 'wait 3', 'press f6', 'wait %d' % wait, 'snap', 'wait 1', 'snap', 'exit']
        return H.run('exp_' + tag, Ls, 'exp', 'floppy/funky.img', 300 + wait, sound=False)
    def keep_px(d):
        im = LO(snaps(d)[-1]).convert('1'); px = im.load()
        return sum(1 for x in range(8, 200) for y in range(18, 30) if px[x, y] == 0)
    def box_px(d):                                                     # the snapshot taken when processing started: big dark box
        im = LO(snaps(d)[0]).convert('1'); px = im.load()
        return sum(1 for x in range(0, 248) for y in range(0, 60) if px[x, y] == 0)
    d = run('smp_sp1200', ['press plus', 'wait 0.8', 'press down', 'wait 0.8', 'press n2', 'press n2', 'press n0', 'press n5', 'press n0', 'press enter', 'wait 1'], 30)
    t = H.log_text(d); Rr = 22050
    def model(inp, mask=0xfff0):
        bx = 44100 - Rr; bp = bx; dx = 0; o = []
        for w in inp:
            if bp < bx: bp += Rr
            else: bp -= bx; dx = w & mask
            o.append(dx)
        return o
    good = []
    for tag, mul, base in (('OUTL', 13, 0x0007), ('OUTR', 7, 0x1001)):
        m = re.search(tag + r' ([0-9a-f ]+)', t)
        if not m: good.append(False); continue
        out = [int(x, 16) for x in m.group(1).split()]
        mod = model([0] * 8 + [(base + i * mul) & 0xffff for i in range(len(out))])[8:]
        good.append(sum(1 for a, b in zip(out, mod) if a == b) >= len(out) - 2)
    kp, bp = keep_px(d), box_px(d)
    R[f'sampling SP1200: L/R match the model'] = all(good) and len(good) == 2
    R[f'sampling SP1200: black processing box shown (dark px {bp}), KEEP text shown without a key (px {kp})'] = bp > 2500 and kp > 120
    d2 = run('smp_s900', ['press plus', 'wait 0.8', 'press plus', 'wait 0.8'], 70)
    R[f'sampling S900: completes, KEEP text shown (px {keep_px(d2)})'] = 'OUTL' in H.log_text(d2) and keep_px(d2) > 120
    R['sampling: screens to review by eye'] = [d + '/snap', d2 + '/snap']

def programs(n):
    Lp = P.shift_key('n6') + ['wait 1.5', 'press f1', 'wait 1.5']
    for k in range(n):
        Lp += ['press window', 'wait 1.2', 'press f3', 'wait 1.2', 'press f5', 'wait 1.5', 'press main', 'wait 0.8'] + P.shift_key('n6') + ['wait 1.2', 'press f1', 'wait 1.2']
    return Lp + ['press main', 'wait 1']
def t_prog24():
    Lp = P.boot() + P.load_first_file(35) + programs(23) + ['snap']
    Lp += chop_enter() + ['press f3', 'wait 1', 'press f3', 'wait 1', 'press f3', 'wait 1', 'wait 0.5'] + P.taps(P.FUNKY_CUTS[:5]) + ['wait 2', 'snap', P.T(ZD, 'p24chop'), 'press f6', 'wait 1.5']
    Lp += ['press main', 'wait 1', 'tap pad1 0', 'wait 0.5', 'tap pad3 0', 'wait 0.5'] + P.shift_key('n6') + ['wait 1.5', 'press f1', 'wait 1.5', 'snap'] + UPDATE
    d = H.run('exp_prog24', Lp, 'exp', GOLD, 700, sound=False)
    z = ' '.join(log(d, 'ZONES'))
    R['prog24: 24 programs, chop still works (start tap + 5 cuts -> 6 zones)'] = 'n=6' in z
    R['prog24: then restore by update = original'] = healthy(d) and update_ok(d)
    R['prog24: screens'] = d + '/snap'

def t_use_restore():
    Lu = P.boot() + P.load_first_file(35) + chop_enter() + ['press f3', 'wait 1', 'press f3', 'wait 1', 'press f3', 'wait 1', 'wait 0.5'] + P.taps(P.FUNKY_CUTS) + ['wait 2', 'press f6', 'wait 1.5']
    Lu += ['press main', 'wait 1', 'down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press right', 'wait 1', 'press window', 'wait 1.5',
           'press plus', 'wait 0.8', 'press f5', 'wait 2', 'press f6', 'wait 3', 'press f6', 'wait 14', 'press f6', 'wait 30', 'press f5', 'wait 3'] + UPDATE
    d = H.run('exp_use_restore', Lu, 'exp', GOLD, 500, sound=False)
    R['use then restore: chop + SP1200 sampling used, restore by update = original'] = healthy(d) and update_ok(d)


def t_twin():
    """same script on the experimental build and on the VU base without DAVEY code: every screen must be pixel-identical
    (catches garbled text / corrupted screens anywhere outside our own chop and sampling screens)"""
    Lt = [l for l in P.tour()['lines'] if l != 'exit'] + ['press main', 'wait 1'] + programs(23) + P.shift_key('n6') + ['wait 1.5', 'press f1', 'wait 1.5', 'snap'] + \
         P.shift_key('n8') + ['wait 1.5', 'snap', 'press f1', 'wait 1', 'snap', 'press f2', 'wait 1', 'snap', 'press main', 'wait 1', 'snap', 'exit']
    a = H.run('exp_twin', Lt, 'exp', 'floppy/funky.img', 900, sound=False)
    b = H.run('exp_twin_base', Lt, 'expbase', 'floppy/funky.img', 900, sound=False)
    sa, sb = snaps(a), snaps(b)
    bad = [i for i, (x, y) in enumerate(zip(sa, sb)) if diff(LO(x), L(y))]
    R[f'twin: {len(sa)} screens vs the VU base, identical (differing: {bad[:12]})'] = healthy(a) and healthy(b) and len(sa) == len(sb) and len(sa) > 50 and not bad

def t_mute():
    d = H.run('exp_mute', P.mute_matrix()['lines'], 'exp', 'floppy/funky.img', 1300, sound=False)
    rows = [l.split(' ', 2) for l in H.log_text(d).split('\n') if l.startswith('PLAYING')]
    r = {x[1]: sorted(set(t.split(':')[1] for t in (x[2].split() if len(x) > 2 else []))) for x in rows}
    bad = []; pairs = sorted(set(k.rsplit('_', 1)[0] for k in r))
    for p in pairs:
        g1, g2 = int(p[1]), int(p[2]); a, b = r.get(p + '_a'), r.get(p + '_b'); exp = (g1 == g2 and g1 != 0)
        killed = a is not None and '37' in a and b is not None and '37' not in b
        if not ((killed == exp) and ('36' in (b or []))): bad.append(p)
    R[f'mute: MUTE 1-8 matrix, {len(pairs)} pairs (same group chokes, others do not), failing {bad}'] = healthy(d) and not bad and len(pairs) >= 12
def t_vub():
    ok = True; where = []
    for name, fn, cap in (('v1', P.vub_feat1, 600), ('v2', P.vub_feat2, 450)):
        a = H.run('exp_' + name, fn()['lines'], 'exp', 'floppy/funky.img', cap, sound=False)
        b = H.run('exp_' + name + '_base', fn()['lines'], 'expbase', 'floppy/funky.img', cap, sound=False)
        sa, sb = snaps(a), snaps(b); bad = [i for i, (x, y) in enumerate(zip(sa, sb)) if diff(LO(x), L(y))]
        ok &= healthy(a) and len(sa) == len(sb) and len(sa) > 5 and not bad; where.append((name, len(sa), bad[:8]))
    R[f'vub: tune/transpose/ALL/double STOP screens identical to the VU base {where}'] = ok

def t_mute4():
    pairs = ((1, 1), (2, 2), (3, 3), (4, 4), (1, 2), (3, 4), (2, 3), (1, 4), (4, 0), (0, 4), (0, 0), (1, 0))
    d = H.run('exp_mute4', P.mute_matrix(pairs)['lines'], 'exp', 'floppy/funky.img', 1000, sound=False)
    rows = [l.split(' ', 2) for l in H.log_text(d).split('\n') if l.startswith('PLAYING')]
    r = {x[1]: sorted(set(t.split(':')[1] for t in (x[2].split() if len(x) > 2 else []))) for x in rows}
    bad = []; got = sorted(set(k.rsplit('_', 1)[0] for k in r))
    for p in got:
        g1, g2 = int(p[1]), int(p[2]); a, b = r.get(p + '_a'), r.get(p + '_b'); exp = (g1 == g2 and g1 != 0)
        killed = a is not None and '37' in a and b is not None and '37' not in b
        if not ((killed == exp) and ('36' in (b or []))): bad.append(p)
    R[f'mute: Mute 1-4 matrix, {len(got)} pairs, failing {bad}'] = healthy(d) and not bad and len(got) == len(pairs)

def t_chop_preview():
    """VU-style editing inside the chop screen: pad n selects (and plays) slice n, cursor to End + data trims the shared
    boundary, cursor to Zone + data steps slices, after a lazy chop pads select slices"""
    FLD = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print("FLD %s field="..sp:read_u16(0x582b0+0x8d58).." cur="..sp:read_u8(0x582b0+0xd7dd))')
    L2 = P.boot() + P.load_first_file(35) + chop_enter() + ['press f3', 'wait 1']                                    # 8 even
    L2 += ['tap pad3 0', 'wait 0.6', P.T(FLD, 'pad3'), 'press right', 'wait 0.6', 'press plus', 'wait 0.5', 'press plus', 'wait 0.5', P.T(ZD, 'trim'), P.T(FLD, 'end'), 'snap']
    L2 += ['press right', 'wait 0.6', 'press plus', 'wait 0.6', P.T(FLD, 'zone'), 'snap']
    L2 += ['press f3', 'wait 1', 'press f3', 'wait 1', 'wait 0.5'] + P.taps(P.FUNKY_CUTS[:5]) + ['wait 3', 'tap pad2 0', 'wait 0.6', P.T(FLD, 'lzpad2'), P.T(ZD, 'lz'), 'snap', 'exit']
    d = H.run('exp_chop_preview', L2, 'exp', 'floppy/funky.img', 300, sound=False)
    f = {l.split()[1]: l for l in log(d, 'FLD')}; z = {l.split()[1]: l for l in log(d, 'ZONES')}
    cur = lambda k: int(re.search(r'cur=(\d+)', f.get(k, 'cur=-1')).group(1)); fld = lambda k: int(re.search(r'field=(\d+)', f.get(k, 'field=-1')).group(1))
    B = lambda k: [int(x) for x in re.search(r'B=([\d ]+)', z.get(k, 'B=')).group(1).split()] if k in z else []
    R['chop preview: pad 3 selects slice 3'] = cur('pad3') == 3
    R['chop preview: cursor to End, data +2 moves the shared boundary (zone 3 end = zone 4 start)'] = fld('end') == 3 and len(B('trim')) > 4 and B('trim')[4] == 42857 + 2
    R['chop preview: cursor to Zone, data + steps to slice 4'] = fld('zone') == 4 and cur('zone') == 4
    R['chop preview: after a lazy chop (6 zones) pad 2 selects slice 2'] = 'n=6' in z.get('lz', '') and cur('lzpad2') == 2
    R['chop preview: run healthy'] = healthy(d)

def t_rec_normal():
    """a normal recording (Sampling Mode OFF): must reach KEEP or RETRY and keep the sound, screen for screen like the VU base.
    (2026-10-16: the close fix had broken this path and crashed the real unit; the emulator records silence, threshold set to -inf)"""
    Lr = P.boot() + P.load_first_file(35) + ['down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press down', 'wait 0.5'] + \
         ['press minus', 'wait 0.1'] * 70 + ['wait 0.5', 'press f6', 'wait 2', 'press f6', 'wait 12', 'snap', 'press f5', 'wait 3', 'snap'] + \
         P.shift_key('n5') + ['wait 2', 'snap', 'press main', 'wait 1', 'snap', 'exit']
    a = H.run('exp_rec_normal', Lr, 'exp', 'floppy/funky.img', 300, sound=False)
    b = H.run('exp_rec_normal_base', Lr, 'expbase', 'floppy/funky.img', 300, sound=False)
    sa, sb = snaps(a), snaps(b); bad = [i for i, (x, y) in enumerate(zip(sa, sb)) if diff(LO(x), L(y))]
    R[f'normal recording (Sampling OFF): KEEP, TRIM and main screens identical to the VU base (differing {bad})'] = healthy(a) and len(sa) == 4 and len(sa) == len(sb) and not bad

def t_digit():
    """chop screen: SHIFT+cursor sets the wheel step on St/End exactly like stock TRIM (the chop redraw used to reset it).
    The same key sequence runs on stock TRIM (St) and in the chop screen (End); the step sizes must match and include 10 and 1000."""
    SEQ = lambda D: ['press plus', 'wait 0.6', P.T(D, 'p1')] + ['down shift', 'wait 0.3', 'press left', 'wait 0.3', 'up shift', 'wait 1'] + \
        ['down shift', 'wait 0.3', 'press plus', 'wait 0.3', 'up shift', 'wait 1', P.T(D, 'p10'), 'press plus', 'wait 0.6', P.T(D, 'p10b')] + \
        ['down shift', 'wait 0.3', 'press left', 'wait 0.3', 'press left', 'wait 0.3', 'up shift', 'wait 1', 'down shift', 'wait 0.3', 'press plus', 'wait 0.3', 'up shift', 'wait 1', P.T(D, 'p1000')] + \
        ['down shift', 'wait 0.3', 'press right', 'wait 0.3', 'press right', 'wait 0.3', 'press right', 'wait 0.3', 'up shift', 'wait 1', 'down shift', 'wait 0.3', 'press plus', 'wait 0.3', 'up shift', 'wait 1', P.T(D, 'back1'), 'snap', 'exit']
    DC = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print("DG %s v="..(sp:read_u16(0x582b0+0x8e72+8)+65536*sp:read_u16(0x582b0+0x8e74+8)))')
    DT = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local o=sp:read_u16(0x582b0+0xd7c2) local s=sp:read_u16(0x582b0+0xd7c4) print("DG %s v="..sp:read_u32(s*16+o+0x26))')
    Lc = P.boot() + P.load_first_file(35) + chop_enter() + ['press right', 'wait 0.6', P.T(DC, 'a')] + SEQ(DC)
    Lt = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', 'press down', 'wait 0.6', P.T(DT, 'a')] + SEQ(DT)
    steps = []
    for name, L, b in (('exp_digit', Lc, 'exp'), ('exp_digit_stock', Lt, 'stock')):
        d = H.run(name, L, b, 'floppy/funky.img', 200, sound=False)
        v = {l.split()[1]: int(re.search(r'v=(\d+)', l).group(1)) for l in log(d, 'DG')}
        ks = ['a', 'p1', 'p10', 'p10b', 'p1000', 'back1']
        steps.append([v[ks[k + 1]] - v[ks[k]] for k in range(5)] if all(k in v for k in ks) else None)
        R[f'digit: {b} run healthy'] = healthy(d)
    R[f'digit: chop End steps == stock TRIM St steps after SHIFT+cursor (chop {steps[0]}, stock {steps[1]})'] = steps[0] is not None and steps[0] == steps[1] and 10 in steps[0] and 1000 in steps[0]

def t_prog_mono():
    """program MONO: MONO pads choke each other; every other POLY/MONO pairing and the same-pad POLY re-hit stay stock"""
    def ovl(pad, m): return [f'tap pad{pad} 0', 'wait 0.8'] + ['press minus', 'wait 0.3'] * 3 + (['press plus', 'wait 0.3'] if m else []) + ['wait 0.5']
    L = P.boot() + P.load_first_file(37) + P.pad2_gets_sound() + P.shift_key('n6') + ['wait 1.5', 'press f1', 'wait 2', 'press f2', 'wait 2'] + ['press right', 'wait 0.5'] * 7
    for m1, m2 in ((0, 0), (1, 1), (1, 0), (0, 1)):
        L += ovl(1, m1) + ovl(2, m2) + ['snap', 'wait 4', 'tap pad1 0', 'wait 0.45', P.T(P.VOICES_PN, f'o{m1}{m2}_a'), 'tap pad2 0', 'wait 0.45', P.T(P.VOICES_PN, f'o{m1}{m2}_b'), 'wait 4']
    L += ovl(1, 1) + ['wait 4', 'tap pad1 0', 'wait 0.45', 'tap pad1 0', 'wait 0.45', P.T(P.VOICES_PN, 'rehit_mono'), 'wait 4']
    L += ovl(1, 0) + ['wait 4', 'tap pad1 0', 'wait 0.45', 'tap pad1 0', 'wait 0.45', P.T(P.VOICES_PN, 'rehit_poly'), 'exit']
    d = H.run('exp_prog_mono', L, 'exp', 'floppy/funky.img', 400, sound=False)
    pv = {l.split()[1]: sorted(l.split()[2:]) for l in log(d, 'PLAYING')}
    want = {'o00_b': ['0:36', '0:37'], 'o11_b': ['0:36'], 'o10_b': ['0:36', '0:37'], 'o01_b': ['0:36', '0:37'], 'rehit_mono': ['0:37'], 'rehit_poly': ['0:37', '0:37']}
    bad = {k: pv.get(k) for k, w in want.items() if pv.get(k) != w}
    R[f'prog mono: MONO+MONO choke, other pairings and re-hits as stock (bad {bad})'] = not bad
    R['prog mono: run healthy'] = healthy(d)

def t_f6play():
    """chop screen F6 PLAY (replaces DONE, 2026-10-17): held = current slice sounds, release stops it (audio measured from a WAV capture)"""
    import subprocess, struct
    TM = lambda t: 'lua print(string.format("TM %s %.3f","' + t + '",manager.machine.time:as_double()))'
    def run(hold_extra):
        L = P.boot() + P.load_first_file(35) + chop_enter() + ['press f3', 'wait 1', 'press f3', 'wait 1.5', TM('q0'), 'wait 1.5', TM('q1'), 'down f6', TM('h0'), 'wait 0.05', TM('h1')]
        L += (['wait %.2f' % hold_extra] if hold_extra else []) + ['up f6', 'wait 1.5', 'exit']
        sc = os.path.join(ROOT, 'test_log', 'f6play.txt'); open(sc, 'w').write('\n'.join(L) + '\n'); w = os.path.join(ROOT, 'test_log', 'f6play.wav')
        out = subprocess.run([os.path.join(os.environ.get('MPC_EMU', ROOT), 'tools/dev/run_script_snd.sh'), sc, 'floppy/funky.img'], cwd=ROOT, env=dict(os.environ, SYSDIR=H.SYS['exp'], CAP='150', WAV=w), capture_output=True, text=True)
        lg = open(os.path.dirname(os.path.dirname(out.stdout.strip().split('\n')[-1])) + '/out.log', errors='replace').read()
        T = {m.group(1): float(m.group(2)) for m in re.finditer(r'TM (\S+) ([\d.]+)', lg)}
        raw = open(w, 'rb').read(); ch, sr = struct.unpack_from('<HI', raw, 22); i = raw.index(b'data'); dl, = struct.unpack_from('<I', raw, i + 4)   # plain RIFF read (kept from when build_os/suite/chunk.py shadowed the stdlib chunk module)
        a = struct.unpack_from('<%dh' % (min(dl, len(raw) - i - 8) // 2), raw, i + 8)
        rms = lambda x, y: (sum(v * v for v in a[int(x * sr) * ch:int(y * sr) * ch]) / max(1, int((y - x) * sr) * ch)) ** 0.5
        return rms(T['q0'], T['q1']), rms(T['h0'], T['h1']), rms(T['h1'] + 0.15, T['h1'] + 0.35)
    q, h, rel = run(0); _, _, held = run(0.45)
    R[f'f6play: quiet {q:.0f}, F6 held sounds {h:.0f}, released -> {rel:.0f} (held through: {held:.0f})'] = q < 5 and h > 50 and rel < 5 and held > 50

def t_tpad():
    """TRIM page pad select (2026-10-17): after a chop + APPLY, a pad hit on TRIM selects that pad's sound (name, End, waveform)
    and still sounds; an empty pad keeps the current sound. Audio from a WAV capture."""
    import subprocess, struct
    N = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local o=sp:read_u16(0x582b0+0xd7c2) local s=sp:read_u16(0x582b0+0xd7c4) local t={} for i=0x12,0x1d do t[#t+1]=string.char(sp:read_u8(s*16+o+i)) end print("SND %s "..table.concat(t))'
    TM = lambda t: 'lua print(string.format("TM %s %.3f","' + t + '",manager.machine.time:as_double()))'
    L = P.boot() + P.load_first_file(35) + chop_enter() + ['press f3', 'wait 1', 'press f5', 'wait 2', 'press f5', 'wait 12', 'press main', 'wait 1']
    L += P.shift_key('n5') + ['wait 2', P.T(N, 'start'), 'wait 1', TM('q0'), 'wait 1', TM('q1'), 'tap pad3 0', TM('p3'), 'wait 1.5', P.T(N, 'pad3'), 'snap',
                              'tap pad1 0', 'wait 1.5', P.T(N, 'pad1'), 'snap', 'tap pad12 0', 'wait 1.5', P.T(N, 'pad12'), 'snap', 'exit']
    sc = os.path.join(ROOT, 'test_log', 'tpad.txt'); open(sc, 'w').write('\n'.join(L) + '\n'); w = os.path.join(ROOT, 'test_log', 'tpad.wav')
    out = subprocess.run([os.path.join(os.environ.get('MPC_EMU', ROOT), 'tools/dev/run_script_snd.sh'), sc, 'floppy/funky.img'], cwd=ROOT, env=dict(os.environ, SYSDIR=H.SYS['exp'], CAP='200', WAV=w), capture_output=True, text=True)
    sess = os.path.dirname(os.path.dirname(out.stdout.strip().split('\n')[-1])); lg = open(sess + '/out.log', errors='replace').read()
    T = {m.group(1): float(m.group(2)) for m in re.finditer(r'TM (\S+) ([\d.]+)', lg)}
    nm = {m.group(1): m.group(2).strip() for m in re.finditer(r'SND (\S+) (.*)', lg)}
    raw = open(w, 'rb').read(); ch, sr = struct.unpack_from('<HI', raw, 22); i = raw.index(b'data'); dl, = struct.unpack_from('<I', raw, i + 4)
    a = struct.unpack_from('<%dh' % (min(dl, len(raw) - i - 8) // 2), raw, i + 8)
    rms = lambda x, y: (sum(v * v for v in a[int(x * sr) * ch:int(y * sr) * ch]) / max(1, int((y - x) * sr) * ch)) ** 0.5
    q, hit = rms(T['q0'], T['q1']), rms(T['p3'] - 0.4, T['p3'] + 0.2)
    R[f"tpad: pad3 -> {nm.get('pad3')}, pad1 -> {nm.get('pad1')}, empty pad12 keeps {nm.get('pad12')} (start {nm.get('start')})"] = \
        nm.get('start') == 'FUNKY' and nm.get('pad3') == 'FUNKY3' and nm.get('pad1') == 'FUNKY1' and nm.get('pad12') == 'FUNKY1'
    R[f'tpad: the pad hit still sounds (quiet {q:.0f}, hit {hit:.0f})'] = q < 5 and hit > 50
    R['tpad: screens to review by eye'] = sess + '/snap'

def t_lazy_repeat():
    """LAZY: each pad cuts once per run (user report 2026-10-17): pad1 starts, pad2, pad3 cut, pad2 again is ignored, pad4 cuts;
    UNDO frees pad4, which can cut again"""
    L = P.boot() + P.load_first_file(35) + chop_enter() + ['press f3', 'wait 1', 'press f3', 'wait 1', 'press f3', 'wait 1.5']        # 16 -> 8 -> 4 -> LAZY
    L += ['tap pad1 0', 'wait 0.35', 'tap pad2 0', 'wait 0.35', 'tap pad3 0', 'wait 0.35', 'tap pad2 0', 'wait 0.35', 'tap pad4 0', 'wait 2.5', P.T(ZD, 'after'), 'snap']
    L += ['press f4', 'wait 1', P.T(ZD, 'undo'), 'snap', 'exit']
    d = H.run('exp_lazy_repeat', L, 'exp', 'floppy/funky.img', 150, sound=False)
    z = {l.split()[1]: l for l in log(d, 'ZONES')}
    n = lambda k: int(re.search(r'n=(\d+)', z.get(k, 'n=-1')).group(1))
    R[f"lazy repeat: pads 1,2,3,2,4 give {n('after')} slices (4 expected, repeated pad2 ignored), UNDO -> {n('undo')} (3)"] = n('after') == 4 and n('undo') == 3
    R['lazy repeat: run healthy'] = healthy(d)

def t_timing():
    """Full Timing list (2026-10-22): from the default 1/16 the DATA wheel reaches 1/32(3) (stock value 6, still the stock
    grid and the same picture as the stock OS), then 1/4 (7, grid 96, off-grid hits land on quarter notes) and 1/4(3)
    (8, grid 64), and stops there"""
    G = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print("GRID %s timing="..sp:read_u8(0x22e67).." grid="..sp:read_u16(0xfe70+0x4856))'
    def run(n, build, rec=True, step=False):
        L = P.boot() + P.load_first_file(37) + ['press main', 'wait 1', 'press down', 'wait 0.4', 'press right', 'wait 0.4', 'press right', 'wait 0.6']
        L += ['press plus', 'wait 0.4'] * n + ['wait 0.5', 'snap', P.T(G, 'set')]
        if rec:
            L += ['down rec', 'wait 0.2', 'press play', 'wait 0.2', 'up rec', 'wait 2.5', 'tap pad1 0', P.T(G, 'hit1'), 'wait 0.62', 'tap pad1 0', 'wait 0.71', 'tap pad1 0', 'wait 1.5', 'press stop', 'wait 1']
        if step: L += ['press f1', 'wait 2'] + ['press stepnext', 'wait 0.8', 'snap'] * 9
        return H.run(f'exp_timing_{build}_{n}', L + ['exit'], build, 'floppy/funky.img', 150, sound=False)
    def grid(d, tag): g = (log(d, 'GRID ' + tag) or ['timing=-1 grid=-1'])[0]; return g.split(' ', 2)[-1]
    ds = run(3, 'stock', rec=False); d6 = run(3, 'exp')
    same = len(snaps(ds)) > 0 and len(snaps(d6)) > 0 and not diff(L(snaps(ds)[0]).crop((0, 0, 248, 60)), LO(snaps(d6)[0]).crop((0, 0, 248, 60)))
    R[f'timing: 1/32(3) kept: value 6, stock grid ({grid(d6, "hit1")}), screen = stock OS'] = grid(d6, 'hit1') == 'timing=6 grid=8' and same
    d7 = run(4, 'exp', step=True)
    s = snaps(d7)
    found = sum(1 for p in s[1:] if sum(1 for x in range(20, 120) for y in range(11, 20) if L_px(p, x, y)) > 60)    # an event row (">N: 37/A01 ...")
    R[f'timing: 1/4 = value 7, grid 96 ({grid(d7, "hit1")}), off-grid hits on quarter notes: {found} of 3'] = grid(d7, 'hit1') == 'timing=7 grid=96' and found == 3
    d8 = run(5, 'exp')
    R[f'timing: 1/4(3) = value 8, grid 64 ({grid(d8, "hit1")})'] = grid(d8, 'hit1') == 'timing=8 grid=64'
    d9 = run(9, 'exp', rec=False)
    R[f'timing: the wheel stops at 1/4(3) ({grid(d9, "set")})'] = grid(d9, 'set').startswith('timing=8 ')
    texts = [snaps(d)[0] for d in (d6, d7, d8) if snaps(d)]
    R['timing: 1/32(3), 1/4, 1/4(3) look different'] = len(texts) == 3 and all(diff(LO(a).crop((0, 0, 248, 60)), LO(b).crop((0, 0, 248, 60))) for a, b in ((texts[0], texts[1]), (texts[1], texts[2])))
    R['timing: runs healthy'] = all(healthy(d) for d in (d6, d7, d8, d9))

def t_timing_disk():
    """.ALL files with 1/4 (2026-10-22): DAVEY saves the header with 1/8 + a "DAVEYTC" trailer; a stock OS loads that file
    as 1/8 and records without the divide error a raw value 7 causes; DAVEY loads it back as 1/4; a stock-saved .ALL
    loads on DAVEY unchanged"""
    sys.path.insert(0, os.path.join(ROOT, 'exp_reloc'))
    from fat12 import read as fat_read
    G = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print("TC %s "..sp:read_u8(0x22e67).." grid="..sp:read_u16(0xfe70+0x4856))'
    DIV = 'lua manager.machine.debugger:command("bpset 401,1,{printf \\"WR DIVERR\\"; g}") print("BPDIV")'
    CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
    def tc_field(n): return ['press main', 'wait 1', 'press down', 'wait 0.4', 'press right', 'wait 0.4', 'press right', 'wait 0.6'] + ['press plus', 'wait 0.4'] * n
    SAVE = P.shift_key('n3') + ['wait 2', 'press f2', 'wait 1.5', 'press up', 'wait 0.5', 'press f6', 'wait 2', 'press f5', 'wait 6', 'snap']
    LOAD = ['press main', 'wait 1'] + P.shift_key('n3') + ['wait 2', 'press f1', 'wait 1.5', 'press plus', 'wait 0.8', 'press plus', 'wait 0.8', 'snap', 'press f6', 'wait 3', 'snap', 'press f5', 'wait 8', 'snap', 'press main', 'wait 1.5', 'snap']
    REC = ['down rec', 'wait 0.2', 'press play', 'wait 0.2', 'up rec', 'wait 2.5', 'tap pad1 0', 'wait 0.62', 'tap pad1 0', 'wait 1.5', 'press stop', 'wait 1.5', 'snap']
    def tc(d, tag): return ((log(d, 'TC ' + tag) or ['TC x -1'])[0].split(' ', 2)[-1])
    da = H.run('exp_tdisk_save', P.boot() + P.load_first_file(37) + tc_field(4) + SAVE + [P.T(G, 'after'), 'exit'], 'exp', 'floppy/funky.img', 150, sound=False)
    fa = da + '/floppy_after.img'
    f = fat_read(fa, 'ALL_SEQ_') if os.path.exists(fa) else b''
    R[f'timing disk: DAVEY save keeps 1/4 in RAM ({tc(da, "after")}), file header 1/8 ({f[0x717] if f else None}), trailer {f[-8:] if f else None}'] = tc(da, 'after').startswith('7 ') and len(f) > 0x800 and f[0x717] == 1 and f[-8:] == b'DAVEYTC\x07'
    ds = H.run('exp_tdisk_stock', P.boot() + [DIV] + LOAD + [P.T(G, 'loaded')] + REC + [P.T(G, 'rec'), CON, 'exit'], 'stock', fa, 160, sound=False)
    div = any('DIVERR' in l for l in log(ds, 'CON'))
    R[f'timing disk: stock OS loads it as 1/8 ({tc(ds, "loaded")}) and records without a divide error ({"ERROR" if div else "none"})'] = tc(ds, 'loaded').startswith('1 ') and not div and healthy(ds)
    de = H.run('exp_tdisk_load', P.boot() + LOAD + [P.T(G, 'loaded'), 'exit'], 'exp', fa, 120, sound=False)
    R[f'timing disk: DAVEY loads it back as 1/4 ({tc(de, "loaded")})'] = tc(de, 'loaded').startswith('7 ')
    dk = H.run('exp_tdisk_stocksave', P.boot() + P.load_first_file(37) + tc_field(2) + SAVE + [P.T(G, 'after'), 'exit'], 'stock', 'floppy/funky.img', 150, sound=False)
    dl = H.run('exp_tdisk_stockload', P.boot() + LOAD + [P.T(G, 'loaded'), 'exit'], 'exp', dk + '/floppy_after.img', 120, sound=False)
    R[f'timing disk: a stock-saved .ALL (1/32 = {tc(dk, "after")}) loads on DAVEY unchanged ({tc(dl, "loaded")})'] = tc(dk, 'after').startswith('5 ') and tc(dl, 'loaded').startswith('5 ')
    R['timing disk: runs healthy'] = all(healthy(d) for d in (da, de, dk, dl))

def t_chop_opts():
    """patcher options Chop: even split / Lazy chop (2026-10-22): a build with only one of them offers only that kind
    on the chop screen (entry and F3: even = 16 -> 8 -> 4 -> 16, lazy = always LAZY)"""
    import subprocess, hashlib
    sys.path.insert(0, os.path.join(HERE, 'mods')); sys.path.insert(0, HERE)
    import make_exp, engine, zone_chop
    base, _ = engine.build(engine.load_data(), open(make_exp.STOCK, 'rb').read(), make_exp.VUB)
    zone_chop.apply(make_exp.Img(base), make_exp.PLACE['zone_chop']); vmode = zone_chop.OPT_AT - 1
    M = f'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print("MODE %s "..sp:read_u8({vmode}))'
    for kind, want in (('even', [0, 1, 2, 0]), ('lazy', [3, 3, 3, 3])):
        sysd = os.path.join(ROOT, 'test_log', 'sys_chop_' + kind); os.makedirs(sysd, exist_ok=True)
        subprocess.run([sys.executable, os.path.join(HERE, 'make_exp.py'), sysd + '/MPC2KXL.BIN', '--chop=' + kind], check=True, capture_output=True)
        H.SYS['chop_' + kind] = sysd
        L = P.boot() + P.load_first_file(37) + chop_enter() + ['snap', P.T(M, 'e')] + ['press f3', 'wait 1', 'snap', P.T(M, 'f')] * 3 + ['press f1', 'wait 1', 'exit']
        d = H.run('exp_chop_' + kind, L, 'chop_' + kind, 'floppy/funky.img', 120, sound=False)
        got = [int(l.split()[-1]) for l in log(d, 'MODE')]
        R[f'chop opts: {kind} only: modes {got} (want {want})'] = got == want and healthy(d)

def L_px(path, x, y):
    from PIL import Image
    im = Image.open(path).convert('L'); return im.getpixel((x, y)) < 100

def t_mute_all():
    """ASSIGN > Mode > WINDOW (2026-10-21): vubeatz's ALL FOR window copies the pad's Mode to the bank (16 pads) or the
    whole program (64 notes); CANCEL changes nothing; every path returns to the ASSIGN page; pads set this way choke"""
    MODES = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local o=sp:read_u16(0x5c*4) local s=sp:read_u16(0x5c*4+2) local L=s*16+o '
             'local t={} for n=0,63 do t[#t+1]=string.format("%x",sp:read_u8(L+0x1e+0x18*n)) end print("MODES %s "..table.concat(t," "))')
    bank_a = sorted(n - 35 for n in (37, 36, 42, 82, 40, 38, 46, 44, 48, 47, 45, 43, 49, 55, 51, 53))
    res = {}
    for key, name in (('f5', 'program'), ('f4', 'bank'), ('f2', 'cancel')):
        L = P.boot() + P.load_first_file(37) + P.pad2_gets_sound() + P.shift_key('n6') + ['wait 1.5', 'press f1', 'wait 2'] + P.set_mode_for_pad(1, 2)
        L += ['wait 0.5', 'snap', 'press window', 'wait 1.5', 'snap', f'press {key}', 'wait 2', 'snap', P.T(MODES, name)]
        if name == 'program':            # A01 and A02 now share MUTE 2: hitting A02 must cut A01
            L += ['wait 3', 'tap pad1 0', 'wait 0.45', 'tap pad2 0', 'wait 0.45', P.T(P.VOICES_PN, 'choke')]
        L += ['exit']
        d = H.run(f'exp_mute_all_{name}', L, 'exp', 'floppy/funky.img', 150, sound=False)
        m = [int(x, 16) for x in (log(d, 'MODES') or ['MODES x'])[0].split()[2:]]
        s_ = snaps(d)
        back = len(s_) >= 3 and not diff(L_img(s_[-3]), L_img(s_[-1]))     # just before WINDOW vs after the button
        res[name] = (m, back, d, log(d, 'PLAYING'))
    pm, pb, _, pv = res['program']; bm, bb, _, _ = res['bank']; cm, cb, _, _ = res['cancel']
    R[f'mute all: PROGRAM -> all 64 notes MUTE 2 ({pm.count(5)}), back on ASSIGN'] = len(pm) == 64 and pm.count(5) == 64 and pb
    R[f'mute all: BANK -> exactly bank A ({[i for i, v in enumerate(bm) if v == 5] == bank_a}), back on ASSIGN'] = [i for i, v in enumerate(bm) if v == 5] == bank_a and bb
    R['mute all: CANCEL changes nothing (only A01 = MUTE 2), back on ASSIGN'] = [i for i, v in enumerate(cm) if v == 5] == [2] and cb
    R[f'mute all: pads set by PROGRAM choke each other ({pv})'] = bool(pv) and pv[0].split()[2:] == ['0:36']
    R['mute all: runs healthy'] = all(healthy(r[2]) for r in res.values())

def L_img(p):
    from PIL import Image
    return Image.open(p)

def t_wave_chop():
    """waveform keeps loading in the chop screen (user report 2026-10-21): record a long sound, open the chop screen at once;
    the stock waveform calculation (7C00:03DC counts 0..0xF5 columns) must still reach the end"""
    C = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print("WCOUNT %s "..sp:read_u16(0x7c3dc))'
    L = P.boot() + P.load_first_file(35) + ['down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press down', 'wait 0.5']
    L += ['press minus', 'wait 0.1'] * 70 + ['wait 0.5', 'press f6', 'wait 2', 'press f6', 'wait 12', 'press f5', 'wait 3']       # 10 s stereo recording, KEEP
    L += P.shift_key('n5') + ['wait 0.3', 'press f3', 'wait 0.6', 'press f3', 'wait 0.3', P.T(C, 'enter'), 'wait 20', P.T(C, 'later'), 'snap', 'exit']
    d = H.run('exp_wave_chop', L, 'exp', 'floppy/funky.img', 150, sound=False)
    c = {l.split()[1]: int(l.split()[2]) for l in log(d, 'WCOUNT')}
    # with the fast waveform (EXP11) the calculation usually finishes before the chop screen opens; the EXP10 run proved
    # the unfinished case (193 -> 245; EXP8 froze at 148). Required now: complete in the chop screen either way.
    R[f"wave chop: waveform calculation in the chop screen {c.get('enter')} -> {c.get('later')} of 245 columns"] = c.get('enter', 999) <= 245 and c.get('later') == 245
    R['wave chop: run healthy'] = healthy(d)

def t_wave_fast():
    """fast waveform (2026-10-21): a 10 s recording's waveform is complete within ~1 s of opening TRIM (stock ~5 s), and
    FUNKY's 245 columns match the VU base's (stock) calculation within 2 pixel rows, >= 80 % identical"""
    C = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print(string.format("WT %.2f %d",manager.machine.time:as_double(),sp:read_u16(0x7c3dc)))'
    L = P.boot() + P.load_first_file(35) + ['down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press down', 'wait 0.5']
    L += ['press minus', 'wait 0.1'] * 70 + ['wait 0.5', 'press f6', 'wait 2', 'press f6', 'wait 12', 'press f5', 'wait 3']
    L += P.shift_key('n5') + [x for _ in range(8) for x in ('wait 0.25', C)] + ['exit']
    d = H.run('exp_wave_fast_t', L, 'exp', 'floppy/funky.img', 150, sound=False)
    pts = [(float(l.split()[1]), int(l.split()[2])) for l in log(d, 'WT ')]
    t_done = next((round(t - pts[0][0] + 0.25, 2) for t, c in pts if c >= 245), None) if pts else None
    W = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for i=0,244 do t[#t+1]=sp:read_u16(0x7c008+2*i)..","..sp:read_u16(0x7c1f2+2*i) end '
         'print("WS "..sp:read_u16(0x7c3dc).." "..table.concat(t," "))')
    Ls = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 8', W, 'exit']
    cols = {}
    for name, b in (('fast', 'exp'), ('stock', 'expbase')):
        r = H.run('exp_wave_fast_s_' + name, Ls, b, 'floppy/funky.img', 100, sound=False)
        w = (log(r, 'WS ') or ['WS 0'])[0].split()
        cols[name] = (int(w[1]), [tuple(map(int, x.split(','))) for x in w[2:]])
    (cf, A), (cs_, B) = cols['fast'], cols['stock']
    same = sum(1 for x, y in zip(A, B) if x == y); worst = max((max(abs(x[0] - y[0]), abs(x[1] - y[1])) for x, y in zip(A, B)), default=99)
    R[f'wave fast: 10 s recording, waveform complete after {t_done} s in TRIM'] = t_done is not None and t_done <= 1.0
    R[f'wave fast: FUNKY columns vs stock: {same} of {len(A)} identical, worst {worst} rows'] = cf == cs_ == 245 and len(A) == 245 and worst <= 2 and same >= 196
    R['wave fast: runs healthy'] = healthy(d)

TESTS = {'wave_fast': t_wave_fast, 'wave_chop': t_wave_chop, 'mute_all': t_mute_all, 'timing': t_timing, 'timing_disk': t_timing_disk, 'chop_opts': t_chop_opts, 'lazy_repeat': t_lazy_repeat, 'tpad': t_tpad, 'f6play': t_f6play, 'digit': t_digit, 'prog_mono': t_prog_mono, 'rec_normal': t_rec_normal, 'chop_preview': t_chop_preview, 'mute4': t_mute4, 'mute': t_mute, 'vub': t_vub, 'twin': t_twin, 'gate_update': t_gate_update, 'gate_boot': t_gate_boot, 'chop': t_chop, 'sampling': t_sampling, 'prog24': t_prog24, 'use_restore': t_use_restore}
if __name__ == '__main__' and sys.argv[1:2] == ['--make-refs']:
    d = H.run('exp_ref_boot', BOOT_LINES, 'stock', GOLD, 120, sound=False); print(d, snaps(d)); sys.exit()
if __name__ == '__main__':
    binp = sys.argv[1]; names = sys.argv[2:] or list(TESTS)
    sysd = os.path.join(HERE, 'sys_exp'); os.makedirs(sysd, exist_ok=True)
    open(sysd + '/MPC2KXL.BIN', 'wb').write(open(binp, 'rb').read()); H.SYS['exp'] = sysd
    based = os.path.join(HERE, 'sys_expbase'); os.makedirs(based, exist_ok=True)
    open(based + '/MPC2KXL.BIN', 'wb').write(open(os.path.join(HERE, 'base', 'vub_noregions.BIN'), 'rb').read()); H.SYS['expbase'] = based
    sem = threading.Semaphore(int(os.environ.get("PAR", "2")))
    def w(f):
        with sem:
            try: f()
            except Exception as e:                       # a crashing test is a failure, never a silent pass
                import traceback; traceback.print_exc(); R[f'{f.__name__}: CRASHED ({type(e).__name__}: {e})'] = False
    ts = [threading.Thread(target=w, args=(TESTS[n],)) for n in names]
    [t.start() for t in ts]; [t.join() for t in ts]
    allok = True
    for k, v in R.items():
        if isinstance(v, bool): allok &= v; print('%-96s %s' % (k, 'PASS' if v else 'FAIL'))
        else: print('%-96s %s' % (k, v))
    json.dump(R, open(os.path.join(HERE, 'test_result.json'), 'w'), indent=1, default=str)
    print('ALL PASS' if allok else 'SOME FAILED')
