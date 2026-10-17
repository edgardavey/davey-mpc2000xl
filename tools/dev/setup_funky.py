#!/usr/bin/env python3
"""Commands: load FUNKY.WAV, REGIONS on pad 1, lazy-chop 14 transients, tempo 90, count off, 4 bars."""
on=[0.025,0.100,0.334,0.394,0.668,1.162,1.467,1.646,1.811,1.956,2.125,2.180,2.255,2.454]
L=['wait 28','down shift','up shift','wait 0.3','press n3','wait 0.3','down shift','up shift','wait 2','press f6','wait 3','press n3','press n5','press enter','wait 6',
   'press f5','wait 3','press main','wait 1','press pad1','press levels','wait 1','press down','press plus','press plus','press f2','wait 2','press f3','press f3','press f3','wait 1',
   'wait 0.5','tap pad1 0']
t=0
for k,c in enumerate(on[1:]):
    cut=c-0.01; L+=[f'wait {cut-t:.3f}',f'tap pad{k+2} 0']; t=cut
L+=['wait 1.2','press f5','wait 1.5','press f6','wait 2','snap',
    'press down','press n9','press n0','press n0','press enter','press down','press minus','press right','press right','press n4','press n4','press enter','wait 1','press f5','wait 2','snap']
print('\n'.join(L))
