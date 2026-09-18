# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Vubeatz and contributors
"""MPC2000XL front-panel geometry.

The case and control groups use a 1280 x 980 canvas. Buttons and pads are
solid flat faces, as in the Classic emulator. The LCD is always guest pixels.
"""
import math
from panel_artwork import SVG

WIDTH, HEIGHT = 1280, 980
LCD = (214, 96, 310, 75)
FADER = (74, 658, 80, 170)
FADER_CAP = (84, 802, 60, 26)
FADER_VALUE = (94, 835, 40, 13)
LEDS = [('after',110,574), ('undo',222,656), ('rec',209,801),
        ('overdub',283,801), ('play',431,801),
        ('full',763,211), ('levels',843,211),
        ('nextseq',763,291), ('trackmute',843,291),
        ('banka',923,291), ('bankb',1003,291),
        ('bankc',1083,291), ('bankd',1163,291)]


def make_artwork(dest):
    dest.mkdir(parents=True, exist_ok=True)
    p = SVG(WIDTH, HEIGHT)
    ink, small = '#353b3f', '#52585d'
    p.rect(0, 0, WIDTH, HEIGHT, '#e4e6e5')
    p.gradient('case', ['#e3e4e1', '#d6d8d5', '#d9dad6'])
    p.gradient('lip', ['#babeb7', '#d8dad2', '#c4c8bd'])
    p.rect(29, 32, 1224, 926, '#9b9e99', 12)
    p.rect(24, 22, 1230, 895, 'url(#case)', 4, '#b9bcb7', 1)
    p.rect(25, 917, 1228, 40, 'url(#lip)', 9)
    p.path('M28 916 H1250', stroke='#7f857a', sw=1.5)
    p.path('M29 25 H1247', stroke='#f6f6f1', sw=2)
    p.path('M31 958 H1243', stroke='#aeb3a8')

    # XL's tilting display housing occupies the upper left, not the centre.
    p.rect(103, 43, 520, 193, '#242a30', 6, '#707579', 2)
    p.rect(142, 72, 443, 140, '#171d29', 2)
    p.path('M150 73 H579', stroke='#40454f', sw=3)
    p.path('M107 210 H618 M145 74 V229 M586 74 V229', stroke='#50555c', sw=1)
    p.rect(206, 89, 326, 89, '#080f14', 1)
    p.rect(*LCD, '#a9b7a0')
    p.text('INTEGRATED RHYTHM MACHINE  16 BIT DRUM SAMPLER / MIDI SEQUENCER',
           369, 87, 5.9, '#c3c5c8', tracking=0.28, width=330)
    for n in range(6):
        p.text(f'F{n+1}', 234+52*n, 194, 8, '#c7cbd0', tracking=0.5)

    # Model lettering uses vector outlines.
    p.add('<g transform="translate(902,69) scale(0.80)">')
    logo = '#555e63'
    p.path('M0 32 V0 H4 L20 20 L36 0 H40 V32', stroke=logo, sw=2.2)
    p.path('M54 32 V0 H79 Q86 0 86 7 V12 Q86 19 79 19 H54', stroke=logo, sw=2.2)
    p.path('M130 0 H104 Q97 0 97 8 V24 Q97 32 104 32 H130', stroke=logo, sw=2.2)
    p.path('M145 7 Q145 0 152 0 H171 Q178 0 178 7 V12 Q178 17 173 20 '
           'L151 28 Q145 30 145 32 H178', stroke=logo, sw=4.8)
    for x in (190, 230, 270):
        p.rect(x, 0, 28, 32, 'none', 3, logo, 4.8)
    p.path('M310 0 L340 32 M340 0 L310 32 M353 0 V32 H379', stroke=logo, sw=2.4)
    p.add('</g>')
    p.rect(902, 107, 304, 2, '#a52e36')
    p.text('MIDI PRODUCTION CENTER', 1054, 127, 13.4, ink, tracking=1.45, width=307)

    # Two distinct grey fields: control panel above, square pad bank below.
    p.rect(697, 163, 536, 174, '#a6adb2', 1)
    p.rect(697, 350, 536, 510, '#a6adb2', 1)
    p.rect(726, 187, 160, 58, '#e4e5dd')
    p.rect(726, 267, 160, 56, '#e4e5dd')

    def knob(cx, cy, label, red=False):
        p.text(label, cx, cy-43, 9.5, ink, tracking=0.8)
        p.circle(cx, cy, 30, '#dce0db', '#424b50', 1.5)
        p.circle(cx, cy, 24, '#b34c5c' if red else '#aaaead')
        angle = math.radians(-104 if red else 124)
        p.path(f'M{cx} {cy} L{cx+20*math.cos(angle):.2f} {cy+20*math.sin(angle):.2f}',
               stroke='#f5f4ee', sw=5)
        for angle in range(-225, 46, 45):
            a=math.radians(angle)
            p.circle(cx+35*math.cos(a), cy+35*math.sin(a), 0.8, '#50585d')
        p.text('MIN', cx-26, cy+39, 5.9, small, tracking=0.3)
        p.text('MAX', cx+26, cy+39, 5.9, small, tracking=0.3)
    knob(1009, 223, 'REC GAIN', True)
    knob(1129, 223, 'MAIN VOLUME')

    buttons=[]
    def key(name, port, mask, box, style='ivory', label=None, sub=None, label_y=None,
            output=None, label_size=9):
        buttons.append((name, port, mask, box, output, style))
        x,y,w,h=box
        if label:
            p.text(label, x+w/2, y-11 if label_y is None else label_y,
                   label_size, ink, tracking=0.65, width=max(w+28,60))
        if sub:
            p.text(sub, x+w/2, y+h+10, 6.4, small, tracking=0.25, width=w+28)

    for n in range(6):
        key(f'f{n+1}', 'KEYS', 1<<n, (216+52*n, 284, 36, 17), label=f'F{n+1}')
    key('main', 'KEYS', 0x100, (370,354,48,25), label='MAIN SCREEN')
    key('window', 'KEYS', 0x200, (491,354,48,25), 'yellow', 'OPEN WINDOW')

    # Blue digit keys and ivory Shift/Enter, in the XL's four-row numeric block.
    menus={1:'SONG',2:'MISC',3:'LOAD',4:'SAMPLE',5:'TRIM',6:'PROGRAM',7:'MIXER',8:'OTHER',9:'MIDI / SYNC'}
    for row,digits in enumerate(((7,8,9),(4,5,6),(1,2,3))):
        for col,n in enumerate(digits):
            key(f'num{n}','NUMBERS',1<<n,(96+75*col,359+46*row,36,17),
                'blue',str(n),menus[n], label_size=8)
    p.rect(86,484,56,38,'#adb2b4')
    key('shift','MODIFIERS',2,(96,497,36,17),'ivory','SHIFT',output='shift_active', label_y=491,label_size=8)
    key('num0','NUMBERS',1,(171,497,36,17),'blue','0',label_size=8)
    key('enter','KEYS',0x4000,(246,497,36,17),'ivory','ENTER',sub='EXECUTE',label_size=8)

    p.text('DATA',448,395,10.2,ink,tracking=1.1)
    p.circle(448,484,78,'#444950','#272e33',2)
    p.circle(448,484,49,'#41464d','#686e73',1.2)
    p.circle(439,527,14,'#343a41','#656c70',1)
    p.path('M430 419 L426 410 M449 417 V406 M468 419 L472 410',stroke='#81878b',sw=1)
    key('minus','KEYS',0x40,(370,406,78,156),'wheel_left')
    key('plus','KEYS',0x80,(448,406,78,156),'wheel_right')

    p.text('CURSOR',448,598,9.5,ink,tracking=0.9)
    key('left','KEYS',0x400,(394,610,27,78),'cursor_left')
    key('right','KEYS',0x800,(475,610,27,78),'cursor_right')
    key('up','KEYS',0x1000,(423,610,50,38),'cursor_up')
    key('down','KEYS',0x2000,(423,650,50,38),'cursor_down')
    p.text('DIGIT',448,702,6.5,small,tracking=0.55)

    p.path('M94 551 H60 V856 H167 V551 H135',stroke='#939b99',sw=1)
    p.text('NOTE',114,549,8.8,ink,tracking=0.8)
    p.text('VARIATION',114,560,8.8,ink,tracking=0.5)
    key('after','EXTRAS',1,(92,591,44,23),label='AFTER',label_y=572)
    key('tap','EXTRAS',2,(238,583,54,40),label='TAP TEMPO',label_y=564)
    p.text('NOTE REPEAT',265,575,8,ink,tracking=0.4)
    key('undo','EXTRAS',4,(204,674,44,23),label='UNDO SEQ',label_y=651)
    key('erase','EXTRAS',8,(278,674,44,23),label='ERASE',label_y=663)

    p.path('M204 723 H340 M404 723 H544',stroke='#8a918e',sw=0.8)
    p.text('LOCATE',374,725,7.2,small,tracking=0.65)
    p.text('STEP',263,739,8.5,ink,tracking=0.8)
    p.text('BAR',485,739,8.5,ink,tracking=0.8)
    for name,mask,x,label in [('stepprev',0x10,204,'<'),('stepnext',0x20,278,'>'),
                              ('goto',0x40,352,'GO TO'),('barprev',0x800,426,'<<'),('barnext',0x8000,500,'>>')]:
        key(name,'EXTRAS',mask,(x,746,44,23),label=label,label_y=739,label_size=8.2)
    # STEP and BAR captions sit between their arrows, not on a button label.
    for name,mask,x,label,style in [('rec',0x80,200,'REC','red'),('overdub',0x100,274,'OVER DUB','red'),
                                   ('stop',0x200,348,'STOP','ivory'),('play',0x400,422,'PLAY','ivory'),
                                   ('playstart',0x10000,496,'PLAY START','ivory')]:
        key(name,'EXTRAS',mask,(x,820,54,42),style,label,label_y=811,label_size=8.7)

    key('full','EXTRAS',0x2000,(744,224,46,23),label='FULL LEVEL',label_y=205,label_size=8.2)
    key('levels','EXTRAS',0x4000,(824,224,46,23),label='16 LEVELS',label_y=205,label_size=8.2)
    key('nextseq','EXTRAS',0x200000,(744,304,46,23),label='NEXT SEQ',label_y=286,label_size=8.2)
    key('trackmute','EXTRAS',0x100000,(824,304,46,23),label='TRACK MUTE',label_y=286,label_size=8.2)
    p.path('M901 279 H1007 M1054 279 H1210',stroke='#69737a',sw=0.7)
    p.text('PAD BANK',1030,281,7.2,small,tracking=0.5)
    for name,mask,x,label in [('banka',0x1000,904,'A'),('bankb',0x20000,984,'B'),
                             ('bankc',0x40000,1064,'C'),('bankd',0x80000,1144,'D')]:
        key(name,'EXTRAS',mask,(x,304,46,23),label=label,label_y=290,label_size=8.2)

    p.path('M735 365 H932 M996 365 H1195',stroke='#69737a',sw=0.8)
    p.text('DRUMS',964,368,9,ink,tracking=1.2)
    for row in range(4):
        for col in range(4):
            n=(3-row)*4+col+1
            x,y=742+117*col,391+116*row
            key(f'pad{n}','PADS',1<<(n-1),(x,y,99,99),'pad')
            p.text(f'PAD {n}',x+3,y-7,8,ink,align='left',tracking=0.6)

    for _, x, y in LEDS:
        p.circle(x+4,y+4,4.5,'#c2c7c5')
        p.circle(x+4,y+4,3,'#353e3f')
    p.text('M: MAIN  /  H: WINDOW  /  SHIFT + 1-9: MODES  /  - +: DATA  /  [ ]: FADER',
           640,974,8.3,'#65706b',tracking=0.4)
    p.save(dest/'panel.svg')

    # Same flat construction as Classic: solid faces, one outline, no bevels.
    styles={'ivory':(80,35),'blue':(60,28),'yellow':(80,35),'red':(65,46),'pad':(99,99),
            'cursor_left':(27,78),'cursor_right':(27,78),'cursor_up':(50,38),'cursor_down':(50,38)}
    colours={'ivory':('#eeeed6','#74796a'),'blue':('#335c79','#344c5d'),
             'yellow':('#dda835','#8c753f'),'red':('#b5686e','#825359')}
    for style,(w,h) in styles.items():
        for pressed in (0,1):
            s=SVG(w,h)
            if style=='pad':
                s.rect(1,1,w-2,h-2,'#a4aaa2' if pressed else '#888b8d',2,'#4d5559',1.4)
            else:
                fill,edge=colours.get(style,colours['ivory'])
                if pressed:fill,edge='#a3b397','#596e56'
                s.rect(1,1,w-2,h-2,fill,2,edge,1.2)
                if style.startswith('cursor_'):
                    arrow={'cursor_left':'M17 32 L10 39 L17 46',
                           'cursor_right':'M10 32 L17 39 L10 46',
                           'cursor_up':'M18 23 L25 16 L32 23',
                           'cursor_down':'M18 15 L25 22 L32 15'}[style]
                    s.path(arrow,stroke='#78806c',sw=1.5)
            s.save(dest/f'{style}-{pressed}.svg')
    for side in ('left','right'):
        for pressed in (0,1):
            s=SVG(78,156)
            s.rect(0,0,78,156,'none')
            if pressed:s.circle(12 if side=='left' else 66,78,3,'#d5dfd0')
            s.save(dest/f'wheel_{side}-{pressed}.svg')
    track=SVG(80,170)
    track.rect(0,0,80,170,'none')
    track.rect(35,0,10,170,'#9da49d',1)
    track.rect(37,1,6,168,'#242c2e',1)
    for n in range(13):
        y=3+n*13.6
        track.path(f'M8 {y} H29 M51 {y} H72',stroke='#8e9790',sw=0.9)
    track.save(dest/'fader-track.svg')
    cap=SVG(60,26)
    cap.rect(1,1,58,24,'#eeeedd',2,'#969f94',1.2)
    cap.rect(2,11,56,4,'#b5404a')
    cap.save(dest/'fader-cap.svg')
    return buttons
