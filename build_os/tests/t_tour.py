import sys; sys.path.insert(0, 'build_os/tests')
from common import *
def mode(k): return shift_key(k) + ['wait 1.5']
def softs(keys, wait=1.2): 
    out = []
    for f in keys: out += [f'press {f}', f'wait {wait}', 'snap']
    return out
L = ['wait 28', 'snap']
L += mode('n3') + ['snap'] + ['press f6','wait 3','snap','press n3','press n5','press enter','wait 6','snap','press f5','wait 3','snap','press main','wait 1','snap']
# main page soft keys
L += softs(['f1','main','f2','main','f3','main','f4','main'])
# mode pages (Song, Misc, Load, Sample, Trim, Program, Mixer, Other, MIDI/Sync)
for n, sk in (('n1',['f1','f2','f3','f4','f5','f6']),('n2',['f1','f2','f3','f4','f5','f6']),('n3',['f1','f2','f3','f4']),('n4',['f1','f2','f3','f4','f5','f6']),
              ('n5',['f1','f2','f3','f4','f5','f6']),('n7',['f1','f2','f3','f4']),('n8',['f1','f2','f3']),('n9',['f1','f2','f3','f4','f5','f6'])):
    L += mode(n) + ['snap'] + softs(sk) + ['press main','wait 1']
# program mode: select drum 1, then pages
L += mode('n6') + ['snap','press f1','wait 2','snap'] + softs(['f2','f3','f4','f5','f1'])
L += ['press main','wait 1','snap','exit']
print('\n'.join(L))
