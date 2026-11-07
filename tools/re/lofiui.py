"""lofiui.py BIN PLUS: TRIM > F5 EDIT > PLUS wheel steps; snap; cursor down x2 (Rate), data +; hit pad 3; snap each step."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
sysd = os.path.abspath('exp_reloc/sys_probe'); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read()); H.SYS['pp'] = sysd
plus = int(sys.argv[2]) if len(sys.argv) > 2 else 8
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', 'press f5', 'wait 1.5'] + ['press plus', 'wait 0.6'] * plus + ['snap']
L += ['press f3', 'wait 0.8', 'snap', 'press f3', 'wait 0.8', 'snap', 'press f1', 'wait 0.8', 'snap', 'press down', 'wait 0.6', 'snap', 'tap pad3 0', 'wait 1', 'snap', 'press plus', 'wait 0.6', 'snap', 'exit']
r = H.run('lofiui_%d' % plus, L, 'pp', 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith('LUAERR'): print(l)
print(r)
