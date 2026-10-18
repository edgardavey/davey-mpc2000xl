import sys; sys.path.insert(0, 'build_os/tests')
from common import *
ZD = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local b=0x582b0 local t={} for i=0,17 do t[#t+1]=sp:read_u16(b+0x8e72+i*4)+65536*sp:read_u16(b+0x8e74+i*4) end print("ZONES %s n="..sp:read_u8(b+0xd7dc).." cur="..sp:read_u8(b+0xd7dd).." B="..table.concat(t," "))'
TS = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for i=0,15 do t[#t+1]=sp:read_u16(0x70174+i*2) end print("TAPS %s cnt="..sp:read_u8(0x70162).." open="..sp:read_u8(0x70160).." run="..sp:read_u8(0x70161).." req="..sp:read_u8(0x70163).." taps="..table.concat(t," "))'
def zones(tag): return [ZD % tag]
def taps(tag): return [TS % tag]
def open_window(): return ['press window','wait 1.5','press f6','wait 2']
L = ['wait 28'] + shift_key('n3') + ['wait 2','press f6','wait 3','press n3','press n5','press enter','wait 6','press f5','wait 3','press main','wait 1'] \
    + shift_key('n5') + ['wait 1.5','press f3','wait 1.5'] + ['press right']*4 + ['wait 1','snap']
# A: PLAY mode, 5 taps
L += open_window() + ['snap','down f6','wait 0.3'] + [x for k in range(5) for x in ([f'tap pad{k+2} 0'] + ['wait 0.4'])][:-1] + ['wait 0.3','up f6','wait 0.5'] + taps('A') + ['press f5','wait 2'] + zones('A') + ['snap']
# B: pad start, 3 taps, UNDO, one more tap (still inside the sound), DO IT
L += open_window() + ['tap pad1 0','wait 0.5','tap pad2 0','wait 0.4','tap pad3 0','wait 0.3','press f3','wait 0.4','tap pad4 0','wait 0.5'] + taps('B') + ['press f5','wait 2'] + zones('B')
# C: debounce (two taps 10 ms apart) and the end-of-sound guard (taps after the sample ends are ignored)
L += open_window() + ['down f6','wait 0.3','tap pad2 0','wait 0.01','tap pad3 0','wait 0.5','tap pad4 0','wait 2.6','tap pad5 0','wait 0.3','up f6','wait 0.4'] + taps('C') + ['press f4','wait 2'] + zones('C')
# D: 16-tap limit
L += open_window() + ['down f6','wait 0.2'] + [x for k in range(20) for x in ([f'tap pad{(k%15)+1} 0'] + ['wait 0.11'])] + ['up f6','wait 0.4'] + taps('D') + ['press f5','wait 2'] + zones('D') + ['snap']
# E: abandon the window with MAIN: pads must stop being swallowed
L += open_window() + ['press main','wait 1.5','tap pad1 0','wait 1'] + taps('E') + ['exit']
print('\n'.join(L))
