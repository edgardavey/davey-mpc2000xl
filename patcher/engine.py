#!/usr/bin/env python3
"""DAVEY patcher engine (Python reference; the browser app uses the same algorithm in engine.js).

Input : the exact original Akai MPC2000XL OS 1.20 (MPC2KXL.BIN, 524288 bytes, sha256 100e3375...).
Output: that file with the selected modules applied, checksum word recomputed, boot region verified unchanged.

Patch kinds in modules.json
  {"offset", "xor"}                      vubeatz-style: bytes ^= xor (relative to the original file)
  {"offset", "old", "new", when?, unless?}  DAVEY-style: current bytes must equal old, then new is written.
                                         when/unless: the patch exists only if those modules are (not) selected.
A module may list "excludes" (modules it cannot be combined with); finalize.forbidden lists ranges that must stay original.
Modules are applied in file order, then the shared rules, then the DAVEY modules (they expect the vubeatz result)."""
import base64, hashlib, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STOCK_SHA = '100e3375b45072c209ffa2b1dbaecbf740c8c4ea29162827ac11cc6bf9cc7bab'

def load_data(path=None):
    return json.load(open(path or os.path.join(HERE, 'modules.json')))

def closure(data, sel):
    mods = {m['id']: m for m in data['modules']}
    out, todo = set(), list(sel)
    while todo:
        x = todo.pop()
        if x in out: continue
        if x not in mods: raise ValueError('unknown module ' + x)
        out.add(x); todo += mods[x]['requires']
    for x in out:
        for e in mods[x].get('excludes', []):
            if e in out: raise ValueError('%s cannot be combined with %s' % (mods[x]['name'], mods[e]['name']))
    return out

def points(data, sel):
    mods = {m['id']: m for m in data['modules']}
    return sum(mods[x]['weight'] for x in sel)

def sel_key(sel): return ','.join(sorted(sel))

def build(data, original, selection):
    """returns (bytes, report dict). raises ValueError on any mismatch."""
    if len(original) != data['base']['size'] or hashlib.sha256(original).hexdigest() != data['base']['sha256']:
        raise ValueError('input is not the exact original OS 1.20 (sha256 %s)' % hashlib.sha256(original).hexdigest())
    S = closure(data, selection)
    d = bytearray(original)
    n_patches = 0
    for m in data['modules']:
        if m['id'] not in S or m['kind'] != 'xor': continue
        for p in m['patches']:
            x = base64.b64decode(p['xor'])
            if p['offset'] < 0 or p['offset'] + len(x) > data['finalize']['unchanged'][0]: raise ValueError('module %s: patch outside the OS area' % m['id'])
            for i, b in enumerate(x): d[p['offset'] + i] ^= b
            n_patches += 1
    for r in data['rules']:
        if r['host'] is not None and r['host'] not in S: continue
        x = base64.b64decode(r['default'])
        for v in r['variants']:
            w = v['when']
            if all(a in S for a in w['all']) and (not w['any'] or any(a in S for a in w['any'])) and not any(a in S for a in w['none']):
                x = base64.b64decode(v['xor']); break
        for i, b in enumerate(x[:r['length']]): d[r['offset'] + i] ^= b
    for m in data['modules']:
        if m['id'] not in S or m['kind'] != 'set': continue
        for p in m['patches']:
            if any(w not in S for w in p.get('when', [])) or any(w in S for w in p.get('unless', [])): continue
            old, new = base64.b64decode(p['old']), base64.b64decode(p['new'])
            if len(old) != len(new) or p['offset'] + len(new) > data['finalize']['unchanged'][0]: raise ValueError('module %s: malformed patch at 0x%x' % (m['id'], p['offset']))
            cur = bytes(d[p['offset']:p['offset'] + len(old)])
            if cur != old:
                raise ValueError('module %s: unexpected bytes at 0x%x (have %s, want %s)' % (m['id'], p['offset'], cur.hex(), old.hex()))
            d[p['offset']:p['offset'] + len(new)] = new
            n_patches += 1
    fin = data['finalize']
    a, b = fin['checksum']['range']
    s = sum(w for (w,) in struct.iter_unpack('<H', bytes(d[a:b]))) & 0xffff
    d[fin['checksum']['offset']:fin['checksum']['offset'] + 2] = struct.pack('<H', s)
    ua, ub = fin['unchanged']
    if bytes(d[ua:ub]) != original[ua:ub]: raise ValueError('boot region changed')
    for fa, fb in fin.get('forbidden', []):        # RAM the OS uses at runtime (program slots 18-24): must stay as in the original
        if bytes(d[fa:fb]) != original[fa:fb]: raise ValueError('a module writes into program memory 0x%x-0x%x' % (fa, fb))
    if len(d) != len(original): raise ValueError('size changed')
    out = bytes(d)
    key = sel_key(S)
    ref = data.get('verified', {}).get(key)
    sha = hashlib.sha256(out).hexdigest()
    return out, {'modules': sorted(S), 'points': points(data, S), 'patches': n_patches, 'checksum': s, 'sha256': sha,
                 'reference': ('match' if ref == sha else 'MISMATCH') if ref else 'untested-combination'}

def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description='DAVEY MPC2000XL patcher (command line)')
    ap.add_argument('original', help='original OS 1.20 MPC2KXL.BIN')
    ap.add_argument('output', help='new file to create (must not exist)')
    ap.add_argument('modules', nargs='*', help='module ids; none = recommended set')
    ap.add_argument('--list', action='store_true', help='list modules and exit')
    a = ap.parse_args(argv)
    data = load_data()
    if a.list:
        for m in data['modules']:
            if not m.get('hidden'): print('%-12s %d pt  %s%s' % (m['id'], m['weight'], m['name'], ('  [requires ' + ','.join(m['requires']) + ']') if m['requires'] else ''))
        return 0
    sel = a.modules or data['meter']['sets']['recommended']
    if os.path.exists(a.output): sys.exit('refusing to overwrite ' + a.output)
    out, rep = build(data, open(a.original, 'rb').read(), sel)
    open(a.output, 'wb').write(out)
    assert open(a.output, 'rb').read() == out
    print(json.dumps(rep, indent=1))
    print('marker (tested set): %d  maximum: %d' % (data['meter']['limit'], data['meter']['maximum']))
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
