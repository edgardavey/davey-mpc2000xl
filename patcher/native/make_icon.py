#!/usr/bin/env python3
"""Draws the DAVEY patcher app icon (MPC-style sampler seen from slightly above the front, like the reference icons)
and builds AppIcon.icns. Every element is extruded toward the viewer (visible front edge + cast shadow), the LCD is recessed.
A containment check fails the build if any element leaves the top face.
usage: make_icon.py   -> build/icon_1024.png, build/AppIcon.icns"""
import os, subprocess, shutil, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
S = 2048; k = S / 1024
def R(*v): return [int(round(x * k)) for x in v]
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def vgrad(w, h, top, bot):
    g = Image.new('RGB', (1, max(1, h)))
    for y in range(h): g.putpixel((0, y), lerp(top, bot, y / max(1, h - 1)))
    return g.resize((max(1, w), max(1, h)))
def rmask(w, h, r): m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m
def fill_grad(img, box, r, top, bot):
    x0, y0, x1, y1 = box; img.paste(vgrad(x1 - x0, y1 - y0, top, bot), (x0, y0), rmask(x1 - x0, y1 - y0, r))
def soft_shadow(img, box, r, dy, blur, a):
    m = Image.new('L', img.size, 0); x0, y0, x1, y1 = box
    ImageDraw.Draw(m).rounded_rectangle((x0, y0 + dy, x1, y1 + dy), r, fill=a)
    img.paste((0, 0, 0), (0, 0), m.filter(ImageFilter.GaussianBlur(blur)))

FACE = (100, 110, 924, 880); FR = 180                   # top face in 1024 units; the lip below it shows the depth
placed = []
def inside_face(box, margin=26):
    """every corner of box (with its depth) must sit inside the face, inset by margin, rounded corners included"""
    x0, y0, x1, y1 = box; fx0, fy0, fx1, fy1 = FACE[0] + margin, FACE[1] + margin, FACE[2] - margin, FACE[3] - margin; r = FR - margin
    for (x, y) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        if not (fx0 <= x <= fx1 and fy0 <= y <= fy1): return False
        cx = fx0 + r if x < fx0 + r else fx1 - r if x > fx1 - r else x
        cy = fy0 + r if y < fy0 + r else fy1 - r if y > fy1 - r else y
        if (x - cx) ** 2 + (y - cy) ** 2 > r * r: return False
    return True
def extrude(img, box1024, r, top, bot, side, depth, shadow=110, rim=None):
    """raised element: cast shadow, front edge (depth px), then the top face"""
    x0, y0, x1, y1 = box1024
    assert inside_face((x0, y0, x1, y1 + depth)), f'element {box1024} leaves the face'
    placed.append(box1024)
    b = R(x0, y0, x1, y1); dp = R(depth)[0]; rr = R(r)[0]
    soft_shadow(img, (b[0], b[1], b[2], b[3] + dp), rr, R(4)[0], R(5)[0], shadow)
    fill_grad(img, (b[0], b[1] + dp, b[2], b[3] + dp), rr, side, lerp(side, (0, 0, 0), .35))
    fill_grad(img, b, rr, top, bot)
    if rim: ImageDraw.Draw(img).rounded_rectangle((b[0] + 2, b[1] + 2, b[2] - 2, b[3] - 2), rr, outline=rim, width=R(2)[0])

# the top face is drawn FLAT (top-down) here; at the end it is warped through a perspective transform
img = Image.new('RGB', (S, S), (214, 212, 205)); face = R(*FACE)      # background = face colour: no dark seam after the warp
m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).rounded_rectangle(face, R(FR)[0], fill=255)      # face mask
FACEC = (214, 212, 205)
img.paste(FACEC, (0, 0), m)
d = ImageDraw.Draw(img)

# ---- LCD: raised dark bezel, recessed screen with inner shadow, hard-pixel text
extrude(img, (186, 196, 606, 414), 26, (66, 67, 64), (44, 45, 43), (30, 30, 29), 8, rim=(86, 87, 84))
scr = R(208, 218, 584, 392); fill_grad(img, scr, R(12)[0], (168, 186, 104), (186, 200, 120))
inner = Image.new('L', (scr[2] - scr[0], scr[3] - scr[1]), 0); ImageDraw.Draw(inner).rectangle((0, 0, scr[2] - scr[0], R(20)[0]), fill=150)
inner = inner.filter(ImageFilter.GaussianBlur(R(9)[0])); img.paste((24, 30, 12), (scr[0], scr[1]), ImageChops.multiply(inner, rmask(scr[2] - scr[0], scr[3] - scr[1], R(12)[0])))
lcd = Image.new('1', (96, 44), 0); ld = ImageDraw.Draw(lcd); ld.fontmode = '1'
try: fnt = ImageFont.load_default(size=11)
except TypeError: fnt = ImageFont.load_default()
ld.text((4, 2), 'DAVEY', fill=1, font=fnt); ld.text((62, 2), '>_', fill=1, font=fnt)
for x in range(4, 92):
    ph = (x - 4) % 22; amp = (10 if ph < 4 else 3) * math.exp(-ph / 7) * (0.7 + 0.3 * abs(math.sin(x)))
    ld.line((x, 31 - amp, x, 31 + amp), fill=1)
for zx in (26, 48, 70): ld.line((zx, 19, zx, 43), fill=1)
pad = R(14)[0]; lcd = lcd.convert('L').resize((scr[2] - scr[0] - 2 * pad, scr[3] - scr[1] - 2 * pad), Image.NEAREST)
img.paste((36, 44, 20), (scr[0] + pad, scr[1] + pad), lcd)
sheen = Image.new('L', (S, S), 0); sd = ImageDraw.Draw(sheen)                        # thin diagonal glass reflection
sd.polygon([(scr[0] + R(40)[0], scr[1]), (scr[0] + R(150)[0], scr[1]), (scr[0] + R(60)[0], scr[3]), (scr[0] - R(50)[0], scr[3])], fill=26)
img.paste((255, 255, 255), (0, 0), ImageChops.multiply(sheen, m.point(lambda v: v)).crop((0, 0, S, S)))

# ---- F-keys
for i in range(6):
    x0 = 196 + i * 70; extrude(img, (x0, 438, x0 + 56, 458), 6, (244, 243, 238), (214, 212, 206), (160, 158, 152), 6, shadow=90)

# ---- data wheel: cylinder (side visible), knurled rim, recessed dimple
cx, cy, rr, dep = 756, 300, 92, 16
assert inside_face((cx - rr, cy - rr, cx + rr, cy + rr + dep))
C = R(cx, cy, rr, dep); sh = Image.new('L', (S, S), 0)
ImageDraw.Draw(sh).ellipse((C[0] - C[2], C[1] - C[2] + C[3] + R(6)[0], C[0] + C[2], C[1] + C[2] + C[3] + R(6)[0]), fill=150)
img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(R(10)[0])))
for j in range(C[3], 0, -1):                                                         # side wall
    t = j / C[3]; ImageDraw.Draw(img).ellipse((C[0] - C[2], C[1] - C[2] + j, C[0] + C[2], C[1] + C[2] + j), fill=lerp((40, 41, 40), (18, 18, 18), t))
disc = Image.new('L', (S, S), 0); ImageDraw.Draw(disc).ellipse((C[0] - C[2], C[1] - C[2], C[0] + C[2], C[1] + C[2]), fill=255)
img.paste(vgrad(S, 2 * C[2], (96, 97, 95), (46, 47, 46)), (0, C[1] - C[2]), disc.crop((0, C[1] - C[2], S, C[1] + C[2])))
d = ImageDraw.Draw(img)
for j in range(40):
    t = j * math.pi / 20; d.line((C[0] + math.cos(t) * C[2] * .87, C[1] + math.sin(t) * C[2] * .87, C[0] + math.cos(t) * C[2] * .98, C[1] + math.sin(t) * C[2] * .98), fill=(72, 73, 71), width=R(2)[0])
dr = R(20)[0]; dx, dy = C[0] + int(C[2] * .45), C[1] - int(C[2] * .42)
d.ellipse((dx - dr, dy - dr, dx + dr, dy + dr), fill=(30, 31, 30)); d.ellipse((dx - dr + R(3)[0], dy - dr + R(5)[0], dx + dr - R(2)[0], dy + dr), fill=(60, 61, 59))

# ---- 16 pads, extruded, kept clear of the rounded corner
P, G, X0, Y0 = 70, 12, 514, 498
for r_ in range(4):
    for c in range(4):
        x0, y0 = X0 + c * (P + G), Y0 + r_ * (P + G)
        extrude(img, (x0, y0, x0 + P, y0 + P), 13, (92, 93, 92), (58, 59, 58), (30, 30, 30), 11, shadow=150, rim=(104, 105, 104))

# ---- transport buttons + REC LED
for i, col in enumerate([(214, 58, 50), (232, 230, 224), (232, 230, 224), (232, 230, 224)]):
    x0 = 196 + i * 72; top = tuple(min(255, v + 16) for v in col)
    extrude(img, (x0, 556, x0 + 58, 594), 8, top, col, lerp(col, (0, 0, 0), .35), 8, shadow=100)
led = R(212, 624, 228, 640); d.ellipse((led[0] - R(4)[0], led[1] - R(4)[0], led[2] + R(4)[0], led[3] + R(4)[0]), fill=(150, 34, 28)); d.ellipse(led, fill=(255, 76, 64))

# ---- floppy slot (recessed) + model text, both inside the face
assert inside_face((196, 690, 450, 744))
'''sl = R(196, 692, 450, 716); fill_grad(img, sl, R(6)[0], (22, 22, 22), (66, 66, 64))
d.rounded_rectangle(R(392, 698, 440, 708), R(2)[0], fill=(12, 12, 12))
'''
fnt2 = ImageFont.load_default(size=int(22 * k)) if True else None
lab = 'DAVEY MPC PATCHER'; tw = d.textlength(lab, font=fnt2) / k                    # label on top, centred over the LCD
assert inside_face((396 - tw / 2, 146, 396 + tw / 2, 172))
d.text(R(396 - tw / 2, 146), lab, fill=(124, 122, 116), font=fnt2)

# ---- forced perspective: far edge narrower, face foreshortened; squares become trapezoids, circles ellipses
def solve(A, bvec):
    n = len(bvec); M = [row[:] + [bvec[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]; M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]
def persp(dst, src):            # coefficients mapping output (dst) points to input (src) points, for Image.transform
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return solve(A, B)
fx0, fy0, fx1, fy1 = face; W = fx1 - fx0
# square body: rounded square silhouette; front wall = its lower band; top face = the rest (both straight-edged)
BX0, BY0, BX1, BY1 = R(96, 96, 928, 928); BR = R(184)[0]; LIPH = R(74)[0]
VF = (BX0, BY0, BX1, BY1 - LIPH)                                    # visible top face
TOP_IN = 0.0                                                        # flat contents (user preference); >0 = forced perspective
dst = [(VF[0] + W * TOP_IN, VF[1] + R(14)[0]), (VF[2] - W * TOP_IN, VF[1] + R(14)[0]), (VF[2], VF[3] - R(8)[0]), (VF[0], VF[3] - R(8)[0])]
co = persp(dst, [(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)])
wface = img.transform((S, S), Image.PERSPECTIVE, co, Image.BICUBIC)
wmask = m.transform((S, S), Image.PERSPECTIVE, co, Image.BICUBIC)
out = Image.new('RGB', (S, S), (0, 0, 0))
body = Image.new('L', (S, S), 0); ImageDraw.Draw(body).rounded_rectangle((BX0, BY0, BX1, BY1), BR, fill=255)
fmask = Image.new('L', (S, S), 0); ImageDraw.Draw(fmask).rounded_rectangle(VF, BR, fill=255)
sh = ImageChops.offset(body, 0, R(14)[0]).filter(ImageFilter.GaussianBlur(R(18)[0])).point(lambda v: int(v * .45))
alpha = ImageChops.lighter(sh, body)
out.paste(vgrad(S, BY1 - BY0, (158, 156, 150), (86, 84, 80)), (0, BY0), body.crop((0, BY0, S, BY1)))   # wall colour
out.paste(FACEC, (0, 0), fmask)                                     # top face base, same colour as the flat face
out.paste(wface, (0, 0), ImageChops.multiply(wmask, fmask))         # perspective contents
shade = vgrad(S, VF[3] - VF[1], (255, 255, 255), (0, 0, 0)).convert('L')    # light falls from the top: brighten top, darken front
lit = Image.new('L', (S, S), 0); lit.paste(shade.point(lambda v: int(v * .18)), (0, VF[1])); out.paste((255, 255, 255), (0, 0), ImageChops.multiply(lit, fmask))
dk = Image.new('L', (S, S), 0); dk.paste(shade.point(lambda v: int((255 - v) * .10)), (0, VF[1])); out.paste((0, 0, 0), (0, 0), ImageChops.multiply(dk, fmask))
ImageDraw.Draw(out).rounded_rectangle(VF, BR, outline=(244, 243, 238), width=R(4)[0])
# floppy slot on the front wall, bottom left (where the wall is straight)
dw = ImageDraw.Draw(out); wy0 = VF[3]; 
sx0, sx1 = R(228)[0], R(500)[0]; sy0, sy1 = wy0 + int(LIPH * .36), wy0 + int(LIPH * .64)
out.paste(vgrad(sx1 - sx0, sy1 - sy0, (18, 18, 18), (60, 60, 58)), (sx0, sy0), rmask(sx1 - sx0, sy1 - sy0, R(5)[0]))
dw.line((sx0 + R(6)[0], sy1 + R(2)[0], sx1 - R(6)[0], sy1 + R(2)[0]), fill=(180, 178, 172), width=R(2)[0])
ex0 = sx1 + R(18)[0]; dw.rounded_rectangle((ex0, sy0 + R(2)[0], ex0 + R(46)[0], sy1 - R(2)[0]), R(4)[0], fill=(124, 122, 116), outline=(72, 70, 66), width=R(2)[0])
img = out
final = img.convert('RGBA'); final.putalpha(alpha); final = final.resize((1024, 1024), Image.LANCZOS)
final.save(os.path.join(OUT, 'icon_1024.png'))
iset = os.path.join(OUT, 'AppIcon.iconset'); shutil.rmtree(iset, ignore_errors=True); os.makedirs(iset)
for s in (16, 32, 128, 256, 512):
    final.resize((s, s), Image.LANCZOS).save(f'{iset}/icon_{s}x{s}.png'); final.resize((s * 2, s * 2), Image.LANCZOS).save(f'{iset}/icon_{s}x{s}@2x.png')
subprocess.run(['iconutil', '-c', 'icns', iset, '-o', os.path.join(OUT, 'AppIcon.icns')], check=True)
print('wrote', os.path.join(OUT, 'AppIcon.icns'), 'elements placed:', len(placed))
