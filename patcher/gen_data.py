#!/usr/bin/env python3
"""Generates modules.json for the DAVEY patcher.

Sources
  * vubeatz updater 2.0 module data (offsets, weights, dependencies, shared rules): only the modules whose result is contained
    in our stable base are used (tune, transpose, mute, param_copy, regions, lazy, hpf, input_thru, format, double_stop,
    delay670, step_move + helpers). His own Sampling Mode (lofi_window), SWING and large-HFE are NOT offered (ours replaces the first;
    the other two are outside this project and were never tested with our modules).
  * our own modules, measured as byte differences produced by build_os/mod_*.py on top of the stable base."""
import base64, hashlib, importlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'build_os')); sys.path.insert(0, HERE)
VUB = os.environ.get('VU_UPDATER_JSON', os.path.expanduser('~/Documents/CLAUDE/mpc-private-refs/vubeatz/MPC2000XL Updater 2.app/Contents/Resources/modular.json'))   # private copy (2026-10-18), never published
STOCK = os.path.join(ROOT, 'build_os', 'sys_stock', 'MPC2KXL.BIN')
b64 = lambda b: base64.b64encode(bytes(b)).decode()

vub = json.load(open(VUB))
stock = open(STOCK, 'rb').read()
assert hashlib.sha256(stock).hexdigest() == vub['files']['MPC2KXL.BIN']['sha256']

INCLUDED = ['ram_init', 'runtime', 'u13_pitch', 'u13_program', 'tune', 'transpose', 'mute', 'param_copy', 'regions', 'lazy',
            'hpf', 'input_thru', 'format', 'double_stop', 'delay670', 'step_move']
DESC = {
 'tune': 'TUNE field goes to +/-360 (three octaves)',
 'transpose': 'Program TRANSPOSE +/-36 semitones on the ASSIGN page',
 'mute': 'Mute groups 1-4 (MODE field on the ASSIGN page)',
 'param_copy': 'ALL: copy a parameter to a bank or the whole program',
 'regions': 'REGION EDIT on the TRIM page: 4 / 8 / 16 even slices, slice editing, APPLY',
 'lazy': 'Lazy chop inside REGION EDIT: tap pads while the sample plays',
 'hpf': 'LPF / HPF with FREQ 0-200',
 'input_thru': 'Input Thru, and PLAY / STOP on the RECORD page',
 'format': 'FORMAT keeps the disk geometry',
 'double_stop': 'Press STOP twice to silence all voices',
 'delay670': 'EB16 delay time up to 670 ms',
 'step_move': 'STEP page: Move Event (SHIFT + F5)',
}
mods = []
for m in vub['modules']:
    if m['id'] not in INCLUDED: continue
    mods.append({'id': m['id'], 'name': m['name'], 'desc': DESC.get(m['id'], m['name']), 'group': 'base', 'source': 'vubeatz',
                 'hidden': m['hidden'], 'weight': m['weight'], 'requires': m['requires'], 'kind': 'xor',
                 'patches': [{'offset': p['offset'], 'xor': p['xor']} for p in m['patches']]})
own = {}   # offset -> set(vubeatz module ids) for ownership of bytes
for m in vub['modules']:
    for p in m['patches']:
        for i, b in enumerate(base64.b64decode(p['xor'])):
            if b: own.setdefault(p['offset'] + i, set()).add(m['id'])

stable = open(os.path.join(ROOT, 'archive', 'stable_overdub_fix_2026-10-07', 'MPC2KXL_overdub_fix.BIN'), 'rb').read()
baseline = open(os.path.join(ROOT, 'archive', 'stable_overdub_fix_2026-10-07', 'MPC2KXL1_vubeatz_baseline.BIN'), 'rb').read()
import make_os

def runs(before, after, skip=()):
    ch = [i for i in range(len(before)) if before[i] != after[i] and i not in skip]
    out = []
    for i in ch:
        o = frozenset(own.get(i, ()))
        if out and i - out[-1][1] <= 3 and out[-1][2] == o: out[-1][1] = i
        else: out.append([i, i, o])
    return out

def patches_from(before, after, split_by_owner=False, skip=(0x77ffe, 0x77fff)):
    res = []
    for a, b, o in runs(before, after, skip):
        p = {'offset': a, 'old': b64(before[a:b + 1]), 'new': b64(after[a:b + 1])}
        if split_by_owner and o: p['when'] = sorted(o)
        res.append(p)
    return res

def apply_ours(name, version=None):
    img = make_os.Image()
    if version: img.version = version
    importlib.import_module('mod_' + name).apply(img)
    return bytes(img.d)

# overdub fix = difference between baseline (vubeatz modules only) and stable
mods.append({'id': 'overdub_fix', 'name': 'REGIONS overdub fix', 'group': 'davey', 'source': 'davey', 'hidden': False, 'weight': 2,
             'requires': ['regions'], 'kind': 'set',
             'desc': 'Overdubbing a REGION no longer deletes same-tick notes of other regions (hooks the note pairing loop)',
             'patches': patches_from(baseline, stable) + [{'offset': 0x76e04, 'old': b64(bytes(2)), 'new': b64(bytes(2))}]})
# ---- relocated DAVEY modules (exp_reloc line): built on the VU base WITHOUT REGIONS, placed only in measured-free RAM
sys.path.insert(0, os.path.join(ROOT, 'exp_reloc')); sys.path.insert(0, os.path.join(ROOT, 'exp_reloc', 'mods'))
import make_exp, engine
import sampling as x_sampling, zone_chop as x_chop, mute8 as x_mute8, prog_mono as x_pmono
tmp = {'base': {'size': 524288, 'sha256': vub['files']['MPC2KXL.BIN']['sha256']}, 'modules': [m for m in mods if m['kind'] == 'xor'],
       'rules': vub['rules'], 'finalize': {'checksum': {'range': [0, 0x77ffe], 'offset': 0x77ffe}, 'unchanged': [0x78000, 0x80000]}}
base_noreg, _ = engine.build(tmp, stock, make_exp.VUB)
def exp_apply(fn):
    img = make_exp.Img(base_noreg); fn(img); return bytes(img.d)
mods.append({'id': 'zone_chop', 'name': 'Zone chop', 'group': 'davey', 'source': 'davey', 'hidden': False, 'weight': 2, 'requires': [],
             'excludes': ['regions'], 'kind': 'set',
             'desc': 'TRIM > ZONE, press F3 again: chop screen with the waveform. F3 cycles 16 / 8 / 4 / LAZY, F4 UNDO, F5 APPLY makes the sounds and a drum program, F6 PLAY (hold) and the pads preview slices. 16 LEVELS stays free.',
             'patches': patches_from(base_noreg, exp_apply(lambda img: x_chop.apply(img, make_exp.PLACE['zone_chop'])))})
mods.append({'id': 'prog_mono', 'name': 'Program MONO', 'group': 'davey', 'source': 'davey', 'hidden': False, 'weight': 1, 'requires': [],
             'kind': 'set', 'desc': 'Pads set to Voice overlap MONO choke each other (newer-MPC style): ALL > MONO makes the whole program mono. A single MONO pad works as stock.',
             'patches': patches_from(base_noreg, exp_apply(lambda img: x_pmono.apply(img, make_exp.PLACE['prog_mono'])))})
MUTE8_AT = 0x77f00          # free with and without REGIONS (never written in 33 coverage runs over both configurations)
make_exp.FREE.append((0x77f00, 0x77f80))
mods.append({'id': 'mute8', 'name': 'Mute groups 1-8', 'group': 'davey', 'source': 'davey', 'hidden': False, 'weight': 0, 'requires': ['mute'],
             'kind': 'set', 'desc': 'MODE field accepts MUTE 5-8 as well (adds to Mute groups 1-4)',
             'patches': patches_from(base_noreg, exp_apply(lambda img: x_mute8.apply(img, MUTE8_AT))) +
                        [{'offset': 0x75c38, 'old': b64(bytes.fromhex('26803f07')), 'new': b64(bytes.fromhex('26803f0b')), 'when': ['regions']}]})
mods.append({'id': 'sampling', 'name': 'Sampling Mode (SP1200 / S900)', 'group': 'davey', 'source': 'davey', 'hidden': False, 'weight': 2,
             'requires': [], 'kind': 'set',
             'desc': 'SAMPLE page > Mode field > WINDOW: SP1200 / S900 presets or a custom 8000-44100 Hz rate for new recordings. Shows the processing box, then KEEP / RETRY at once.',
             'patches': patches_from(base_noreg, exp_apply(x_sampling.apply))})
mods.append({'id': 'date', 'name': 'OS date Oct. 11,2026', 'group': 'davey', 'source': 'davey', 'hidden': False, 'weight': 0, 'requires': [],
             'kind': 'set', 'desc': 'Date line on OTHER > VER. and the date stamp of a Copy Operating System file',
             'patches': patches_from(stable, apply_ours('date'))})
mods.append({'id': 'dark', 'name': 'Dark mode (inverted LCD)', 'group': 'davey', 'source': 'davey', 'hidden': False, 'weight': 2, 'requires': [],
             'kind': 'set', 'experimental': True,
             'desc': 'Every LCD pixel byte is inverted inside the screen refresh loops. Touches the refresh path: emulator-tested only',
             'patches': patches_from(stable, apply_ours('dark'))})
for m in mods:                                   # REGIONS side of the either/or
    if m['id'] == 'regions': m['excludes'] = ['zone_chop']
    if m['id'] in ('regions', 'lazy', 'overdub_fix'): m['hidden'] = True      # 2026-10-17: our fork offers Zone chop only; VU Regions stay in VU's own patcher

# our modules must not overlap each other
seen = {}
for m in mods:
    if m['kind'] != 'set': continue
    for p in m['patches']:
        for i in range(p['offset'], p['offset'] + len(base64.b64decode(p['old']))):
            assert i not in seen or seen[i] == m['id'], (hex(i), m['id'], seen[i])
            seen[i] = m['id']

rules = vub['rules']
data = {'format': 'davey-patcher', 'schema_version': 2, 'release': 'DAVEY patcher 4.0',
        'base': {'file': 'MPC2KXL.BIN', 'size': 524288, 'sha256': vub['files']['MPC2KXL.BIN']['sha256']},
        'modules': mods, 'rules': rules,
        'finalize': {'checksum': {'range': [0, 0x77ffe], 'offset': 0x77ffe}, 'unchanged': [0x78000, 0x80000],
                     'forbidden': [[0x70000, 0x741b0]]}}
davey = make_exp.VUB + ['zone_chop', 'sampling', 'prog_mono']
allw = lambda ids: engine.points(data, engine.closure(data, ids))
data['meter'] = {'limit': allw(davey),
                 'maximum': allw([m['id'] for m in mods if not m['hidden']]),
                 'limit_set': 'davey',
                 'sets': {'davey': davey,
                          'light': ['tune', 'transpose', 'param_copy', 'format']}}
# the DAVEY preset must be byte-identical to the emulator-tested experimental file
out, rep = engine.build(data, stock, davey)
exp2 = open(os.path.join(ROOT, 'exp_reloc', 'DAVEY_EXP7.BIN'), 'rb').read()
assert out == exp2, 'DAVEY preset differs from exp_reloc/DAVEY_EXP7.BIN'
print('DAVEY preset == DAVEY_EXP7.BIN', rep['sha256'][:16])
# tested combinations (emulator gates passed on the exact file); more are added by finalize_verified.py after the gate runs
data['verified'] = {engine.sel_key(engine.closure(data, davey)): rep['sha256']}
_extra = os.path.join(HERE, 'verified_extra.json')       # written by exp_reloc/gate_presets.py: only selections that passed both restore gates
if os.path.exists(_extra):
    for k, v in json.load(open(_extra)).items():
        sel_ = k.split(','); b_, r_ = engine.build(data, stock, sel_)
        assert r_['sha256'] == v, 'verified_extra entry no longer reproduces: ' + k
        data['verified'][k] = v
json.dump(data, open(os.path.join(HERE, 'modules.json'), 'w'), indent=1)
print('modules:', len(mods), 'limit', data['meter']['limit'], 'max', data['meter']['maximum'])
for m in mods:
    if not m['hidden']:
        print(f"  {m['id']:12} w={m['weight']} req={m['requires']} patches={len(m['patches'])}")
