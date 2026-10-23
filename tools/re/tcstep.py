import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
BP = 'lua manager.machine.debugger:command("bpset 4509,1,{printf \\"WR STEP aw=%x cw=%x bw=%x ss=%x sp=%x\\",aw,cw,bw,ss,sp; g}") print("BP")'
MARK = lambda t: f'lua manager.machine.debugger:command("printf \\"WR MARK {t}\\"")'
CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
L = P.boot() + P.load_first_file(37) + ['press main', 'wait 1', 'press down', 'wait 0.4', 'press right', 'wait 0.4', 'press right', 'wait 0.6', BP, MARK('plus'), 'press plus', 'wait 0.5', MARK('minus'), 'press minus', 'wait 0.5', MARK('end'), CON, 'exit']
r = H.run('tcstep', L, 'stock', 'floppy/funky.img', 100, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith('CON'): print(l)
