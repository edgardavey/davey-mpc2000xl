"""smpst.py BUILD: sample (arm, start, stop, KEEP), then TRIM: snap the SAMPLE page and TRIM (is St at 0?)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
H.SYS['t13'] = os.environ.get('SYSDIR_T13', '')
L = P.boot() + P.shift_key('n4') + ['wait 2', 'snap', 'press f6', 'wait 3', 'snap', 'press f6', 'wait 6', 'press f6', 'wait 3', 'snap', 'press f5', 'wait 3', 'snap']
L += P.shift_key('n5') + ['wait 3', 'snap', 'exit']
r = H.run('smpst_' + sys.argv[1], L, sys.argv[1], 'floppy/funky.img', 120, sound=False)
print(r)
