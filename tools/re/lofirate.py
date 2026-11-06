"""lofirate.py BIN: TRIM > F5 EDIT > 8 plus > down x2 > plus x3; print v_ridx (75E6:02C2) after each step and snap."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
sysd = os.path.abspath('exp_reloc/sys_probe'); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read()); H.SYS['pp'] = sysd
RI = lambda t: 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] print(string.format("CON RIDX %s %%d fld=%%04x:%%04x", sp:read_u16(0x75e60+0x2c2), sp:read_u16(0x582b0+0x8b1c), sp:read_u16(0x582b0+0x8b1a)))' % t
CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', 'press f5', 'wait 1.5'] + ['press plus', 'wait 0.6'] * 8
L += ['press down', 'wait 0.6', 'press down', 'wait 0.6', RI('a0'), 'press plus', 'wait 0.6', RI('a1'), 'press plus', 'wait 0.6', RI('a2'), 'snap', 'press minus', 'wait 0.6', RI('a3'), 'exit']
r = H.run('lofirate', L, 'pp', 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('CON', 'LUAERR')): print(l)
print(r)
