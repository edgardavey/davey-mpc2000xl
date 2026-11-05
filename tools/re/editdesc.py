"""editdesc.py: stock; dump the current field descriptor (far ptr 582B:8B1A) in the TRIM Edit window and the ZONE Edit window."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
D = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local o=sp:read_u16(0x582b0+0x8b1a) local s=sp:read_u16(0x582b0+0x8b1c) local a=s*16+o '
     'local t={} for i=0,0x27 do t[#t+1]=string.format("%02x",sp:read_u8(a+i)) end print(string.format("DESC @TAG@ %04x:%04x ",s,o)..table.concat(t," "))')
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', 'press f5', 'wait 1.5', 'press plus', 'wait 0.6', D.replace('@TAG@', 'trim')]
L += ['press f4', 'wait 1', 'press main', 'wait 1'] + P.shift_key('n5') + ['wait 2', 'press f3', 'wait 1.5', 'press f5', 'wait 1.5', 'press plus', 'wait 0.6', D.replace('@TAG@', 'zone'), 'snap', 'exit']
r = H.run('editdesc', L, 'stock', 'floppy/funky.img', 140, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('DESC', 'LUAERR')): print(l)
