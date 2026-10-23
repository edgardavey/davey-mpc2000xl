"""smpst4.py: stock; writers of the sound Start fields (0x618A4, 0x61BF0) while sampling and KEEP."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
TAP = ('lua local cpu=manager.machine.devices[":maincpu"] local sp=cpu.spaces["program"] '
       'stt=sp:install_write_tap(0x618a0,0x618b3,"st",function(off,data,mask) print(string.format("TW %x d=%x m=%x pc=%x:%x",off,data,mask,cpu.state["PS"].value,cpu.state["PC"].value)) end) '
       'stu=sp:install_write_tap(0x61bec,0x61bfb,"su",function(off,data,mask) print(string.format("TW %x d=%x m=%x pc=%x:%x",off,data,mask,cpu.state["PS"].value,cpu.state["PC"].value)) end) print("TAPON")')
M = lambda t: f'lua print("MARK {t}")'
L = P.boot() + [TAP] + P.shift_key('n4') + ['wait 2', M('arm'), 'press f6', 'wait 3', M('start'), 'press f6', 'wait 6', M('stop'), 'press f6', 'wait 3', M('keep'), 'press f5', 'wait 3', M('trim')]
L += P.shift_key('n5') + ['wait 3', 'exit']
r = H.run('smpst4', L, 'stock', 'floppy/funky.img', 120, sound=False)
import collections; c = collections.OrderedDict(); cur = ''
for l in H.log_text(r).split('\n'):
    if l.startswith('MARK'): cur = l; continue
    if l.startswith('TW'):
        k = (cur, l.split()[1], l.split()[4]); c.setdefault(k, []).append(l.split()[2])
for k, v in c.items(): print(k, v[:3], len(v))
