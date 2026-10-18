"""Recording-pass generator for 90 bpm 4/4, 4-bar loop, 1/16 steps. hits = [(step, pad), ...]; steps 0..63."""
STEP = 60 / 90 / 4
def pass_lines(mode, hits, loops=2):
    """Hold REC/OVERDUB while pressing PLAY START, let the loop wrap once, play the hits in loop 2, stop."""
    L = [f'down {mode}', 'tap playstart 0.3', f'up {mode}']
    t = 0.7
    for s, pad in sorted(hits):
        at = (64 + s) * STEP + (0.07 if s == 0 else 0.04)
        L += [f'wait {at - t:.3f}', f'tap pad{pad} 0']; t = at
    L += [f'wait {128 * STEP - 0.1 - t:.3f}', 'press stop', 'wait 1.5', 'snap']
    return L
HATS = [0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,31,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,61,62,63]
SNARE = [4,12,20,28,36,44,52,60]
KICK = [0,10,16,22,26,32,35,42,48,54,58,62]
def beat_passes(first_mode='overdub', hat=14, snare=10, kick=8):
    return (pass_lines(first_mode, [(s, hat) for s in HATS]) + pass_lines('overdub', [(s, snare) for s in SNARE])
            + pass_lines('overdub', [(s, kick) for s in KICK]))
# NEPAL musical pattern: eighth-note chops (every 2nd step), cycling through slices in a melodic order
MUS_ORDER = [2, 5, 7, 9, 4, 11, 6, 13, 3, 8, 10, 12, 5, 7, 14, 9]
MUS = [(s, MUS_ORDER[(s // 4) % len(MUS_ORDER)]) for s in range(0, 64, 4)]
def music_pass(mode='overdub'): return pass_lines(mode, MUS)
EXPECT = {'hat': len(HATS), 'snare': len(SNARE), 'kick': len(KICK), 'music': len(MUS)}
