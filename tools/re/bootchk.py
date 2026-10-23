"""bootchk.py BIN [TAG]: boot BIN in the emulator, snap the screen after 30 s, print whether the OS main screen came up."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import harness as H, shutil
d = os.path.join(H.ROOT, 'test_log', 'sys_bootchk'); os.makedirs(d, exist_ok=True); shutil.copy(sys.argv[1], d + '/MPC2KXL.BIN'); H.SYS['bc'] = d
r = H.run('bootchk_' + (sys.argv[2] if len(sys.argv) > 2 else 'x'), ['wait 30', 'snap', 'exit'], 'bc', 'floppy/funky.img', 45, sound=False)
print(r + '/snap/0000.png')
