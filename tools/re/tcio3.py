"""tcio3.py: stock; log every INT 91 (file I/O) call with bx/es:di/ds:si/cx during SAVE of the .ALL (and its timing byte check)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
SET = 'lua manager.machine.devices[":maincpu"].spaces["program"]:write_u8(0x22e67,6) print("SET")'
BP = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local a=sp:read_u16(0x91*4)+16*sp:read_u16(0x91*4+2) '
      'manager.machine.debugger:command(string.format("bpset %x,1,{printf \\"WR I91 bx=%%x es=%%x di=%%x ds=%%x si=%%x cx=%%x ax=%%x\\",bw,ds1,iy,ds0,ix,cw,aw; g}",a)) print(string.format("BP91 %x",a))')
MARK = lambda t: f'lua manager.machine.debugger:command("printf \\"WR MARK {t}\\"")'
CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
L = P.boot() + P.load_first_file(37) + ['press main', 'wait 1', SET, 'wait 0.3']
L += P.shift_key('n3') + ['wait 2', 'press f2', 'wait 1.5', 'press up', 'wait 0.5', BP, MARK('save'), 'press f6', 'wait 2', 'press f5', 'wait 6', 'snap', 'press f5', 'wait 4', 'snap', MARK('end'), CON, 'exit']
r = H.run('tcio3', L, 'stock', 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('CON', 'BP91', 'LUAERR')): print(l)
