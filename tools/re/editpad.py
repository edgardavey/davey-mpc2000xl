"""editpad.py BIN: TRIM > F5 EDIT > SP1200 NEW SOUND; hit pads in the Edit window; print the current sound name and the DSP key-on mask after each hit."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
sysd = os.path.abspath('exp_reloc/sys_probe'); os.makedirs(sysd, exist_ok=True)
open(sysd + '/MPC2KXL.BIN', 'wb').write(open(sys.argv[1], 'rb').read()); H.SYS['pp'] = sysd
CUR = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local s=sp:read_u16(0x582b0+0xd7c4) local o=sp:read_u16(0x582b0+0xd7c2) local a=s*16+o local nm="" '
       'for i=0x12,0x21 do nm=nm..string.char(sp:read_u8(a+i)) end print("@T@ cur "..nm.." ctx "..string.format("%04x:%04x",sp:read_u16(0x582b0+0x98a8),sp:read_u16(0x582b0+0x98a6)))')
VOX = ('lua local d=manager.machine.devices[":dsp"] local n=0 for i=0,31 do end print("@T@ vox")')
L = P.boot() + P.load_first_file(35) + P.shift_key('n5') + ['wait 2', CUR.replace('@T@', 'trim'), 'press f5', 'wait 1.5'] + ['press plus', 'wait 0.6'] * 8 + ['snap', CUR.replace('@T@', 'edit0')]
L += ['tap pad2 0', 'wait 0.5', 'snap', CUR.replace('@T@', 'pad2'), 'wait 1', 'snap', 'tap pad3 0', 'wait 0.5', CUR.replace('@T@', 'pad3'), 'snap', 'exit']
r = H.run('editpad', L, 'pp', 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if ' cur ' in l or l.startswith('LUAERR'): print(l)
print(r)
