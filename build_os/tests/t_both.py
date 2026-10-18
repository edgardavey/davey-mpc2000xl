import sys; sys.path.insert(0, 'build_os/tests')
from common import *
ZD = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local b=0x582b0 local t={} for i=0,7 do t[#t+1]=sp:read_u16(b+0x8e72+i*4)+65536*sp:read_u16(b+0x8e74+i*4) end print("ZONES %s n="..sp:read_u8(b+0xd7dc).." B="..table.concat(t," "))'
on=[0.025,0.100,0.334,0.394,0.668,1.162,1.467,1.646,1.811,1.956,2.125,2.180,2.255,2.454]
def zone_chop(tag):
    L = shift_key('n5') + ['wait 1.5','press f3','wait 1.5'] + ['press right']*4 + ['wait 1','press window','wait 1.5','press f6','wait 2','down f6','wait 0.3']
    L += [x for k in range(5) for x in ([f'tap pad{k+2} 0'] + ['wait 0.4'])][:-1] + ['wait 0.3','up f6','wait 0.5','snap','press f5','wait 2'] + [ZD % tag,'snap']
    return L
L = ['wait 28'] + shift_key('n3') + ['wait 2','press f6','wait 3','press n3','press n5','press enter','wait 6','press f5','wait 3','press main','wait 1']
L += zone_chop('first_zone_chop')
# vubeatz REGIONS lazy chop on the same sound
L += ['press main','wait 1.5','press pad1','press levels','wait 1','press down','press plus','press plus','press f2','wait 2','press f3','press f3','press f3','wait 1','wait 0.5','tap pad1 0']
t = 0
for k, c in enumerate(on[1:]):
    cut = c - 0.01; L += [f'wait {cut-t:.3f}', f'tap pad{k+2} 0']; t = cut
L += ['wait 1.2','snap','press f5','wait 1.5','press f6','wait 2','snap','press main','wait 1.5','tap pad8 0','wait 1.5']
# zone lazy chop again
L += zone_chop('second_zone_chop') + ['exit']
print('\n'.join(L))
