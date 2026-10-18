#!/usr/bin/env python3
"""view.py SESSION_DIR [N]: stack the last N snapshots (3x) into SESSION_DIR/m3.png"""
import os, sys
from PIL import Image
S = os.path.join(sys.argv[1], 'snap', 'mpc2000xldiag'); n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
fs = sorted(os.listdir(S))[-n:]
ims = [Image.open(os.path.join(S, f)) for f in fs]
w = max(i.width for i in ims); h = sum(i.height for i in ims)
o = Image.new('RGB', (w, h)); y = 0
for i in ims: o.paste(i, (0, y)); y += i.height
o.resize((w*3, h*3), Image.NEAREST).save(os.path.join(sys.argv[1], 'm3.png')); print(fs)
