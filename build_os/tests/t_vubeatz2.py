import sys; sys.path.insert(0, 'build_os/tests')
from common import *
VA = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for v=0,31 do local b=0x582b0+0x9609+v*20 local n=sp:read_u8(b+1) if n~=255 and n~=204 then t[#t+1]=v..":"..n end end print("VA %s "..table.concat(t," "))'
def typ(s): return [f'press n{c}' for c in s] + ['press enter', 'wait 0.8']
L = ['wait 28'] + shift_key('n3') + ['wait 2','press f6','wait 3','press n3','press n5','press enter','wait 6','press f5','wait 3','press main','wait 1']
L += shift_key('n6') + ['wait 1.5','press f1','wait 2'] + ['press down','wait 0.5']*3 + ['snap']          # Transpose field
L += typ('36') + ['snap'] + typ('40') + ['snap'] + typ('7') + ['snap'] + ['tap minus 0.2'] * 3 + ['wait 0.5','snap'] + typ('0')
L += ['tap minus 0.2'] * 45 + ['wait 0.5','snap'] + typ('0') + ['snap']                                   # 0 -> wheel down to the limit -> back to 0
L += ['press up','wait 0.4'] * 4 + ['press down','wait 0.5','press right','wait 0.5','press minus','wait 0.5','press minus','wait 0.8','snap']   # pad A01 -> note 35 (FUNKY)
L += ['press main','wait 1','tap pad1 0','wait 0.4',VA % 'play','snap','tap stop 0','wait 1',VA % 'single_stop','tap pad1 0','wait 0.4',VA % 'play2','tap stop 0.3','tap stop 0','wait 1',VA % 'double_stop','exit']
print('\n'.join(L))
