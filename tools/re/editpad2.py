"""editpad2.py BIN: chop + APPLY (pads 1-n get slices), TRIM > F5 EDIT > SP1200 NEW SOUND; hit pad3 / pad1 in the Edit window: log the current sound, RMS after each hit, snap."""
import sys, os, re, struct, subprocess
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'build_os', 'suite')); sys.path.insert(0, os.path.join(ROOT, 'exp_reloc'))
import phases as P, harness as H, test_exp as T
sysd = os.path.abspath(os.path.join(ROOT, 'exp_reloc/sys_probe')); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read())
N = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local o=sp:read_u16(0x582b0+0xd7c2) local s=sp:read_u16(0x582b0+0xd7c4) local t={} for i=0x12,0x1d do t[#t+1]=string.char(sp:read_u8(s*16+o+i)) end print("SND @T@ "..table.concat(t))'
TM = lambda t: 'lua print(string.format("TM %s %.3f","' + t + '",manager.machine.time:as_double()))'
L = P.boot() + P.load_first_file(35) + T.chop_enter() + ['press f3', 'wait 1', 'press f5', 'wait 2', 'press f5', 'wait 12', 'press main', 'wait 1']
L += P.shift_key('n5') + ['wait 2', N.replace('@T@', 'trim'), 'press f5', 'wait 1.5'] + ['press plus', 'wait 0.6'] * 8 + ['snap', TM('q0'), 'wait 1', TM('q1'), 'tap pad3 0', TM('p3'), 'wait 1.5', N.replace('@T@', 'pad3'), 'snap', 'tap pad1 0', TM('p1'), 'wait 1.5', N.replace('@T@', 'pad1'), 'snap', 'tap pad12 0', 'wait 1', N.replace('@T@', 'pad12'), 'press f5', 'wait 20', 'snap', N.replace('@T@', 'done'), 'exit']
sc = os.path.join(ROOT, 'test_log', 'editpad2.txt'); open(sc, 'w').write('\n'.join(L) + '\n'); w = os.path.join(ROOT, 'test_log', 'editpad2.wav')
out = subprocess.run([os.path.join(ROOT, 'tools/dev/run_script_snd.sh'), sc, 'floppy/funky.img'], cwd=ROOT, env=dict(os.environ, SYSDIR=sysd, CAP='260', WAV=w), capture_output=True, text=True)
d = os.path.dirname(os.path.dirname(out.stdout.strip().split('\n')[-1])); lg = open(d + '/out.log', errors='replace').read()
for l in lg.split('\n'):
    if l.startswith(('SND', 'LUAERR')): print(l)
Tm = {m.group(1): float(m.group(2)) for m in re.finditer(r'TM (\S+) ([\d.]+)', lg)}
raw = open(w, 'rb').read(); ch, sr = struct.unpack_from('<HI', raw, 22); i = raw.index(b'data'); dl, = struct.unpack_from('<I', raw, i + 4)
a = struct.unpack_from('<%dh' % (min(dl, len(raw) - i - 8) // 2), raw, i + 8)
rms = lambda x, y: (sum(v * v for v in a[int(x * sr) * ch:int(y * sr) * ch]) / max(1, int((y - x) * sr) * ch)) ** 0.5
print('quiet', round(rms(Tm['q0'], Tm['q1'])), 'pad3 hit', round(rms(Tm['p3'], Tm['p3'] + 0.8)), 'pad1 hit', round(rms(Tm['p1'], Tm['p1'] + 0.8)))
print(d)
