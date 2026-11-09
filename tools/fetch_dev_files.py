#!/usr/bin/env python3
"""fetch_dev_files.py  : set up a fresh dev system with everything the tests need that is not in git.

  1. test samples (floppy/*.WAV) from the newest GitHub release that carries davey-dev-files.zip, sha256-checked
  2. floppy images (funky, stereo, test, break, both) built from them with tools/make_floppy.py (any OS)
  3. Akai's stock OS 1.20 downloaded from Akai's own CDN (never redistributed by us), sha256-checked, put at
     build_os/sys_stock/MPC2KXL.BIN, and gold_floppy.img (funky + that OS stamped 2004-11-11 15:11) built from it

  python3 tools/fetch_dev_files.py            fetch + build whatever is missing
  python3 tools/fetch_dev_files.py --pack     (maintainer) make davey-dev-files.zip from floppy/*.WAV and print its sha256
Needs only Python 3. Not covered: VU's updater data (modular.json, only for patcher/gen_data.py; ask the project owner)."""
import hashlib, io, json, os, sys, urllib.request, zipfile, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools')); import make_floppy
REPO = 'edgardavey/davey-mpc2000xl'; ASSET = 'davey-dev-files.zip'
OS_URL = 'https://cdn.inmusicbrands.com/akai/mpc2000xl/mpc2kxl.zip_1114805f0243a1492c5f249c71889b96.zip'
OS_SHA = '100e3375b45072c209ffa2b1dbaecbf740c8c4ea29162827ac11cc6bf9cc7bab'
WAVS = {  # sha256 of every sample the tests use
    'FUNKY.WAV': '2fa7376ad2c7935fb57acfb349ea91cd9e43227b48226ba825073884bb40f39b',
    'NEPAL.WAV': '3ac65d3e2b82ea9797e836dc93a88cc5eb25637c7f0d569243dce4025eac61ee',
    'BREAK.WAV': '4b93191ae09634684e550f4a1e8dce6d5b6addb7209f7120728007f6d6d7b8dd',
    'CHOPTEST.WAV': 'cdbb732dbb82c926c16de0cbed411a74ad3925e984648bf477a47edc558738fc',
    'STEREO.WAV': '8d30ae7df5814e5748aad1758d2bcecab3406d0529560df41d4d800818ccb086'}
IMAGES = {'funky.img': ['FUNKY.WAV'], 'stereo.img': ['STEREO.WAV'], 'test.img': ['CHOPTEST.WAV'], 'break.img': ['BREAK.WAV'],
          'both.img': ['FUNKY.WAV', 'NEPAL.WAV']}
FL = os.path.join(ROOT, 'floppy')
sha = lambda b: hashlib.sha256(b).hexdigest()
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'davey-dev-files'}), timeout=120).read()


def pack():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, h in WAVS.items():
            b = open(os.path.join(FL, n), 'rb').read(); assert sha(b) == h, n + ' differs from the table'; z.writestr(n, b)
    p = os.path.join(ROOT, 'release', ASSET); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(buf.getvalue())
    print('wrote', p, len(buf.getvalue()), 'bytes sha256', sha(buf.getvalue()))


def samples():
    if all(os.path.exists(os.path.join(FL, n)) and sha(open(os.path.join(FL, n), 'rb').read()) == h for n, h in WAVS.items()): return
    rel = json.loads(get(f'https://api.github.com/repos/{REPO}/releases?per_page=30'))
    url = next((a['browser_download_url'] for r in rel for a in r['assets'] if a['name'] == ASSET), None)
    if not url: sys.exit(f'no GitHub release of {REPO} carries {ASSET} yet')
    z = zipfile.ZipFile(io.BytesIO(get(url))); os.makedirs(FL, exist_ok=True)
    for n, h in WAVS.items():
        b = z.read(n); assert sha(b) == h, n + ': sha256 mismatch'; open(os.path.join(FL, n), 'wb').write(b)
    print('samples ok')


def images():
    for img, names in IMAGES.items():
        p = os.path.join(FL, img)
        if os.path.exists(p): continue
        fs = [(n, open(os.path.join(FL, n), 'rb').read(), datetime.datetime(2026, 1, 1)) for n in names]
        open(p, 'wb').write(make_floppy.build(fs)); print('built', p)


def akai_os():
    p = os.path.join(ROOT, 'build_os', 'sys_stock', 'MPC2KXL.BIN')
    if not (os.path.exists(p) and sha(open(p, 'rb').read()) == OS_SHA):
        z = zipfile.ZipFile(io.BytesIO(get(OS_URL)))
        n = next(i for i in z.namelist() if i.lower().endswith('mpc2kxl.bin'))
        b = z.read(n); assert sha(b) == OS_SHA, 'Akai OS sha256 differs from the known 1.20'
        os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(b); print('stock OS ok (from Akai)')
    g = os.path.join(FL, 'gold_floppy.img')
    if not os.path.exists(g):
        fs = [('FUNKY.WAV', open(os.path.join(FL, 'FUNKY.WAV'), 'rb').read(), datetime.datetime(2026, 1, 1)),
              ('MPC2KXL.BIN', open(p, 'rb').read(), datetime.datetime(2004, 11, 11, 15, 11))]   # the stamp matters: see HANDOFF 6
        open(g, 'wb').write(make_floppy.build(fs)); print('built', g)


if __name__ == '__main__':
    if '--pack' in sys.argv: pack()
    else: samples(); images(); akai_os(); print('done')
