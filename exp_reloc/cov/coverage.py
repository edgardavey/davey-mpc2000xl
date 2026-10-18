#!/usr/bin/env python3
"""Experimental relocation, step 1: which bytes of RAM 0x741B0-0x7FFFF are ever written after boot?
Runs many suites on one build with a write watch, saves one bitmap per suite (1 byte per address, 1 = written)
in exp_reloc/cov/out/<suite>.bin, and prints the merged free ranges. Read-only for every other folder.
usage: coverage.py BUILD.BIN [suite ...]"""
import os, sys, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'build_os', 'suite'))
import phases as P, harness as H
LO, HI = 0x741B0, 0x80000
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

def tap_on(tag):
    return ('lua local m=manager.machine local sp=m.devices[":maincpu"].spaces["program"] covw={} '
            f'covtap=sp:install_write_tap({LO},{HI - 1},"cov",function(off,data,mask) if m.time:as_double()<3 then return end '
            'if (mask & 0xff)~=0 then covw[off]=1 end if (mask & 0xff00)~=0 then covw[off+1]=1 end end) print("COVON")')
def tap_dump(tag):
    return (f'lua local f=io.open("{OUT}/{tag}.bin","wb") local t={{}} for a={LO},{HI - 1} do t[#t+1]=covw[a] and "\\1" or "\\0" '
            'if #t==4096 then f:write(table.concat(t)) t={} end end f:write(table.concat(t)) f:close() print("COVDUMP")')

def programs24():
    L = P.boot() + P.shift_key('n6') + ['wait 1.5', 'press f1', 'wait 1.5']
    for k in range(23):
        L += ['press window', 'wait 1.2', 'press f3', 'wait 1.2', 'press f5', 'wait 1.5', 'press main', 'wait 0.8'] + P.shift_key('n6') + ['wait 1.2', 'press f1', 'wait 1.2']
    return {'lines': L + ['exit'], 'cap': 400, 'floppy': 'floppy/funky.img'}
def sampling():
    L = P.boot() + P.load_first_file(35) + ['down shift', 'up shift', 'wait 0.3', 'press n4', 'wait 0.3', 'down shift', 'up shift', 'wait 2', 'press right', 'wait 1',
         'press window', 'wait 1.5', 'press plus', 'wait 0.8', 'press f5', 'wait 2', 'press f6', 'wait 3', 'press f6', 'wait 14', 'press f6', 'wait 3', 'press f5', 'wait 30']
    return {'lines': L + ['exit'], 'cap': 300, 'floppy': 'floppy/funky.img'}

SUITES = {n: getattr(P, n) for n in ['smoke', 'zone_suite', 'regions_suite2', 'seq_basic', 'seq_edit', 'tracks_song', 'disk_suite', 'trim_suite',
                                      'program_suite', 'mixer_other', 'mute_matrix', 'tour', 'vub_feat1', 'vub_feat2', 'copy_os', 'undo_check']}
SUITES.update({'programs24': programs24, 'sampling': sampling})

def run(name, sysdir):
    s = SUITES[name]()
    body = [l for l in s['lines'] if l != 'exit']
    lines = [tap_on(name)] + body + ['wait 1', tap_dump(name), 'wait 1', 'exit']
    d = H.run('cov_' + name, lines, 'cov', s.get('floppy', 'floppy/funky.img'), s.get('cap', 600) + 400, sound=False)
    ok = os.path.exists(f'{OUT}/{name}.bin') and 'COVDUMP' in H.log_text(d)
    return name, ok

def merged():
    import glob
    m = bytearray(HI - LO)
    for f in glob.glob(OUT + '/*.bin'):
        b = open(f, 'rb').read()
        for i, v in enumerate(b):
            if v: m[i] = 1
    return m

def free_ranges(m, img, minlen=64):
    out = []; i = 0
    while i < len(m):
        if not m[i]:
            j = i
            while j < len(m) and not m[j]: j += 1
            if j - i >= minlen: out.append((LO + i, j - i))
            i = j
        else: i += 1
    return out

if __name__ == '__main__':
    binp = sys.argv[1]; names = sys.argv[2:] or list(SUITES)
    sysdir = os.path.join(HERE, 'sys_cov'); os.makedirs(sysdir, exist_ok=True)
    open(os.path.join(sysdir, 'MPC2KXL.BIN'), 'wb').write(open(binp, 'rb').read())
    H.SYS['cov'] = sysdir
    with cf.ThreadPoolExecutor(2) as ex:
        for name, ok in ex.map(lambda n: run(n, sysdir), names):
            print(f'{name:<16} {"ok" if ok else "NO DUMP"}', flush=True)
    m = merged(); img = open(binp, 'rb').read()
    print('suites merged:', len(os.listdir(OUT)))
    for a, n in free_ranges(m, img):
        nz = sum(1 for k in range(a, min(a + n, 0x78000)) if img[k])
        print(f'never written: {a:#07x}-{a + n - 1:#07x} {n:6d} B   (non-zero image bytes inside: {nz})')
