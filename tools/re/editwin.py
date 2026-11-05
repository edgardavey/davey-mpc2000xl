"""editwin.py BUILD: TRIM > F5 EDIT, step through the Edit: list (snap each), then SECTION -> NEW SOUND DO IT (snap)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', 'press f5', 'wait 1.5', 'snap']
L += ['press plus', 'wait 0.6', 'snap'] * 9 + ['press minus', 'wait 0.6'] * 7 + ['snap', 'press f5', 'wait 2', 'snap', 'press f5', 'wait 3', 'snap', 'exit']
r = H.run('editwin', L, sys.argv[1] if len(sys.argv) > 1 else 'stock', 'floppy/funky.img', 150, sound=False)
print(r)
