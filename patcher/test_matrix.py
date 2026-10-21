#!/usr/bin/env python3
"""Emulator test matrix: every selectable module alone + the combined sets.
For each selection: build with the engine, boot it, look at the main page, the version page, then run LOAD > OS update > DO IT
and require it to reach "Loading" and "Flash block 1-7 erase". Every screen is compared with the same run on the untouched
original OS (inverted for dark mode)."""
import os, sys, json, shutil, hashlib, threading, subprocess
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'build_os', 'suite'))
import engine, harness as H
data = engine.load_data()
orig = open(os.path.join(ROOT, 'build_os', 'sys_stock', 'MPC2KXL.BIN'), 'rb').read()
FLOPPY = os.path.join(ROOT, 'floppy', 'gold_floppy.img')   # holds the ORIGINAL Akai MPC2KXL.BIN: the restore source
LINES = ['wait 28', 'snap', 'down shift', 'up shift', 'wait 0.3', 'press n8', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press f3', 'wait 1.5', 'snap',
         'press main', 'wait 1', 'down shift', 'up shift', 'wait 0.3', 'press n3', 'wait 0.3', 'down shift', 'up shift', 'wait 2.5', 'press plus', 'wait 1.5', 'snap',
         'press f6', 'wait 3', 'snap', 'press f5', 'wait 3', 'snap', 'wait 12', 'snap', 'wait 25', 'snap', 'exit']
NAMES = ['main', 'version', 'load', 'prompt', 'loading', 'loading2', 'erase']
# RESTORE GATE 2: boot from disk (the boot program's loader, forced the same way the emulator test established) with the ORIGINAL on disk.
POKE = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] emu.register_frame_done(function() '
        'local t=manager.machine.time:as_double() if t>0.3 and t<3 then sp:write_u8(0x35cf,0x22) sp:write_u8(0x35d0,0xe0) end end)')
BOOT_LINES = [POKE, 'wait 2', 'snap', 'wait 40', 'snap', 'down shift', 'up shift', 'wait 0.3', 'press n8', 'wait 0.3', 'down shift', 'up shift', 'wait 2',
              'press f3', 'wait 1.5', 'snap', 'exit']
BOOT_NAMES = ['loader', 'main', 'version']

def sets():
    S = {}
    vis = [m['id'] for m in data['modules'] if not m['hidden']]
    for i in vis: S['only_' + i] = [i]
    for k, v in data['meter']['sets'].items(): S['set_' + k] = v
    S['set_recommended_dark'] = data['meter']['sets']['recommended'] + ['dark']
    S['stock_identity'] = []
    return S

def run_one(name, sel, results):
    d = '/tmp/mx/' + name; os.makedirs(d, exist_ok=True)
    out, rep = engine.build(data, orig, sel)
    open(d + '/MPC2KXL.BIN', 'wb').write(out)
    H.SYS['mx_' + name] = d
    res = H.run('mx_' + name, LINES, 'mx_' + name, FLOPPY, 200, sound=False)
    boot = H.run('mxboot_' + name, BOOT_LINES, 'mx_' + name, FLOPPY, 160, sound=False)
    results[name] = (res, rep, boot)

def inv(im): return ImageChops.invert(im)
def region_diff(a, b):
    return ImageChops.difference(a, b).point(lambda v: 255 if v > 60 else 0).getbbox()

def judge(res, ref, dark):
    snaps = sorted(os.listdir(res + '/snap')); rsn = sorted(os.listdir(ref + '/snap'))
    if len(snaps) != len(NAMES): return False, 'only %d of %d screens' % (len(snaps), len(NAMES)), {}
    notes = {}; ok = True
    for i, n in enumerate(NAMES):
        a = Image.open(res + '/snap/' + snaps[i]).convert('L'); b = Image.open(ref + '/snap/' + rsn[i]).convert('L')
        if dark: b = inv(b)
        bb = region_diff(a, b)
        notes[n] = 'same' if not bb else 'diff' + str(bb)
        if bb and n not in ('version',): ok = False
    # proof the flash step was reached: the original's last screen must not be the Loading screen any more
    r_last = Image.open(ref + '/snap/' + rsn[NAMES.index('erase')]).convert('L'); r_load = Image.open(ref + '/snap/' + rsn[NAMES.index('loading')]).convert('L')
    if not region_diff(r_last, r_load): ok = False; notes['erase'] = 'reference never left Loading: gate invalid'
    return ok, ('ok' if ok else 'screen mismatch'), notes

if __name__ == '__main__':
    only = sys.argv[1:]
    S = sets()
    if only: S = {k: v for k, v in S.items() if k in only}
    S2 = dict(S); S2['__reference_stock'] = None
    results = {}
    ref_dir = '/tmp/mx/__ref'; os.makedirs(ref_dir, exist_ok=True)
    open(ref_dir + '/MPC2KXL.BIN', 'wb').write(orig)   # plain write: an earlier copy may be read-only
    H.SYS['mx_ref'] = ref_dir
    ths = []
    sem = threading.Semaphore(5)
    def worker(n, s):
        with sem: run_one(n, s, results)
    todo = [threading.Thread(target=worker, args=(n, s)) for n, s in S.items()]
    ref_res = {}
    def refw():
        with sem:
            ref_res['r'] = H.run('mx_ref', LINES, 'mx_ref', FLOPPY, 200, sound=False)
            ref_res['b'] = H.run('mxboot_ref', BOOT_LINES, 'mx_ref', FLOPPY, 160, sound=False)
    tr = threading.Thread(target=refw); tr.start()
    [t.start() for t in todo]; [t.join() for t in todo]; tr.join()
    ref = ref_res['r']
    report = []
    allok = True
    for n, (res, rep, boot) in sorted(results.items()):
        dark = 'dark' in rep['modules']
        ok, msg, notes = judge(res, ref, dark)
        h = H.health(res, LINES)
        good = ok and h['finished'] and not h['lua_errors']
        # restore gate 2: everything after boot-from-disk must equal the stock run, never inverted (the original OS is now running)
        bs = sorted(os.listdir(boot + '/snap')); rb = sorted(os.listdir(ref_res['b'] + '/snap'))
        bok = len(bs) == len(BOOT_NAMES)
        if bok:
            for i in range(len(BOOT_NAMES)):
                a = Image.open(boot + '/snap/' + bs[i]).convert('L'); b = Image.open(ref_res['b'] + '/snap/' + rb[i]).convert('L')
                if region_diff(a, b): bok = False
        bh = H.health(boot, BOOT_LINES)
        bok = bok and bh['finished'] and not bh['lua_errors']
        good = good and bok
        allok &= good
        report.append((n, rep['points'], len(rep['modules']), 'PASS' if good else 'FAIL', msg, 'restore-by-update:' + ('ok' if ok else 'FAIL'),
                       'restore-by-bootdisk:' + ('ok' if bok else 'FAIL'), notes.get('version')))
    for r in report: print('%-26s pts=%2d mods=%2d %-4s %-16s %-24s %-26s version:%s' % r)
    json.dump(report, open(os.path.join(HERE, 'matrix_result.json'), 'w'), indent=1)
    print('ALL PASS' if allok else 'SOME FAILED')
