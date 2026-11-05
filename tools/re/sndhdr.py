"""sndhdr.py BUILD: dump the current sound's header (far ptr 582B:[D7C2]) for a disk-loaded sound and for a fresh recording."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
D = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local o=sp:read_u16(0x582b0+0xd7c2) local s=sp:read_u16(0x582b0+0xd7c4) local a=s*16+o '
     'local t={} for i=0,0x3f do t[#t+1]=string.format("%02x",sp:read_u8(a+i)) end print(string.format("HDR %s %05x ",a)..table.concat(t," "))')
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', D.replace('%s', 'loaded')]
L += ['press main', 'wait 1'] + P.shift_key('n4') + ['wait 2', 'press f6', 'wait 3', 'press f6', 'wait 4', 'press f6', 'wait 3', 'press f5', 'wait 3'] + P.shift_key('n5') + ['wait 2', D.replace('%s', 'recorded'), 'exit']
r = H.run('sndhdr', L, sys.argv[1] if len(sys.argv) > 1 else 'stock', sys.argv[2] if len(sys.argv) > 2 else 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('HDR', 'LUAERR')): print(l)
