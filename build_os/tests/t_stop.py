import sys; sys.path.insert(0, 'build_os/tests')
from common import *
L = load_sound_and_regions()
# idle STOP: sample rings, sequencer stopped
L += ['tap pad1 0','wait 2'] + voices('idle_before') + ['press stop','wait 1.5'] + voices('idle_after') + ['snap']
# STOP while the sequencer is playing
L += ['press playstart','wait 1.5','tap pad1 0','wait 2'] + voices('play_before') + ['press stop','wait 1.5'] + voices('play_after') + ['snap','exit']
print('\n'.join(L))
