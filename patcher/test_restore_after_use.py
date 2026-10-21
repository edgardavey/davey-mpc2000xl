#!/usr/bin/env python3
"""GATE 3: use the features, THEN restore by update.
For each scenario the build is exercised with a real suite (zone chop, REGIONS, MUTE, sequencer, sampling, ...) and the OS update flow is run
afterwards with the ORIGINAL MPC2KXL.BIN as the source. The last three screens (update prompt, Loading, Flash block erase) must equal the
untouched original's (inverted for dark mode)."""
import os, sys, json, threading
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'build_os', 'suite'))
import engine, harness as H, phases
data = engine.load_data(); orig = open(os.path.join(ROOT, 'build_os', 'sys_stock', 'MPC2KXL.BIN'), 'rb').read()
GOLD = os.path.join(ROOT, 'floppy', 'gold_floppy.img')      # funky.img + the ORIGINAL MPC2KXL.BIN (built by test_matrix preparation)
REF = os.path.join(ROOT, 'test_log', 'runs', 'mx_ref', 'mx_ref', 'snap')        # prompt/loading/erase of the untouched original: snaps 3,4,5
UPDATE = ['press main', 'wait 1', 'down shift', 'up shift', 'wait 0.3', 'press n3', 'wait 0.3', 'down shift', 'up shift', 'wait 2.5',
          'press plus', 'wait 0.5', 'press plus', 'wait 0.5', 'press plus', 'wait 1.5', 'press f6', 'wait 3', 'snap', 'press f5', 'wait 3', 'snap', 'wait 12', 'snap', 'wait 25', 'snap', 'exit']
def sampling(preset_keys, record_wait):
    return ['wait 28', 'down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press right', 'wait 1', 'press window', 'wait 1.5'] + preset_keys + \
           ['press f5', 'wait 2', 'press f6', 'wait 3', 'press f6', 'wait %d' % record_wait, 'press f6', 'wait 3', 'press f5', 'wait 2']
def body(fn): return [l for l in fn()['lines'] if l != 'exit']
SC = {
 'zone_lazy':        (['zone_lazy'], lambda: body(phases.zone_suite)),
 'regions_lazy_fix': (['regions', 'lazy', 'overdub_fix'], lambda: body(phases.regions_suite2)),
 'mute8':            (['mute8'], lambda: body(phases.mute_matrix)),
 'vub_features':     (['tune', 'transpose', 'param_copy', 'double_stop'], lambda: body(phases.vub_feat1)),
 'stock_vub_features': ([], lambda: body(phases.vub_feat1)),   # control: the untouched original OS
 'sampling_sp1200':  (['sampling'], lambda: sampling(['press plus', 'wait 0.8'], 14)),
 'sampling_s900':    (['sampling'], lambda: sampling(['press plus', 'wait 0.8', 'press plus', 'wait 0.8'], 60)),
 'recommended_seq':  (data['meter']['sets']['recommended'], lambda: body(phases.seq_basic) + body(phases.seq_edit)),
 'recommended_dark_pages': (data['meter']['sets']['recommended'] + ['dark'], lambda: body(phases.tour)),
}
def run(name, sel, mk, out):
    d = '/tmp/mxr/' + name; os.makedirs(d, exist_ok=True)
    b, rep = engine.build(data, orig, sel); open(d + '/MPC2KXL.BIN', 'wb').write(b); H.SYS['r_' + name] = d
    lines = mk() + UPDATE
    res = H.run('rau_' + name, lines, 'r_' + name, GOLD, 900, sound=False)
    out[name] = (res, 'dark' in rep['modules'])
def judge(res, dark):
    snaps = sorted(os.listdir(res + '/snap'))[-4:]; ref = sorted(os.listdir(REF))[3:7]
    if len(snaps) < 4 or len(ref) < 4: return False, 'missing screens'
    for a, b in zip(snaps, ref):
        # the free-memory readout (x >= 230) shows through behind the dialog and legitimately differs after sounds/sequences were used
        A = Image.open(res + '/snap/' + a).convert('L').crop((0, 0, 230, 60)); B = Image.open(os.path.join(REF, b)).convert('L').crop((0, 0, 230, 60))
        if dark: B = ImageChops.invert(B)
        if ImageChops.difference(A, B).point(lambda v: 255 if v > 60 else 0).getbbox(): return False, 'update screens differ'
    return True, 'prompt, Loading and the flash-erase step identical to the original'
if __name__ == '__main__':
    only = sys.argv[1:]; out = {}
    todo = {k: v for k, v in SC.items() if not only or k in only}
    sem = threading.Semaphore(4)
    def w(n, s, m):
        with sem: run(n, s, m, out)
    ts = [threading.Thread(target=w, args=(n, s, m)) for n, (s, m) in todo.items()]
    [t.start() for t in ts]; [t.join() for t in ts]
    allok = True; rows = []
    for n, (res, dark) in sorted(out.items()):
        ok, msg = judge(res, dark); h = H.health(res, [])
        good = ok and h['finished'] and not h['lua_errors']; allok &= good
        rows.append([n, 'PASS' if good else 'FAIL', msg])
        print('%-26s %-5s %s' % (n, 'PASS' if good else 'FAIL', msg))
    json.dump(rows, open(os.path.join(HERE, 'restore_after_use_result.json'), 'w'), indent=1)
    print('ALL PASS' if allok else 'SOME FAILED')
