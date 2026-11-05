"""lofiprobe.py SYSDIR PLUS [FLOPPY]: TRIM > F5 EDIT, wheel PLUS steps, DO IT; dump the original and the current sound (header + data stats)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
H.SYS['lp'] = sys.argv[1]; n = int(sys.argv[2])
SAVE = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] origo=sp:read_u16(0x582b0+0xd7c2) origs=sp:read_u16(0x582b0+0xd7c4) print("ORIG", string.format("%04x:%04x",origs,origo))')
DUMP = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local d=manager.machine.devices[":dsp"].spaces["l6028"] '
        'local function info(tag,s,o) local a=s*16+o local nm="" for i=0x12,0x21 do nm=nm..string.char(sp:read_u8(a+i)) end '
        ' local da=sp:read_u32(a+0x0a) local len=sp:read_u32(a+0x2e) local st=sp:read_u8(a+0x25) local low=0 local sum=0 '
        ' for i=1000,1999 do local w=d:read_u16((da+i)*2) if (w & 0xf)~=0 then low=low+1 end sum=(sum+w)%65536 end '
        ' local held=0 for i=1000,1998 do if d:read_u16((da+i)*2)==d:read_u16((da+i+1)*2) then held=held+1 end end '
        ' print(string.format("SND %s %04x:%04x name=[%s] st=%d len=%d dsp=%x low4bits=%d held=%d sum=%04x",tag,s,o,nm,st,len,da,low,held,sum)) end '
        'info("orig",origs,origo) info("cur",sp:read_u16(0x582b0+0xd7c4),sp:read_u16(0x582b0+0xd7c2))')
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', SAVE, DUMP.replace('"orig"', '"before"'), 'press f5', 'wait 1.5'] + ['press plus', 'wait 0.6'] * n + ['snap', 'press f5', 'wait 1.5', 'snap', 'wait 12', 'snap', DUMP, 'exit']
r = H.run('lofiprobe_%d' % n, L, 'lp', sys.argv[3] if len(sys.argv) > 3 else 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('SND', 'ORIG', 'LUAERR')): print(l)
print(r)
