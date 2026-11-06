"""padargs.py BIN LIN: TRIM page, hit pads 1, 3, 13 (and bank B pad 1): log aw/cw/dw at LIN (the TRIM pad event handler) and the zone_chop last-note byte."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
sysd = os.path.abspath('exp_reloc/sys_probe'); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read()); H.SYS['pp'] = sysd
BP = 'lua manager.machine.debugger:command("bpset %s,1,{printf \\"WR PAD aw=%%x cw=%%x dw=%%x bw=%%x\\",aw,cw,dw,bw; g}") print("BPSET")' % sys.argv[2]
CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', BP, 'tap pad1 0', 'wait 1', 'tap pad3 0', 'wait 1', 'tap pad13 0', 'wait 1', 'press bank_b' if False else 'wait 0.1', CON, 'exit']
r = H.run('padargs', L, 'pp', 'floppy/funky.img', 100, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('CON', 'LUAERR')): print(l)
