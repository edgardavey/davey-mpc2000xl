import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

def smoke():
    L = boot() + ['snap'] + shift_key('n8') + ['wait 2', 'snap', 'press f3', 'wait 2', 'snap', 'exit']
    return {'lines': L, 'cap': 90}

# ---------------------------------------------------------------------------------------------------------
# Layered scenario: zone lazy chop (REMEDY style) and REGIONS lazy chop (vubeatz style), FUNKY (beat) + NEPAL (music)
from seqgen import *
FUNKY_ON = [0.025,0.100,0.334,0.394,0.668,1.162,1.467,1.646,1.811,1.956,2.125,2.180,2.255,2.454]
NEPAL_CUTS = [0.78,1.51,2.15,2.78,3.32,3.93,4.37,4.98,5.45,5.91,6.33,6.9,7.45]
FUNKY_CUTS = [c for c in FUNKY_ON[1:]]
def taps(cuts):
    L = ['tap pad1 0']; t = 0
    for k, c in enumerate(cuts):
        cut = c - 0.01; L += [f'wait {cut - t:.3f}', f'tap pad{k + 2} 0']; t = cut
    return L
NOTES_DUMP = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local h={} for r=0,700 do local a=0x102800+r*8 local n=sp:read_u8(a+4) '
              'if n>=35 and n<=98 and sp:read_u8(a+6)==0x7f then h[n]=(h[n] or 0)+1 end end local t={} for n=35,98 do if h[n] then t[#t+1]=n..":"..h[n] end end print("NOTES %s "..table.concat(t," "))')
REGION_DUMP = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local h={} for a=0x100000,0x110000,2 do if sp:read_u8(a+4)==0x23 and sp:read_u8(a+5)==1 and sp:read_u8(a+6)==0xff and sp:read_u8(a+7)>=0xf0 then local k=sp:read_u8(a+7)-0xf0+1 h[k]=(h[k] or 0)+1 end end local t={} for k=1,16 do if h[k] then t[#t+1]="r"..k..":"..h[k] end end print("REGIONS %s "..table.concat(t," "))')
def to_sq(): return ['press main', 'wait 1.2'] + ['press up', 'wait 0.25'] * 8 + ['press left', 'wait 0.4']                       # cursor back on the Sq field
def to_sfield(): return to_sq() + ['press down', 'wait 0.3'] * 4                                     # Sq > tempo > Count > Tr > S:
def chunk_load():
    return boot() + shift_key('n3') + ['wait 2', 'press f6', 'wait 3', 'press n3', 'press n5', 'press enter', 'wait 6', 'press f5', 'wait 3',
        'press plus', 'wait 1', 'press f6', 'wait 3', 'press n3', 'press n6', 'press enter', 'wait 16', 'press f5', 'wait 3', 'snap', 'press main', 'wait 1']
def chunk_zone(name, cuts, select_funky=False):
    L = shift_key('n5') + ['wait 1.5']
    if select_funky: L += ['press f3', 'wait 1.5', 'press up', 'wait 0.6', 'press left', 'wait 0.6', 'press minus', 'wait 1.5', 'snap']      # Snd NEPAL -> FUNKY
    else: L += ['press f3', 'wait 1.5']
    L += ['press right'] * 4 + ['wait 1', 'press window', 'wait 1.5', 'press f6', 'wait 2'] + taps(cuts)
    L += ['wait 0.8', 'snap', 'press f5', 'wait 2', 'press f5', 'wait 1.5', 'snap', 'press f5', 'wait 9', 'snap']
    return L
def chunk_pgm_assign():
    """Edit DRUM 3's program (program 1) so pad A01 = note 35 (FUNKY) for the REGIONS approach, then DRUM 2 -> program 2 (NEPAL slices).
    DRUM 1 keeps program 3 (FUNKY slices): the ASSIGN page edits the program of the drum chosen on the first Program screen."""
    L = shift_key('n6') + ['wait 1.5', 'press f3', 'wait 2', 'snap']                                                          # DRUM 3
    L += ['press down', 'wait 0.5', 'press right', 'wait 0.5', 'press minus', 'wait 0.5', 'press minus', 'wait 0.8', 'snap']     # pad A01 -> note 35
    L += ['press f3', 'wait 1.5', 'press up', 'wait 0.5', 'snap']                                                              # DRUM tab
    L += ['press minus', 'wait 0.8', 'snap', 'press down', 'wait 0.8', 'press plus', 'wait 1', 'snap']                           # Drum 2 -> program 2
    return L
def chunk_seq_setup():
    return to_sq() + ['press down', 'wait 0.4'] + typ('900') + ['press down', 'press minus', 'press right', 'press right', 'press n4', 'press n4', 'press enter', 'wait 1', 'press f5', 'wait 2', 'snap']
def chunk_track(n, drum):
    """select track n (plus on the Tr: field) and set that track's drum (plus on the S: field)"""
    L = to_sq() + ['press down', 'wait 0.3'] * 3 + ['press plus', 'wait 0.8'] * (n - 1) + ['snap', 'press down', 'wait 0.4']
    L += ['press plus', 'wait 0.7'] * (drum - 1) + ['snap']
    return L

def chunk_regions(cuts, pad):
    """vubeatz style: 16 LEVELS = REGIONS for the pressed pad's note, REGION EDIT > LAZY, tap the cuts, APPLY, DONE"""
    L = ['press main', 'wait 1', f'tap pad{pad} 0', 'wait 0.8', 'press levels', 'wait 1.2', 'snap', 'press down', 'press plus', 'press plus', 'wait 0.5', 'snap',
         'press f2', 'wait 2', 'press f3', 'press f3', 'press f3', 'wait 1', 'snap'] + taps(cuts)
    L += ['wait 1.2', 'snap', 'press f5', 'wait 1.5', 'press f6', 'wait 2', 'snap', 'press main', 'wait 1']
    return L

def chunk_track_rel(delta, drum):
    """move the Tr: field by delta tracks (plus/minus), then set that track's drum with plus from DRUM1"""
    L = to_sq() + ['press down', 'wait 0.3'] * 3 + [('press plus' if delta > 0 else 'press minus'), 'wait 0.8'] * abs(delta) + ['snap', 'press down', 'wait 0.4']
    L += ['press plus', 'wait 0.7'] * (drum - 1) + ['snap']
    return L

REGION_DUMP36 = REGION_DUMP.replace('==0x23', '==0x24')

VOICES_PN = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for v=0,31 do local b=0x582b0+0x9609+v*20 local n=sp:read_u8(b+1) '
             'if n~=255 and n~=204 then t[#t+1]=sp:read_u8(b)..":"..n end end print("PLAYING %s "..table.concat(t," "))')
def chunk_play_all(n_samples=24, gap=1.1):
    L = ['press main', 'wait 1', 'press playstart', 'wait 0.5', 'snap']
    for i in range(n_samples): L += [f'wait {gap}', VOICES_PN % f't{i}']
    L += ['snap']
    return L

# ---------------------------------------------------------------------------------------------------------
# Zone lazy chop function suite (FUNKY, 2.59 s) -- every button and edge case, with zone-table / state dumps
ZD = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local b=0x582b0 local t={} for i=0,17 do t[#t+1]=sp:read_u16(b+0x8e72+i*4)+65536*sp:read_u16(b+0x8e74+i*4) end '
      'print("ZONES %s n="..sp:read_u8(b+0xd7dc).." cur="..sp:read_u8(b+0xd7dd).." B="..table.concat(t," "))')
TS = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for i=0,15 do t[#t+1]=sp:read_u16(0x70176+i*2) end '
      'print("TAPS %s cnt="..sp:read_u8(0x70162).." open="..sp:read_u8(0x70160).." run="..sp:read_u8(0x70161).." req="..sp:read_u8(0x70163).." taps="..table.concat(t," "))')
def zone_page_to_zone_field():
    return shift_key('n5') + ['wait 1.5', 'press f3', 'wait 1.5', 'press up', 'wait 0.5', 'press left', 'wait 0.5'] + ['press right'] * 4 + ['wait 0.8']
def zone_open(): return zone_page_to_zone_field() + ['press window', 'wait 1.5', 'press f6', 'wait 2']
def zone_suite():
    L = boot() + load_first_file(35)
    # Z1 PLAY mode, 5 taps at 0.5 0.9 1.3 1.7 2.1 s; DO IT
    L += zone_open() + ['snap', 'down f6', 'wait 0.3'] + [x for k in range(5) for x in ([f'tap pad{k+2} 0'] + ['wait 0.4'])][:-1] + ['wait 0.3', 'up f6', 'wait 0.5', T(TS, 'Z1'), 'snap', 'press f5', 'wait 2', T(ZD, 'Z1'), 'snap']
    # Z2 pad-start mode (first tap = slice 1 at 0), taps +0.5 +0.9 ; DO IT
    L += zone_open() + ['tap pad1 0', 'wait 0.5', 'tap pad2 0', 'wait 0.4', 'tap pad3 0', 'wait 0.3', T(TS, 'Z2'), 'press f5', 'wait 2', T(ZD, 'Z2')]
    # Z3 UNDO removes the last tap and replays from the one before: taps 0.5 0.9 1.3, UNDO, then two taps
    L += zone_open() + ['down f6', 'wait 0.3', 'tap pad2 0', 'wait 0.4', 'tap pad3 0', 'wait 0.4', 'tap pad4 0', 'wait 0.2', 'up f6', 'wait 0.3', T(TS, 'Z3_before_undo'),
          'press f3', 'wait 0.3', T(TS, 'Z3_after_undo'), 'tap pad5 0', 'wait 0.4', 'tap pad6 0', 'wait 0.3', T(TS, 'Z3_final'), 'snap', 'press f5', 'wait 2', T(ZD, 'Z3')]
    # Z4 UNDO down to zero taps, then a new first tap defines slice 1
    L += zone_open() + ['tap pad1 0', 'wait 0.6', 'tap pad2 0', 'wait 0.4', 'press f3', 'wait 0.3', 'press f3', 'wait 0.3', T(TS, 'Z4_after_two_undos'), 'press f3', 'wait 0.3', T(TS, 'Z4_undo_on_empty'),
          'tap pad3 0', 'wait 0.4', T(TS, 'Z4_retap'), 'press f5', 'wait 2', T(ZD, 'Z4')]
    # Z5 16-tap limit: 20 taps 0.11 s apart (they run past the sample end too)
    L += zone_open() + ['down f6', 'wait 0.2'] + [x for k in range(20) for x in ([f'tap pad{(k % 15) + 1} 0'] + ['wait 0.11'])] + ['up f6', 'wait 0.4', T(TS, 'Z5'), 'press f5', 'wait 2', T(ZD, 'Z5')]
    # Z6 end-of-sample guard: taps after the 2.59 s sample are ignored
    L += zone_open() + ['down f6', 'wait 0.3', 'tap pad2 0', 'wait 2.6', 'tap pad3 0', 'wait 0.3', 'up f6', 'wait 0.4', T(TS, 'Z6'), 'press f5', 'wait 2', T(ZD, 'Z6')]
    # Z7 CLOSE (F4) keeps the previous zones
    L += zone_open() + ['down f6', 'wait 0.3', 'tap pad2 0', 'wait 0.4', 'tap pad3 0', 'wait 0.2', 'up f6', 'wait 0.3', 'press f4', 'wait 2', T(ZD, 'Z7_after_close'), 'snap']
    # Z8 DO IT with no taps = one zone covering the sample
    L += zone_open() + ['press f5', 'wait 2', T(ZD, 'Z8')]
    # Z9 abandon via MAIN with taps present, reopen: counter restarts and pads work normally again
    L += zone_open() + ['down f6', 'wait 0.3', 'tap pad2 0', 'wait 0.4', 'tap pad3 0', 'wait 0.2', 'up f6', 'wait 0.3', T(TS, 'Z9_before'), 'press main', 'wait 1.5', 'tap pad4 0', 'wait 1', T(TS, 'Z9_pad_after_main')]
    L += zone_open() + [T(TS, 'Z9_reopened'), 'press f4', 'wait 2']
    # Z10 stock window still works: Number of zones 4 + DO IT gives even zones
    L += zone_page_to_zone_field() + ['press window', 'wait 1.5'] + typ('4') + ['press f5', 'wait 2', T(ZD, 'Z10_even4'), 'snap']
    # Z11 PLAY pressed twice restarts the count; PLAY then pad tap
    L += zone_open() + ['press f6', 'wait 0.8', 'tap pad2 0', 'wait 0.4', 'tap pad3 0', 'wait 0.2', T(TS, 'Z11_before_replay'), 'press f6', 'wait 0.8', T(TS, 'Z11_after_replay'), 'press f4', 'wait 2']
    L += ['exit']
    return {'lines': L, 'cap': 900, 'floppy': 'floppy/funky.img'}

# ---------------------------------------------------------------------------------------------------------
# REGIONS lazy chop function suite (vubeatz). Run on both builds and compare screens (A/B), plus sanity reads.
def reg_open_editor(mode_presses=0):
    """pad 1 + LEVELS -> assign REGIONS -> EDIT"""
    return ['press main', 'wait 1', 'tap pad1 0', 'wait 0.8', 'press levels', 'wait 1.2', 'press down', 'press plus', 'press plus', 'wait 0.5', 'press f2', 'wait 2'] + ['press f3'] * mode_presses + (['wait 1'] if mode_presses else [])
def walk(n, tag=None):
    """step down through n regions, one snapshot each"""
    L = []
    for i in range(n): L += ['press down', 'wait 0.6', 'snap']
    return L
def regions_suite():
    L = boot() + load_first_file(35)
    # R1 default (16 even regions): look at region 1, walk to the end
    L += reg_open_editor() + ['snap'] + walk(15)
    # R2 F3 cycles the even-split mode: 16 -> 8 -> 4 -> LAZY (1 region)
    L += ['press f3', 'wait 1', 'snap', 'press f3', 'wait 1', 'snap', 'press f3', 'wait 1', 'snap']
    # R3 LAZY chop (14 taps), then walk all 14 regions
    L += ['wait 0.5'] + taps(FUNKY_CUTS) + ['wait 1.2', 'snap'] + walk(13)
    # R4 ZOOM toggles the view
    L += ['press f4', 'wait 1', 'snap', 'press f4', 'wait 1', 'snap']
    # R5 CLEAN returns to one region; BACK leaves without applying
    L += ['press f2', 'wait 1', 'snap', 'press f1', 'wait 2', 'snap']
    # R6 reopen: what survived BACK (expect the previous applied state = none yet)
    L += ['press levels', 'wait 1.2', 'snap', 'press f2', 'wait 2', 'snap']
    # R7 chop again, APPLY, DONE; reopen: the chop must be there
    L += ['press f3', 'press f3', 'press f3', 'wait 1'] + ['wait 0.5'] + taps(FUNKY_CUTS) + ['wait 1.2', 'press f5', 'wait 1.5', 'snap', 'press f6', 'wait 2', 'snap']
    L += ['press levels', 'wait 1.2', 'snap', 'press f2', 'wait 2', 'snap']
    # R8 edit St/End by wheel and by typing; boundary sharing between neighbours
    L += ['press right', 'wait 0.5', 'press plus', 'wait 0.6', 'press plus', 'wait 0.6', 'snap', 'press down', 'wait 0.6', 'snap', 'press left', 'wait 0.5'] + typ('5000') + ['snap', 'press up', 'wait 0.6', 'snap']
    # R9 UNDO key inside the editor and after leaving it
    L += ['press undo', 'wait 1', 'snap', 'press f6', 'wait 2', 'press undo', 'wait 1', 'snap']
    # R10 16 LEVELS on: pads map to regions; record 6 hits and count the region events
    L += ['press levels', 'wait 1.2', 'press f6', 'wait 1.2', 'snap', 'press main', 'wait 1']
    L += [x for x in ('press n4', 'press enter') if False]
    L += ['down rec', 'tap playstart 0.3', 'up rec', 'wait 0.5'] + [x for k in (1, 3, 5, 7, 9, 11) for x in (f'tap pad{k} 0', 'wait 0.45')] + ['press stop', 'wait 1.5', REGION_DUMP % 'R10', 'snap']
    L += ['exit']
    return {'lines': L, 'cap': 700, 'floppy': 'floppy/funky.img', 'compare_prefixes': ['REGIONS R10']}

# ---------------------------------------------------------------------------------------------------------
# Standard-feature suites (compared stable vs davey)
def T(tpl, tag): return tpl.replace('%s', tag)
EVT = ('lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for r=0,95 do local a=0x102800+r*8 local b={} for k=0,7 do b[#b+1]=string.format("%02x",sp:read_u8(a+k)) end '
       'if sp:read_u8(a+4)==0 and sp:read_u8(a+5)==0 and sp:read_u8(a+6)==0 then break end t[#t+1]=table.concat(b,"") end print("EVT %s n="..#t.." "..table.concat(t," "))')
def sweep_fields(downs, rights, plusminus=True, wait=0.45):
    """walk the cursor with down then right, nudging each field up and back; one snapshot per field"""
    L = []
    for key, n in (('down', downs), ('right', rights)):
        for i in range(n):
            L += [f'press {key}', f'wait {wait}']
            if plusminus: L += ['press plus', f'wait {wait}', 'snap', 'press minus', f'wait {wait}']
            else: L += ['snap']
    return L
def hits_pass(mode, hits, tempo=100, bars=2, first_wait=0.5):
    """generic record pass for tempo/bars: hits=[(beat16th, pad)]; count-in must be OFF"""
    step = 60 / tempo / 4
    L = [f'down {mode}', 'tap playstart 0.3', f'up {mode}']
    t = 0.7
    for s, pad in sorted(hits):
        at = (bars * 16 + s) * step + (0.07 if s == 0 else 0.04)
        L += [f'wait {at - t:.3f}', f'tap pad{pad} 0']; t = at
    L += [f'wait {bars * 16 * 2 * step - 0.1 - t:.3f}', 'press stop', 'wait 1.5']
    return L
def seq_setup(tempo='1000', bars='2'):
    return to_sq() + ['press down', 'wait 0.4'] + typ(tempo) + ['press down', 'press minus', 'press right', 'press right'] + typ(bars) + ['wait 1', 'press f5', 'wait 2']

def seq_basic():
    L = boot() + load_first_file(37) + seq_setup('1000', '2') + ['snap']
    A = [(0, 1), (4, 1), (8, 1), (12, 1), (16, 1), (20, 1), (24, 1), (28, 1)]
    L += hits_pass('rec', A) + [T(EVT, 'rec'), 'snap']                                    # SB1 record
    L += hits_pass('overdub', [(2, 2), (10, 2), (18, 2), (26, 2)]) + [T(EVT, 'overdub')]   # SB2 overdub
    L += ['press undo', 'wait 1', T(EVT, 'undo'), 'press undo', 'wait 1', T(EVT, 'redo'), 'snap']   # SB3 undo / redo
    L += ['press barprev', 'wait 0.6', 'press barprev', 'wait 0.6', 'press playstart', 'wait 1.5', 'snap', 'wait 2', 'snap', 'press stop', 'wait 1.5', 'snap']   # SB4 playback + stop
    L += ['press f1', 'wait 2', 'snap'] + ['press down', 'wait 0.5', 'snap'] * 3 + ['press main', 'wait 1']                                        # SB5 step edit view
    L += ['press stepnext', 'wait 0.6', 'snap', 'press stepnext', 'wait 0.6', 'snap', 'press stepprev', 'wait 0.6', 'snap', 'press barnext', 'wait 0.6', 'snap', 'press barprev', 'wait 0.6']   # SB6 step/bar keys
    L += ['press erase', 'wait 1', 'snap', 'press erase', 'wait 0.6', T(EVT, 'erase_pressed'), 'snap']                                             # SB7 ERASE key (hold behaviour)
    L += ['exit']
    return {'lines': L, 'cap': 420, 'floppy': 'floppy/funky.img', 'compare_prefixes': ['EVT']}

def seq_edit():
    L = boot() + load_first_file(37) + seq_setup('1000', '2')
    L += hits_pass('rec', [(0, 1), (4, 1), (8, 1), (12, 1), (16, 1), (20, 1), (24, 1), (28, 1)]) + [T(EVT, 'base')]
    E = ['press main', 'wait 1', 'press f2', 'wait 1.5']
    L += E + ['snap', 'press f6', 'wait 2', T(EVT, 'copy_replace_default'), 'snap']                  # SE1 COPY (default), DO IT
    L += E + ['press plus', 'wait 0.8', 'snap', 'press f6', 'wait 2', T(EVT, 'after_edit2'), 'snap']  # SE2 next edit function
    for k in range(3): L += E + ['press plus', 'wait 0.7'] * (k + 2) + ['snap', 'press f6', 'wait 2', T(EVT, f'after_edit_p{k+3}'), 'snap']
    L += ['exit']
    return {'lines': L, 'cap': 520, 'floppy': 'floppy/funky.img', 'compare_prefixes': ['EVT']}

def zone_stock_persist():
    """Stock behaviour check (also runs on the stable build): are custom zone boundaries kept when the ZONE page is left and re-entered?"""
    L = boot() + load_first_file(35)
    L += zone_page_to_zone_field() + ['press window', 'wait 1.5'] + typ('4') + ['press f5', 'wait 2', T(ZD, 'after_4_zones')]
    L += ['press right', 'wait 0.3', 'press right', 'wait 0.3']
    # edit zone 1 End by hand (End field is left of Zone): then dump
    L += ['press left', 'wait 0.4', 'press plus', 'wait 0.5', 'press plus', 'wait 0.5', T(ZD, 'after_edit')]
    L += ['press main', 'wait 1.5'] + zone_page_to_zone_field() + [T(ZD, 'after_reenter'), 'exit']
    return {'lines': L, 'cap': 150, 'floppy': 'floppy/funky.img', 'compare_prefixes': ['ZONES']}

def tracks_song():
    L = boot() + load_first_file(37) + seq_setup('1000', '2')
    L += hits_pass('rec', [(0, 1), (8, 1), (16, 1), (24, 1)]) + [T(EVT, 'tr1')]
    # track navigation / on-off / mute / solo
    L += ['press main', 'wait 1', 'press f6', 'wait 0.8', 'snap', 'press f5', 'wait 0.8', 'snap']                      # Tr+ / Tr-
    L += ['press f3', 'wait 0.8', 'snap', 'press f3', 'wait 0.8', 'snap', 'press f4', 'wait 0.8', 'snap', 'press f4', 'wait 0.8', 'snap']   # TrMUTE on/off, SOLO on/off
    L += to_sq() + ['press down', 'wait 0.3'] * 3 + ['press right', 'wait 0.4', 'snap', 'press plus', 'wait 0.6', 'snap', 'press minus', 'wait 0.6', 'snap']   # track ON field
    # second track, record, then play both
    L += ['press main', 'wait 1', 'press f6', 'wait 0.8'] + hits_pass('overdub', [(4, 2), (12, 2), (20, 2), (28, 2)]) + [T(EVT, 'tr2')]
    L += ['press barprev', 'wait 0.6', 'press barprev', 'wait 0.6', 'press playstart', 'wait 1.5', 'snap', 'press f3', 'wait 1', 'snap', 'press f3', 'wait 0.6', 'press stop', 'wait 1.5']   # play with a track muted then unmuted
    # timing-correct and time signature fields
    L += to_sq() + ['press down', 'wait 0.3'] + ['press right', 'wait 0.4', 'press plus', 'wait 0.5', 'snap'] * 5 + ['press minus', 'wait 0.4'] * 5
    # next sequence: Sq +, set tempo there, back: sequence 1 must keep 100 bpm
    L += to_sq() + ['press plus', 'wait 1', 'snap', 'press down', 'wait 0.4'] + typ('1500') + ['snap', 'press up', 'wait 0.4', 'press minus', 'wait 1', 'snap']
    # song page
    L += shift_key('n1') + ['wait 1.5', 'snap', 'press f1', 'wait 1', 'snap', 'press f2', 'wait 1', 'snap', 'press f3', 'wait 1', 'snap', 'press f4', 'wait 1', 'snap', 'press main', 'wait 1']
    L += ['exit']
    return {'lines': L, 'cap': 520, 'floppy': 'floppy/funky.img', 'compare_prefixes': ['EVT']}

def disk_suite():
    L = boot() + load_first_file(37) + seq_setup('1000', '2') + hits_pass('rec', [(0, 1), (8, 1), (16, 1), (24, 1)])
    L += shift_key('n3') + ['wait 2', 'press f2', 'wait 1.5', 'press up', 'wait 0.5', 'snap']
    for i in range(6):                                           # every save type: DO IT, answer any prompt with DO IT again, look at the result
        L += ['press f6', 'wait 3', 'snap', 'press f6', 'wait 3', 'snap', 'press plus', 'wait 0.8']
    L += ['press f3', 'wait 1.5', 'snap']                       # FORMAT page
    L += ['press f1', 'wait 1.5', 'snap', 'press down', 'wait 0.5', 'snap']   # back to LOAD, file list
    L += ['exit']
    return {'lines': L, 'cap': 420, 'floppy': 'floppy/funky.img'}

def trim_suite():
    L = boot() + load_first_file(37) + shift_key('n5') + ['wait 1.5', 'snap']
    for f in ('f2', 'f3', 'f4'): L += [f'press {f}', 'wait 1.2', 'snap']
    L += ['press f1', 'wait 1.2', 'snap'] + sweep_fields(3, 4, True)                          # TRIM page fields
    L += ['press f2', 'wait 1.2'] + sweep_fields(3, 4, True)                                  # LOOP page fields
    L += ['press f3', 'wait 1.2'] + sweep_fields(2, 4, True)                                  # ZONE page fields
    L += ['press f5', 'wait 1.5', 'snap'] + ['press plus', 'wait 0.7', 'snap'] * 10 + ['press f4', 'wait 1', 'snap']   # EDIT menu functions (look only)
    L += ['exit']
    return {'lines': L, 'cap': 520, 'floppy': 'floppy/funky.img'}

def program_suite():
    L = boot() + load_first_file(37) + shift_key('n6') + ['wait 1.5', 'press f1', 'wait 2', 'snap']
    L += sweep_fields(4, 3, True)                                                              # ASSIGN: pgm, pad, note, transpose, mode
    L += ['press f2', 'wait 1.5', 'snap'] + sweep_fields(3, 6, True)                           # PARAMS
    L += ['press f3', 'wait 1.5', 'snap'] + sweep_fields(3, 2, True)                           # DRUM
    L += ['press f5', 'wait 1.5', 'snap', 'press f6', 'wait 1.2', 'snap']                      # AUTO, PLAY
    # modes through the whole range
    L += ['press f1', 'wait 1.5'] + ['press down', 'wait 0.4'] * 4 + ['snap'] + ['press plus', 'wait 0.6', 'snap'] * 12 + ['press minus', 'wait 0.5'] * 12
    L += ['exit']
    return {'lines': L, 'cap': 520, 'floppy': 'floppy/funky.img'}

def mixer_other():
    L = boot() + load_first_file(37)
    for key, nd, nr in (('n7', 4, 5), ('n8', 3, 3), ('n9', 4, 4), ('n2', 4, 4), ('n1', 3, 3), ('n4', 4, 5)):
        L += shift_key(key) + ['wait 1.5', 'snap'] + [x for f in ('f1', 'f2', 'f3', 'f4') for x in (f'press {f}', 'wait 1', 'snap', 'press main', 'wait 0.6') + tuple(shift_key(key))] 
        L += sweep_fields(nd, nr, True)
    L += ['exit']
    return {'lines': L, 'cap': 900, 'floppy': 'floppy/funky.img'}

def play_sample(tag, n=44, gap=0.115, bars_back=3):
    """rewind and play the sequence, sampling the sounding notes every `gap` seconds"""
    L = ['press main', 'wait 1'] + ['press barprev', 'wait 0.5'] * bars_back + ['press playstart', 'wait 0.1']
    for i in range(n): L += [f'wait {gap}', T(VOICES_PN, f'{tag}_{i}')]
    L += ['press stop', 'wait 1.5']
    return L
def pad2_gets_sound():
    return shift_key('n6') + ['wait 1.5', 'press f1', 'wait 2', 'tap pad2 0', 'wait 0.8', 'press down', 'wait 0.5', 'press down', 'wait 0.5', 'press right', 'wait 0.5', 'press plus', 'wait 0.8', 'snap', 'press main', 'wait 1']
def undo_check():
    L = boot() + load_first_file(37) + pad2_gets_sound() + seq_setup('1000', '2')
    L += hits_pass('rec', [(0, 1), (4, 1), (8, 1), (12, 1), (16, 1), (20, 1), (24, 1), (28, 1)])
    L += hits_pass('overdub', [(2, 2), (10, 2), (18, 2), (26, 2)])
    L += play_sample('before_undo')
    L += ['press undo', 'wait 1.2', 'snap'] + play_sample('after_undo')
    L += ['press undo', 'wait 1.2', 'snap'] + play_sample('after_redo')
    L += ['exit']
    return {'lines': L, 'cap': 520, 'floppy': 'floppy/funky.img'}

def reg_reopen():
    """from the main page: pad 1, LEVELS dialog (REGIONS already set), EDIT"""
    return ['press main', 'wait 1', 'tap pad1 0', 'wait 0.8', 'press levels', 'wait 1.2', 'press f2', 'wait 2']
def regions_suite2():
    L = boot() + load_first_file(35)
    L += reg_open_editor() + ['snap'] + walk(15)                                           # R1 16 even regions, walk to the end
    L += ['press f3', 'wait 1', 'snap', 'press f3', 'wait 1', 'snap', 'press f3', 'wait 1', 'snap']          # R2 16 -> 8 -> 4 -> LAZY
    L += ['wait 0.5'] + taps(FUNKY_CUTS) + ['wait 1.2', 'snap'] + ['press up', 'wait 0.6', 'snap'] * 13       # R3 lazy chop, walk back up through all 14 regions
    L += ['press f4', 'wait 1', 'snap', 'press f4', 'wait 1', 'snap']                       # R4 ZOOM on/off
    L += ['press f2', 'wait 1', 'snap']                                                     # R5 CLEAN -> 1 region
    L += ['press f1', 'wait 2', 'snap']                                                     # R6 BACK leaves the editor (nothing applied yet)
    L += reg_reopen() + ['snap']                                                            # R7 reopen: expect a fresh default (nothing was applied)
    L += ['press f3', 'press f3', 'press f3', 'wait 1', 'wait 0.5'] + taps(FUNKY_CUTS) + ['wait 1.2', 'press f5', 'wait 1.5', 'snap']   # R8 chop and APPLY, stay in editor
    L += ['press f2', 'wait 1', 'snap', 'press f1', 'wait 2']                               # R9 CLEAN then BACK: the applied chop must survive
    L += reg_reopen() + ['snap'] + ['press up', 'wait 0.6', 'press up', 'wait 0.6', 'snap']  # R10 reopen: still 14 regions
    L += ['press f6', 'wait 2', 'snap']                                                     # R11 DONE
    L += reg_reopen() + ['press right', 'wait 0.5', 'press plus', 'wait 0.6', 'press plus', 'wait 0.6', 'snap', 'press down', 'wait 0.6', 'snap',
          'press left', 'wait 0.5'] + typ('5000') + ['snap', 'press up', 'wait 0.6', 'snap']                                         # R12 wheel/typed edits, neighbours share boundaries
    L += ['press undo', 'wait 1, '.rstrip(', ')] if False else ['press undo', 'wait 1', 'snap']                                         # R13 UNDO key inside the editor
    L += ['press f1', 'wait 2', 'snap', 'press undo', 'wait 1', 'snap']                                                              # R14 UNDO key on the main page
    L += seq_setup('1000', '2') + reg_reopen() + ['press f6', 'wait 2']                                                             # R15 DONE, then record with 16 LEVELS on
    L += ['snap', 'press main', 'wait 1']                                                                                              # 16 LEVELS stays on after DONE
    L += hits_pass('rec', [(0, 1), (4, 3), (8, 5), (12, 7), (16, 9), (20, 11), (24, 13), (28, 14)]) + [T(REGION_DUMP, 'R15'), 'snap']
    L += ['exit']
    return {'lines': L, 'cap': 800, 'floppy': 'floppy/funky.img', 'compare_prefixes': ['REGIONS R15']}

def set_mode_for_pad(pad, g):
    """ASSIGN page: select the pad, put the cursor on Mode, set NORMAL then step up to MUTE g (g=0 leaves NORMAL)"""
    return [f'tap pad{pad} 0', 'wait 0.8'] + ['press up', 'wait 0.25'] * 6 + ['press down', 'wait 0.3'] * 4 + ['press minus', 'wait 0.25'] * 12 + (['press plus', 'wait 0.3'] * (3 + g) if g else []) + ['snap']
def mute_matrix(pairs=((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (1, 2), (5, 6), (7, 8), (4, 5), (8, 0), (0, 8), (0, 0))):
    """each pair (g1, g2): pad 1 and pad 2 modes; hit pad 1 then pad 2; the pad-1 voice must die only if g1==g2!=0"""
    L = boot() + load_first_file(37) + pad2_gets_sound() + shift_key('n6') + ['wait 1.5', 'press f1', 'wait 2']
    for g1, g2 in pairs:
        L += set_mode_for_pad(1, g1) + set_mode_for_pad(2, g2)
        L += ['press up', 'wait 0.3'] * 6                                           # keep the cursor away from numeric entry
        L += ['wait 3', 'tap pad1 0', 'wait 0.45', T(VOICES_PN, f'm{g1}{g2}_a'), 'tap pad2 0', 'wait 0.45', T(VOICES_PN, f'm{g1}{g2}_b'), 'wait 3.2']
    L += ['exit']
    return {'lines': L, 'cap': 900, 'floppy': 'floppy/funky.img'}


def tour():
    """screen tour of every mode page and soft key (same as tests/t_tour.py)"""
    def mode(k): return shift_key(k) + ['wait 1.5']
    def softs(keys, wait=1.2):
        out = []
        for f in keys: out += [f'press {f}', f'wait {wait}', 'snap']
        return out
    L = boot() + ['snap'] + shift_key('n3') + ['wait 2', 'snap', 'press f6', 'wait 3', 'snap', 'press n3', 'press n5', 'press enter', 'wait 6', 'snap', 'press f5', 'wait 3', 'snap', 'press main', 'wait 1', 'snap']
    L += softs(['f1', 'main', 'f2', 'main', 'f3', 'main', 'f4', 'main'])
    for n, sk in (('n1', ['f1','f2','f3','f4','f5','f6']), ('n2', ['f1','f2','f3','f4','f5','f6']), ('n3', ['f1','f2','f3','f4']), ('n4', ['f1','f2','f3','f4','f5','f6']),
                  ('n5', ['f1','f2','f3','f4','f5','f6']), ('n7', ['f1','f2','f3','f4']), ('n8', ['f1','f2','f3']), ('n9', ['f1','f2','f3','f4','f5','f6'])):
        L += mode(n) + ['snap'] + softs(sk) + ['press main', 'wait 1']
    L += mode('n6') + ['snap', 'press f1', 'wait 2', 'snap'] + softs(['f2','f3','f4','f5','f1']) + ['press main', 'wait 1', 'snap', 'exit']
    return {'lines': L, 'cap': 450, 'floppy': 'floppy/funky.img'}


def mute_controls():
    return mute_matrix(pairs=((8, 0), (0, 8), (0, 0), (1, 0), (0, 1)))


def _from_file(path, cap):
    L = [l for l in open(os.path.join(ROOT, path)).read().split('\n') if l]
    return {'lines': L, 'cap': cap, 'floppy': 'floppy/funky.img'}
def vub_feat1(): return _from_file('build_os/tests/t_vubeatz.txt', 600)     # TUNE +/-360, ALL bank/program
def vub_feat2(): return _from_file('build_os/tests/t_vubeatz2.txt', 450)    # Transpose +/-36, single vs double STOP


def copy_os():
    """SAVE page type 'Copy Operating System' -> the OS file on the floppy is compared with the loaded BIN on the host"""
    L = boot() + shift_key('n3') + ['wait 2', 'press f2', 'wait 1.5', 'press up', 'wait 0.5'] + ['press plus', 'wait 0.7'] * 5 + ['snap', 'press f6', 'wait 4', 'snap', 'press f6', 'wait 12', 'snap', 'wait 10', 'snap', 'exit']
    return {'lines': L, 'cap': 200, 'floppy': 'floppy/funky.img'}


def copy_os_after_use():
    """use the zone lazy chop (writes its variables into the OS image in memory), then Copy Operating System"""
    L = boot() + load_first_file(35) + zone_open() + ['down f6', 'wait 0.3', 'tap pad2 0', 'wait 0.4', 'tap pad3 0', 'wait 0.3', 'up f6', 'wait 0.5', 'press f5', 'wait 2']
    L += shift_key('n3') + ['wait 2', 'press f2', 'wait 1.5', 'press up', 'wait 0.5'] + ['press plus', 'wait 0.7'] * 5 + ['snap', 'press f6', 'wait 4', 'press f6', 'wait 12', 'snap', 'wait 10', 'snap', 'exit']
    return {'lines': L, 'cap': 260, 'floppy': 'floppy/funky.img'}
