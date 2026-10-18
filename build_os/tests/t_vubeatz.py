import sys; sys.path.insert(0, 'build_os/tests')
from common import *
VA = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for v=0,31 do local b=0x582b0+0x9609+v*20 local n=sp:read_u8(b+1) if n~=255 and n~=204 then t[#t+1]=v..":"..n end end print("VA %s "..table.concat(t," "))'
def typ(s): return [f'press n{c}' for c in s] + ['press enter', 'wait 0.8']
def minus(n): return [f'tap minus 0.2'] * n
L = ['wait 28'] + shift_key('n3') + ['wait 2','press f6','wait 3','press n3','press n5','press enter','wait 6','press f5','wait 3','press main','wait 1']
L += shift_key('n6') + ['wait 1.5','press f1','wait 2','press down','press right','press minus','wait 0.5','press minus','wait 0.8','snap']   # pad A01 -> note 35 (FUNKY)
# ---- Program Transpose (ASSIGN page) ----
L += ['press down','wait 0.5','press down','wait 0.5','press down','wait 0.5','snap'] + typ('36') + ['snap'] + typ('40') + ['snap'] + typ('0') + minus(45) + ['wait 0.5','snap'] + typ('0') + ['snap']
# ---- TUNE (PARAMS page) ----
L += ['press f2','wait 2','press down','press right','press right','wait 0.6','snap'] + typ('360') + ['snap'] + typ('400') + ['snap'] + typ('0') + minus(370) + ['wait 0.5','snap'] + typ('0') + ['snap']
# ---- ALL: BANK then PROGRAM scope ----
L += ['press f1','wait 1.5','press f2','wait 2'] + ['press up','wait 0.3']*7 + ['press down','wait 0.5','snap'] + typ('7') + ['snap','press f2','wait 1.5','snap','press f4','wait 1.5','snap']      # Attack 7 -> ALL -> BANK
L += ['tap pad2 0','wait 1','snap','press bankb','wait 1','tap pad1 0','wait 1','snap','press banka','wait 1']                                   # A02 should have 7, B01 should not
L += ['press down','wait 0.5'] + typ('9') + ['snap','press f2','wait 1.5','press f5','wait 1.5','snap']                                                # Decay 9 -> ALL -> PROGRAM
L += ['press bankb','wait 1','tap pad1 0','wait 1','snap','press bankc','wait 1','tap pad3 0','wait 1','snap','press banka','wait 1']            # B01 and C03: decay 9, attack not 7
# ---- STOP: single press vs double press ----
L += ['press main','wait 1','tap pad1 0','wait 0.4',VA % 'play','tap stop 0','wait 1',VA % 'single_stop','tap pad1 0','wait 0.4',VA % 'play2','tap stop 0.3','tap stop 0','wait 1',VA % 'double_stop','exit']
print('\n'.join(L))
