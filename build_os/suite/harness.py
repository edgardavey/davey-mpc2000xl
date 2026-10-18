"""Test harness: run a command script on one or two builds, collect snapshots/log, compare, and keep an issues list."""
import os, sys, subprocess, shutil, hashlib, time, json, re
from PIL import Image, ImageChops
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # repo root
SYS = {'stable': ROOT + '/build_os/sys_stable', 'davey': ROOT + '/build_os/sys_new', 'stock': ROOT + '/build_os/sys_stock', 'r2': ROOT + '/build_os/sys_r2', 'r2dark': ROOT + '/build_os/sys_r2dark'}
LOG = ROOT + '/test_log'
SH = ['down shift', 'up shift', 'wait 0.3']
def shift_key(k): return SH + [f'press {k}', 'wait 0.3'] + SH
def boot(): return ['wait 28']
def load_first_file(note=35):
    ns = [f'press n{c}' for c in str(note)]
    return shift_key('n3') + ['wait 2', 'press f6', 'wait 3'] + ns + ['press enter', 'wait 6', 'press f5', 'wait 3', 'press main', 'wait 1']
def typ(s): return [f'press n{c}' for c in s] + ['press enter', 'wait 0.8']
def luaprint(tag, expr_body): return f'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] {expr_body}'

def run(name, lines, build, floppy='floppy/funky.img', cap=600, sound=True):
    """Run a script (list of command lines) on a build; return result dir."""
    d = f'{LOG}/runs/{name}/{build}'
    if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(d)
    script = d + '/script.txt'; open(script, 'w').write('\n'.join(lines) + '\n')
    env = dict(os.environ, SYSDIR=SYS[build], CAP=str(cap), SOUNDOPT='sdl' if sound else 'none')
    # watchdog (2026-10-17): an emulator run that stops progressing used to hang the whole suite for hours.
    # Wall-clock limit = 3x the emulated length (min 5 min); on expiry the run is killed, logged as EMULATOR STALL and retried once.
    for attempt in (1, 2):
        p = subprocess.Popen([os.environ.get('MPC_EMU', ROOT) + '/tools/dev/run_script.sh', script, floppy], cwd=ROOT, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, _ = p.communicate(timeout=max(300, 3 * cap)); break
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 9); p.communicate()
            print(f'EMULATOR STALL in {name} (attempt {attempt}), killed after {max(300, 3 * cap)} s', flush=True)
            if attempt == 2:
                open(d + '/out.log', 'w').write(f'EMULATOR STALL: {name} stalled twice; result not trustworthy\n'); return d
    snapdir = stdout.strip().split('\n')[-1]           # <session>/snap/mpc2000xldiag
    sess = os.path.dirname(os.path.dirname(snapdir))
    if os.path.isdir(snapdir): shutil.copytree(snapdir, d + '/snap')
    shutil.copy(sess + '/out.log', d + '/out.log')
    for f in ('media/floppy.img',):
        if os.path.exists(sess + '/' + f): shutil.copy(sess + '/' + f, d + '/floppy_after.img')
    return d

def log_text(d): return open(d + '/out.log', errors='replace').read()
def health(d, script_lines):
    """Basic health: finished (speed line printed), no Lua errors, snapshot count matches number of snap commands."""
    t = log_text(d); n_snap = sum(1 for l in script_lines if l == 'snap')
    got = len(os.listdir(d + '/snap')) if os.path.isdir(d + '/snap') else 0
    return {'finished': 'Average speed' in t, 'lua_errors': re.findall(r'LUAERR.*', t), 'snaps_expected': n_snap, 'snaps_got': got,
            'errors': [l for l in t.split('\n') if re.search(r'(?i)\b(error|fatal|exception|assert)\b', l) and 'LUAERR' not in l][:5]}

def phash(p): return hashlib.sha256(Image.open(p).convert('1').tobytes()).hexdigest()
def compare_snaps(da, db):
    fa = sorted(os.listdir(da + '/snap')) if os.path.isdir(da + '/snap') else []; fb = sorted(os.listdir(db + '/snap')) if os.path.isdir(db + '/snap') else []
    diff = [n for n in fa if n in fb and phash(da + '/snap/' + n) != phash(db + '/snap/' + n)]
    return {'a': len(fa), 'b': len(fb), 'diff': diff}
def grep_lines(d, prefix): return [l for l in log_text(d).split('\n') if l.startswith(prefix)]
def sheet(d, idx, name, cols=2, crop=(0, 0, 248, 60), scale=3):
    fs = sorted(os.listdir(d + '/snap'))
    ims = [Image.open(d + '/snap/' + fs[i]).crop(crop) for i in idx if i < len(fs)]
    w = crop[2] - crop[0]; h = crop[3] - crop[1]; rows = (len(ims) + cols - 1) // cols
    o = Image.new('RGB', (w * cols, h * rows), (255, 255, 255))
    for k, im in enumerate(ims): o.paste(im, ((k % cols) * w, (k // cols) * h))
    o.resize((w * cols * scale, h * rows * scale), Image.NEAREST).save(d + '/' + name)
    return d + '/' + name
