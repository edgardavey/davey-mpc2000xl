"""lofibp.py BIN LIN[,LIN..]: TRIM > F5 EDIT > 8 plus, then cursor down x2; log hits of the linear breakpoints (printf name aw)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
sysd = os.path.abspath('exp_reloc/sys_probe'); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read()); H.SYS['pp'] = sysd
CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
def WP(a):
    a, n = (a.split(':') + ['2'])[:2]
    return 'lua manager.machine.debugger:command("wpset %s,%s,r,1,{printf \\"WR WP %s %%x:%%x\\",ps,pc; g}") print("WPSET")' % (a, n, a)
G = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print(string.format("CON FLD %%s desc=%%04x:%%04x var=%%04x:%%04x idx=%%x e=%%x", "%s", sp:read_u16(0x582b0+0x8b1c), sp:read_u16(0x582b0+0x8b1a), sp:read_u16(0x582b0+0x8b20), sp:read_u16(0x582b0+0x8b1e), sp:read_u16(0x582b0+0x8d56), sp:read_u16(0x582b0+0x8d4c)))'
def BP(a): return 'lua manager.machine.debugger:command("bpset %s,1,{printf \\"WR BP %s ret=%%x:%%x a=%%x:%%x\\",w@((ss<<4)+sp+2),w@((ss<<4)+sp),w@((ss<<4)+sp+6),w@((ss<<4)+sp+4); g}") print("BPSET")' % (a, a)
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', 'press f5', 'wait 1.5'] + ['press plus', 'wait 0.6'] * 8
L += [(WP(a[1:]) if a.startswith('w') else BP(a)) for a in sys.argv[2].split(',')] + [G % 'open', 'press down', 'wait 0.6', G % 'down1', 'lua manager.machine.debugger:command("printf \\"WR MARK down1\\"")', 'press down', 'wait 0.6', G % 'down2', 'press plus', 'wait 0.6', 'lua manager.machine.debugger:command("printf \\"WR MARK plus\\"")', 'snap', 'lua manager.machine.devices[":maincpu"].spaces["program"]:write_u8(0xfe70+0x63,1)', 'wait 1', 'snap', 'lua print("CON F63 "..manager.machine.devices[":maincpu"].spaces["program"]:read_u8(0xfe70+0x63))', CON, 'exit']
r = H.run('lofibp', L, 'pp', 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('CON', 'LUAERR')): print(l)
