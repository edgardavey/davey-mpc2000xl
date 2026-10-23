"""tcdiv.py SYS VALUE: stock OS with Timing forced to VALUE; exercise step keys / record / play; report any divide error (INT 0 -> 0:0401)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
v = int(sys.argv[2])
SET = f'lua manager.machine.devices[":maincpu"].spaces["program"]:write_u8(0x22e67,{v}) print("SET {v}")'
BP = 'lua manager.machine.debugger:command("bpset 401,1,{printf \\"WR DIVERR\\"; g}") manager.machine.debugger:command("bpset 7f37,1,{printf \\"WR P7F37\\"; g}") manager.machine.debugger:command("bpset 7f0f,1,{printf \\"WR P7F0F\\"; g}") manager.machine.debugger:command("bpset 4df6,1,{printf \\"WR GRIDREAD\\"; g}")'
MARK = lambda t: f'lua manager.machine.debugger:command("printf \\"WR MARK {t}\\"")'
CON = 'lua for i,l in ipairs(manager.machine.debugger.consolelog) do if l:find("WR ") then print("CON "..l) end end'
L = P.boot() + P.load_first_file(37) + ['press main', 'wait 1', SET, BP, MARK('main_step')]
L += ['press stepnext', 'wait 0.6'] * 3 + ['press stepprev', 'wait 0.6'] * 2 + ['press barnext', 'wait 0.6', MARK('rec')]
L += ['down rec', 'wait 0.2', 'press play', 'wait 0.2', 'up rec', 'wait 2.5', 'tap pad1 0', 'wait 0.62', 'tap pad1 0', 'wait 1.5', 'press stop', 'wait 1', MARK('stepedit')]
L += ['press f1', 'wait 2'] + ['press stepnext', 'wait 0.6'] * 4 + ['press stepprev', 'wait 0.6'] * 2 + ['snap', MARK('overdub'), 'press main', 'wait 1']
L += ['down overdub', 'wait 0.2', 'press play', 'wait 0.2', 'up overdub', 'wait 2', 'tap pad2 0', 'wait 1', 'press stop', 'wait 1', 'snap', MARK('end'), CON, 'exit']
r = H.run('tcdiv_' + sys.argv[1] + str(v), L, sys.argv[1], 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith('CON') or 'LUAERR' in l: print(l)
print(r)
