#!/usr/bin/env python3
"""runphase.py PHASE [--only BUILD] [--builds A,B]: build the phase script, run it on two builds in parallel
(default stable,davey; 'stock' = original Akai 1.20), print health + comparison of A against B."""
import sys, threading, importlib, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
def main():
    phase = sys.argv[1]; only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    mod = importlib.import_module('phases'); importlib.reload(mod)
    spec = getattr(mod, phase)()
    lines, floppy, cap = spec['lines'], spec.get('floppy', 'floppy/funky.img'), spec.get('cap', 600)
    if only: builds = [only]
    elif '--builds' in sys.argv: builds = sys.argv[sys.argv.index('--builds') + 1].split(',')
    else: builds = ['stable', 'davey']
    tag = '' if builds in (['stable', 'davey'], [only]) else '_' + '_'.join(builds)
    res = {}
    def go(b): res[b] = H.run(phase + tag, lines, b, floppy, cap)
    ts = [threading.Thread(target=go, args=(b,)) for b in builds]
    [t.start() for t in ts]; [t.join() for t in ts]
    for b in builds:
        print(b, res[b]); print('  health:', H.health(res[b], lines))
    if len(builds) == 2:
        a, b2 = builds
        c = H.compare_snaps(res[a], res[b2]); print(f'compare snaps ({a} vs {b2}):', c)
        for pre in spec.get('compare_prefixes', []):
            la = H.grep_lines(res[a], pre); lb = H.grep_lines(res[b2], pre)
            print(f'  {pre}: {a} {len(la)} lines, {b2} {len(lb)} lines, identical={la == lb}')
            if la != lb:
                for x, y in zip(la, lb):
                    if x != y: print(f'    {a}:', x[:200]); print(f'    {b2}:', y[:200])
if __name__ == '__main__': main()
