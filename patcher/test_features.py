#!/usr/bin/env python3
"""Feature tests on files built by the patcher engine (not on the old make_os builds)."""
import os, sys, re, json, hashlib, shutil, threading
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'build_os', 'suite'))
import engine, harness as H, phases
data = engine.load_data(); orig = open(os.path.join(ROOT, 'build_os', 'sys_stock', 'MPC2KXL.BIN'), 'rb').read()
R = os.path.join(ROOT, 'test_log', 'runs')
def mk(name, sel):
    d = '/tmp/mxf/' + name; os.makedirs(d, exist_ok=True)
    out, rep = engine.build(data, orig, sel); open(d + '/MPC2KXL.BIN', 'wb').write(out)
    H.SYS['f_' + name] = d; return 'f_' + name
def phash(p): return hashlib.sha256(Image.open(p).convert('1').tobytes()).hexdigest()
def snaps_equal(a, b, dark=False):
    fa, fb = sorted(os.listdir(a + '/snap')), sorted(os.listdir(b + '/snap'))
    if len(fa) != len(fb): return False, 'count %d vs %d' % (len(fa), len(fb))
    bad = []
    for x, y in zip(fa, fb):
        A = Image.open(a + '/snap/' + x).convert('L'); B = Image.open(b + '/snap/' + y).convert('L')
        if dark: B = ImageChops.invert(B)
        if ImageChops.difference(A, B).point(lambda v: 255 if v > 60 else 0).getbbox(): bad.append(x)
    return (not bad), bad[:6]
def snaps_masked(a, b, max_px=60):
    """compare everything below the two text rows (waveform, highlight, soft keys). Lazy-chop tap times depend on CPU load, so the
    boundary numbers (text rows) may differ by a few frames; below them at most max_px pixels may differ per screen."""
    fa, fb = sorted(os.listdir(a + '/snap')), sorted(os.listdir(b + '/snap'))
    if len(fa) != len(fb): return False, 'count'
    bad = []
    for i, (x, y) in enumerate(zip(fa, fb)):
        A = Image.open(a + '/snap/' + x).convert('L').crop((0, 22, 248, 60)); B = Image.open(b + '/snap/' + y).convert('L').crop((0, 22, 248, 60))
        d = ImageChops.difference(A, B).point(lambda v: 255 if v > 60 else 0)
        n = sum(1 for v in d.getdata() if v)
        if n > max_px: bad.append((i, n))
    return (not bad), bad
def lines(d, pre): return [l for l in open(d + '/out.log', errors='replace').read().split('\n') if l.startswith(pre)]
results = {}
def t_zone():
    n = mk('zone', ['zone_lazy']); res = H.run('pf_zone', phases.zone_suite()['lines'], n, 'floppy/funky.img', 520)
    ref = R + '/zone_suite/davey'
    def nums(l, key):
        m = re.search(key + r'\s*=?\s*([\d ]+)', l); return [int(x) for x in m.group(1).split()] if m else []
    ok = len(lines(res, 'TAPS')) == len(lines(ref, 'TAPS')) > 5 and len(lines(res, 'ZONES')) == len(lines(ref, 'ZONES')) > 5
    worst_t = worst_z = 0
    for a, b in zip(lines(res, 'TAPS'), lines(ref, 'TAPS')):
        if a.split(' cnt=')[0] != b.split(' cnt=')[0] or re.search(r'cnt=(\d+)', a).group(1) != re.search(r'cnt=(\d+)', b).group(1): ok = False
        ta, tb = nums(a, 'taps='), nums(b, 'taps=')
        worst_t = max([worst_t] + [abs(x - y) for x, y in zip(ta, tb)])
    for a, b in zip(lines(res, 'ZONES'), lines(ref, 'ZONES')):
        if a.split(' B=')[0] != b.split(' B=')[0]: ok = False
        za, zb = nums(a, 'B='), nums(b, 'B=')
        worst_z = max([worst_z] + [abs(x - y) for x, y in zip(za, zb)])
    ok = ok and worst_t <= 3 and worst_z <= 150
    results['zone_lazy (counts equal to FR1; max tap diff %d ms, max boundary diff %d frames)' % (worst_t, worst_z)] = ok
def t_regions():
    n = mk('regions', ['regions', 'lazy', 'overdub_fix']); res = H.run('pf_regions', phases.regions_suite2()['lines'], n, 'floppy/funky.img', 900)
    ref = R + '/regions_suite2/davey'
    ok, why = snaps_masked(res, ref); ok2 = lines(res, 'REGIONS R15') == lines(ref, 'REGIONS R15')
    results['regions+lazy+overdub_fix (regions_suite2 vs FR1)'] = ok and ok2
    if not ok: results['  regions detail'] = why
def t_mute():
    n = mk('mute8', ['mute8']); res = H.run('pf_mute', phases.mute_matrix()['lines'], n, 'floppy/funky.img', 900)
    rows = [l.split(' ', 2) for l in open(res + '/out.log', errors='replace') if l.startswith('PLAYING')]
    r = {x[1]: sorted(set(t.split(':')[1] for t in (x[2].split() if len(x) > 2 else []))) for x in rows}
    bad = 0; pairs = sorted(set(k.rsplit('_', 1)[0] for k in r))
    for p in pairs:
        g1, g2 = int(p[1]), int(p[2]); a, b = r.get(p + '_a'), r.get(p + '_b'); exp = (g1 == g2 and g1 != 0)
        killed = a is not None and '37' in a and b is not None and '37' not in b
        if not ((killed == exp) and ('36' in (b or []))): bad += 1
    results['mute8 (mute matrix, %d pairs)' % len(pairs)] = (bad == 0 and len(pairs) >= 12)
def t_vub():
    n = mk('vubfeat', ['tune', 'transpose', 'param_copy', 'double_stop'])
    r1 = H.run('pf_v1', phases.vub_feat1()['lines'], n, 'floppy/funky.img', 600)
    r2 = H.run('pf_v2', phases.vub_feat2()['lines'], n, 'floppy/funky.img', 450)
    ok1, w1 = snaps_equal(r1, R + '/vub_feat1/davey'); ok2, w2 = snaps_equal(r2, R + '/vub_feat2/davey')
    results['tune/transpose/ALL/double STOP (vs FR1)'] = ok1 and ok2
    if not (ok1 and ok2): results['  vub detail'] = (w1, w2)
def t_dark():
    nd = mk('dark', ['dark']); ns = mk('plain', [])
    a = H.run('pf_dark', phases.tour()['lines'], nd, 'floppy/funky.img', 450); b = H.run('pf_plain', phases.tour()['lines'], ns, 'floppy/funky.img', 450)
    ok, why = snaps_equal(a, b, dark=True)
    results['dark mode (71-screen tour = exact inversion of original)'] = ok
    if not ok: results['  dark detail'] = why

def sampling_run(tag, sel, preset_keys, record_wait):
    n = mk(tag, sel); N = 4096; O = 300000; RLEN = 445424
    HOOK = ('lua local d=manager.machine.devices[":dsp"].spaces["l6028"] local sp=manager.machine.devices[":maincpu"].spaces["program"] local done=false local dumped=false '
            'emu.register_frame_done(function() local st=sp:read_u16(0x77d62) '
            'if st==2 and not done then done=true '
            ' for i=0,%d do d:write_u16((0x12680+%d+i)*2,(0x0007+i*13)&0xffff) d:write_u16((0x12680+%d+%d+i)*2,(0x1001+i*7)&0xffff) end print("INJECTED") end '
            'if st==1 and done and not dumped then dumped=true local a={} local b={} '
            ' for i=0,%d do a[#a+1]=string.format("%%04x",d:read_u16((0x12680+%d+i)*2)) b[#b+1]=string.format("%%04x",d:read_u16((0x12680+%d+%d+i)*2)) end '
            ' print("OUTL "..table.concat(a," ")) print("OUTR "..table.concat(b," ")) end end)') % (N - 1, O, RLEN, O, N - 1, O, RLEN, O)
    L = ['wait 28', 'down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press right', 'wait 1', 'press window', 'wait 1.5'] + preset_keys + \
        ['press f5', 'wait 2', HOOK, 'press f6', 'wait 3', 'press f6', 'wait %d' % record_wait, 'snap', 'wait 1', 'snap', 'exit']
    res = H.run('pf_' + tag, L, n, 'floppy/funky.img', 300 + record_wait)
    return res
def t_sampling():
    res = sampling_run('smp_sp1200', ['sampling'], ['press plus', 'wait 0.8', 'press down', 'wait 0.8'] + ['press n2', 'press n2', 'press n0', 'press n5', 'press n0', 'press enter', 'wait 1'], 30)
    t = open(res + '/out.log', errors='replace').read()
    R = 22050
    def model(inp, R, mask=0xfff0):
        bx = 44100 - R; bp = bx; dx = 0; o = []
        for w in inp:
            if bp < bx: bp += R
            else: bp -= bx; dx = w & mask
            o.append(dx)
        return o
    ok = True; detail = []
    for tag, mul, base in (('OUTL', 13, 0x0007), ('OUTR', 7, 0x1001)):
        m = re.search(tag + r' ([0-9a-f ]+)', t)
        if not m: ok = False; detail.append(tag + ' missing'); continue
        out = [int(x, 16) for x in m.group(1).split()]
        # the first sample of the injected window follows unknown previous samples (zeros); model the whole prefix as zeros
        inp = [0] * 8 + [(base + i * mul) & 0xffff for i in range(len(out))]
        mod = model(inp, R)[8:]
        good = sum(1 for a, b in zip(out, mod) if a == b)
        detail.append('%s %d/%d' % (tag, good, len(out)))
        if good < len(out) - 2: ok = False
    # KEEP or RETRY must show its text without a cursor key: dark pixels in the text lines of the window
    snaps = sorted(os.listdir(res + '/snap')); im = Image.open(res + '/snap/' + snaps[-1]).convert('1'); px = im.load()
    textpx = sum(1 for x in range(8, 200) for y in range(18, 30) if px[x, y] == 0)
    keep_ok = textpx > 120
    results['sampling SP1200 22050: L/R vs model (' + ', '.join(detail) + '), KEEP text pixels=%d' % textpx] = ok and keep_ok
def t_sampling_s900():
    res = sampling_run('smp_s900', ['sampling'], ['press plus', 'wait 0.8', 'press plus', 'wait 0.8'], 70)
    t = open(res + '/out.log', errors='replace').read()
    done = 'OUTL' in t and 'OUTR' in t
    snaps = sorted(os.listdir(res + '/snap')); im = Image.open(res + '/snap/' + snaps[-1]).convert('1'); px = im.load()
    textpx = sum(1 for x in range(8, 200) for y in range(18, 30) if px[x, y] == 0)
    results['sampling S900 completes, KEEP text pixels=%d' % textpx] = done and textpx > 120
ts = [threading.Thread(target=f) for f in (t_zone, t_regions, t_mute, t_vub, t_dark, t_sampling, t_sampling_s900)]
[t.start() for t in ts]; [t.join() for t in ts]
for k, v in results.items(): print('%-62s %s' % (k, v if not isinstance(v, bool) else ('PASS' if v else 'FAIL')))
json.dump({k: v for k, v in results.items()}, open(os.path.join(HERE, 'features_result.json'), 'w'), indent=1, default=str)
