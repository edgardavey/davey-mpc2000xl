#!/usr/bin/env python3
"""Restore gates (update + boot-from-disk) for patcher selections, one emulator at a time. Writes patcher/verified_extra.json."""
import os, sys, json, subprocess, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'patcher')); import engine
data = engine.load_data(); stock = open(os.path.join(ROOT, 'build_os', 'sys_stock', 'MPC2KXL.BIN'), 'rb').read()
S = data['meter']['sets']
SEL = {'light': S['light'], 'only_zone_chop': ['zone_chop'], 'only_sampling': ['sampling'], 'only_prog_mono': ['prog_mono'],
       'mute8': ['mute', 'mute8'], 'davey_mute8': S['davey'] + ['mute8']}
out = {}; extra_path = os.path.join(ROOT, 'patcher', 'verified_extra.json')
for name, sel in SEL.items():
    b, rep = engine.build(data, stock, sel); p = f'/tmp/gate_{name}.BIN'; open(p, 'wb').write(b)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'test_exp.py'), p, 'gate_update', 'gate_boot'], capture_output=True, text=True, env=dict(os.environ, PAR='1'))
    ok = 'ALL PASS' in r.stdout
    print(f'{name:<20} {rep["sha256"][:12]} {"PASS" if ok else "FAIL"}', flush=True)
    if not ok: print(r.stdout[-800:], flush=True)
    else: out[engine.sel_key(engine.closure(data, sel))] = rep['sha256']
json.dump(out, open(extra_path, 'w'), indent=1); print('wrote', extra_path, len(out))
