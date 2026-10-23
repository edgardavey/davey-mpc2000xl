import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build_os', 'suite'))
import phases as P, harness as H
H.SYS['t13'] = os.environ.get('SYSDIR_T13', '')
S = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for i=0,3 do t[#t+1]=sp:read_u16(0x74f56+i*2) end local p={} for i=0,3 do p[#p+1]=sp:read_u8(0x74fd5+i) end '
     'print(string.format("ST @TAG@ t=%.2f open=%d run=%d cnt=%d res=%d t0=%d endms=%d beat=%d taps=%s pads=%s",manager.machine.time:as_double(),sp:read_u8(0x74f40),sp:read_u8(0x74f41),sp:read_u8(0x74f42),sp:read_u8(0x74fc6),sp:read_u16(0x74f46),sp:read_u16(0x74f48),sp:read_u16(0x74f4a),table.concat(t," "),table.concat(p," ")))')
TT = lambda t: S.replace('@TAG@', t)
L = P.boot() + P.load_first_file(35) + ['wait 0.5'] + P.shift_key('n5') + ['wait 1.5', 'press f3', 'wait 1.5', 'press f3', 'wait 1.5'] + ['press f3', 'wait 1', 'press f3', 'wait 1', 'press f3', 'wait 1.5', TT('armed')]
L += ['tap pad1 0', 'wait 0.8', TT('p1'), 'tap pad2 0', 'wait 0.8', TT('p2'), 'tap pad2 0', 'wait 0.2', TT('p2again'), 'wait 0.3', 'tap pad3 0', 'wait 0.2', TT('p3'), 'wait 3', TT('end'), 'exit']
r = H.run('lzres', L, 't13', 'floppy/funky.img', 150, sound=False)
for l in H.log_text(r).split('\n'):
    if l.startswith(('ST', 'LUAERR')): print(l)
