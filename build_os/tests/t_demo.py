import sys, subprocess; sys.path.insert(0, 'build_os/tests')
from common import *
on=[0.025,0.100,0.334,0.394,0.668,1.162,1.467,1.646,1.811,1.956,2.125,2.180,2.255,2.454]
L=['wait 28']+shift_key('n3')+['wait 2','press f6','wait 3','press n3','press n5','press enter','wait 6','press f5','wait 3','press main','wait 1']
L+=shift_key('n5')+['wait 1.5','press f3','wait 1.5']+['press right']*4+['wait 1','press window','wait 1.5','press f6','wait 2']
L+=['tap pad1 0']; t=0
for k,c in enumerate(on[1:]):
    cut=c-0.01; L+=[f'wait {cut-t:.3f}',f'tap pad{k+2} 0']; t=cut
L+=['wait 0.5','snap','press f5','wait 2','press f5','wait 1.5','snap','press f5','wait 5','snap']   # DO IT (zones), EDIT, SLICE SOUND DO IT
L+=['press main','wait 1.5','press down','press n9','press n0','press n0','press enter','press down','press minus','press right','press right','press n4','press n4','press enter','wait 1','press f5','wait 2','snap']
def beat(mode, pad, steps): return subprocess.run(['python3','tools/dev/beat.py',mode,str(pad),steps],capture_output=True,text=True).stdout.strip().split('\n')
L+=beat('rec',14,'0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,31,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,61,62,63')
L+=beat('overdub',10,'4,12,20,28,36,44,52,60')
L+=beat('overdub',8,'0,10,16,22,26,32,35,42,48,54,58,62')
L+=['wait 1','press playstart','wait 2','snap']
print('\n'.join(L))
