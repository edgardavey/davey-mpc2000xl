#!/usr/bin/env python3
"""Emit harness commands for one recording pass. usage: beat.py {rec|overdub} pad step,step,..
Holds REC/OVERDUB while PLAY START is pressed, lets the 4-bar loop wrap once, and records the hits in loop 2."""
import sys
mode, pad, steps = sys.argv[1], int(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')]
STEP = 60 / 90 / 4          # one 1/16 at 90 bpm
print(f'down {mode}'); print('tap playstart 0.3'); print(f'up {mode}')
t = 0.7                     # script clock relative to sequencer start (down +0.2, tap +0.3, up +0.4 = 0.9; start at 0.2)
for s in sorted(steps):
    at = (64 + s) * STEP + (0.07 if s == 0 else 0.04)   # +0.04 lands on the grid; the loop-start hit must fall after the wrap
    print(f'wait {at - t:.3f}'); print(f'tap pad{pad} 0'); t = at
print(f'wait {128 * STEP - 0.1 - t:.3f}'); print('press stop'); print('wait 1.5'); print('snap')
