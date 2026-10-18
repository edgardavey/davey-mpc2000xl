#!/usr/bin/env python3
"""chunk.py 'python expression returning a list of command lines' [timeout_s]: append to the live session and wait until it has run."""
import sys, time, os, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import phases, harness, seqgen
S = open('/tmp/S.txt').read().strip()
expr = sys.argv[1]; to = int(sys.argv[2]) if len(sys.argv) > 2 else 900
lines = eval(expr, {**vars(phases), **vars(seqgen)})
tag = 'CHUNK' + uuid.uuid4().hex[:6]
lines = list(lines) + [f'lua print("{tag}")']
with open(S + '/cmd.txt', 'a') as f: f.write('\n'.join(lines) + '\n')
open(os.path.join(harness.ROOT, 'test_log', 'layered_master.txt'), 'a').write('\n'.join(lines[:-1]) + '\n')
t0 = time.time()
while time.time() - t0 < to:
    if tag in open(S + '/out.log', errors='replace').read(): print('done in', int(time.time() - t0), 's'); break
    time.sleep(3)
else: print('TIMEOUT')
