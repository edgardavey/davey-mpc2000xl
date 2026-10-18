"""Shared script fragments for emulator tests (commands for tools/dev/drive.lua)."""
SH = ['down shift','up shift','wait 0.3']          # toggles the SHIFT latch (call twice around a key)
def shift_key(k): return SH + [f'press {k}', 'wait 0.3'] + SH
VOICES = 'lua local sp=manager.machine.devices[":maincpu"].spaces["program"] local t={} for i=0,31 do t[#t+1]=sp:read_u8(0x65aae+i) end print("VOICE %s "..table.concat(t," "))'
def voices(tag): return [VOICES % tag]
def load_sound_and_regions(n_regions_presses=3):
    """boot, load first file on disk into the program, REGIONS on pad 1, one whole-sample region, back to main."""
    L = ['wait 30'] + shift_key('n3') + ['wait 2','press f6','wait 3','press n3','press n5','press enter','wait 6','press f5','wait 3',
         'press main','wait 1','press pad1','press levels','wait 1','press down','press plus','press plus','press f2','wait 2']
    L += ['press f3'] * n_regions_presses + ['wait 1','press f5','wait 1.5','press f6','wait 2','snap','press main','wait 1']
    return L
