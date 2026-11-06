"""editpad_snd.py BIN [PLUS]: audio check, TRIM > F5 EDIT (PLUS wheel steps) > hit a pad: RMS of the capture before and after the hit (TRIM hit first for reference)."""
import sys, os, re, struct, subprocess
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'build_os', 'suite'))
import phases as P, harness as H
sysd = os.path.abspath(os.path.join(ROOT, 'exp_reloc/sys_probe')); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read())
plus = int(sys.argv[2]) if len(sys.argv) > 2 else 8
TM = lambda t: 'lua print(string.format("TM %s %.3f","' + t + '",manager.machine.time:as_double()))'
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', TM('a0'), 'tap pad1 0', 'wait 0.3', TM('a1'), 'wait 3', 'press f5', 'wait 1.5'] + ['press plus', 'wait 0.6'] * plus
F65 = lambda t: 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print("F65 %s "..sp:read_u8(0xfe70+0x65).." 62="..sp:read_u8(0xfe70+0x62).." 67="..sp:read_u8(0xfe70+0x67))' % t
L += [F65('edit'), 'lua manager.machine.devices[":maincpu"].spaces["program"]:write_u8(0xfe70+0x65,0)', 'wait 1', TM('b0'), 'wait 1', TM('b1'), 'tap pad1 0', 'wait 0.3', TM('b2'), 'wait 1', TM('b3'), 'snap', 'exit']
sc = os.path.join(ROOT, 'test_log', 'editpad.txt'); open(sc, 'w').write('\n'.join(L) + '\n'); w = os.path.join(ROOT, 'test_log', 'editpad.wav')
out = subprocess.run([os.path.join(ROOT, 'tools/dev/run_script_snd.sh'), sc, 'floppy/funky.img'], cwd=ROOT, env=dict(os.environ, SYSDIR=sysd, CAP='150', WAV=w), capture_output=True, text=True)
lg = open(os.path.dirname(os.path.dirname(out.stdout.strip().split('\n')[-1])) + '/out.log', errors='replace').read()
T = {m.group(1): float(m.group(2)) for m in re.finditer(r'TM (\S+) ([\d.]+)', lg)}
raw = open(w, 'rb').read(); ch, sr = struct.unpack_from('<HI', raw, 22); i = raw.index(b'data'); dl, = struct.unpack_from('<I', raw, i + 4)
a = struct.unpack_from('<%dh' % (min(dl, len(raw) - i - 8) // 2), raw, i + 8)
rms = lambda x, y: (sum(v * v for v in a[int(x * sr) * ch:int(y * sr) * ch]) / max(1, int((y - x) * sr) * ch)) ** 0.5
print([l for l in lg.split('\n') if 'F65' in l]); print('TRIM hit  :', round(rms(T['a0'], T['a1'] + 1)))
print('Edit quiet:', round(rms(T['b0'], T['b1'])))
print('Edit hit  :', round(rms(T['b2'], T['b3'])))
