"""editfld.py: stock; log every field registration (INT 7D/7E handler 0:4427) while the TRIM Edit window opens and the Edit: value changes."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
BP = 'lua manager.machine.debugger:command("wpset 5a946,2,w,1,{printf \\"WR MAXW %x:%x d=%x\\",ps,pc,wpdata; g}") print("BP")'
MARK = lambda t: f'lua manager.machine.debugger:command("printf \\"WR MARK {t}\\"")'
CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', BP, MARK('open'), 'press f5', 'wait 1.5', 'press f4', 'wait 1', MARK('zone'), 'press f3', 'wait 1.5', 'press f5', 'wait 1.5', MARK('plus2'), 'press plus', 'wait 0.6', 'press plus', 'wait 0.6', MARK('down'), 'press down', 'wait 0.6', MARK('end'), CON, 'exit']
r = H.run('editfld', L, 'stock', 'floppy/funky.img', 120, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('CON', 'LUAERR')): print(l)
