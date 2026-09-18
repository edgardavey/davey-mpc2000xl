# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Vubeatz and contributors
"""Small SVG artwork writer. CoreText outlines keep labels identical in MAME.

NanoSVG (MAME's artwork reader) supports paths/gradients but not SVG text.
Only generation uses macOS CoreText; the resulting SVGs have no font dependency.
"""
import ctypes as C
from functools import lru_cache
from html import escape


class Point(C.Structure):
    _fields_ = [('x', C.c_double), ('y', C.c_double)]


class PathElement(C.Structure):
    _fields_ = [('kind', C.c_int), ('points', C.POINTER(Point))]


class Size(C.Structure):
    _fields_ = [('width', C.c_double), ('height', C.c_double)]


cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
ct = C.CDLL('/System/Library/Frameworks/CoreText.framework/CoreText')
cg = C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
cf.CFStringCreateWithCString.argtypes = [C.c_void_p, C.c_char_p, C.c_uint32]
cf.CFStringCreateWithCString.restype = C.c_void_p
cf.CFRelease.argtypes = [C.c_void_p]
ct.CTFontCreateWithName.argtypes = [C.c_void_p, C.c_double, C.c_void_p]
ct.CTFontCreateWithName.restype = C.c_void_p
ct.CTFontGetGlyphsForCharacters.argtypes = [C.c_void_p, C.POINTER(C.c_uint16), C.POINTER(C.c_uint16), C.c_long]
ct.CTFontGetGlyphsForCharacters.restype = C.c_bool
ct.CTFontGetAdvancesForGlyphs.argtypes = [C.c_void_p, C.c_uint32, C.POINTER(C.c_uint16), C.POINTER(Size), C.c_long]
ct.CTFontGetAdvancesForGlyphs.restype = C.c_double
ct.CTFontCreatePathForGlyph.argtypes = [C.c_void_p, C.c_uint16, C.c_void_p]
ct.CTFontCreatePathForGlyph.restype = C.c_void_p
PathCallback = C.CFUNCTYPE(None, C.c_void_p, C.POINTER(PathElement))
cg.CGPathApply.argtypes = [C.c_void_p, C.c_void_p, PathCallback]


@lru_cache(maxsize=24)
def font(name, size):
    string = cf.CFStringCreateWithCString(None, name.encode(), 0x08000100)
    result = ct.CTFontCreateWithName(string, size, None)
    cf.CFRelease(string)
    if not result:
        raise RuntimeError('CoreText could not open ' + name)
    return result


@lru_cache(maxsize=1024)
def glyph(name, size, char):
    face = font(name, size)
    source, result, advance = C.c_uint16(ord(char)), C.c_uint16(), Size()
    if not ct.CTFontGetGlyphsForCharacters(face, C.byref(source), C.byref(result), 1):
        raise ValueError(f'Missing artwork glyph {char!r} in {name}')
    ct.CTFontGetAdvancesForGlyphs(face, 0, C.byref(result), C.byref(advance), 1)
    path = ct.CTFontCreatePathForGlyph(face, result.value, None)
    parts = []

    @PathCallback
    def visit(_, pointer):
        item = pointer.contents
        op, count = [('M', 1), ('L', 1), ('Q', 2), ('C', 3), ('Z', 0)][item.kind]
        parts.append(op + ' '.join(f'{item.points[i].x:.3f},{item.points[i].y:.3f}' for i in range(count)))

    if path:
        cg.CGPathApply(path, None, visit)
        cf.CFRelease(path)
    return ''.join(parts), advance.width


class SVG:
    def __init__(self, width, height):
        self.width, self.height, self.parts = width, height, []
        self.add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    def add(self, source):
        self.parts.append(source)

    def gradient(self, name, stops, radial=False):
        kind = 'radialGradient' if radial else 'linearGradient'
        coords = 'cx="35%" cy="25%" r="80%"' if radial else 'x1="0%" y1="0%" x2="0%" y2="100%"'
        self.add(f'<defs><{kind} id="{name}" {coords}>')
        for i, colour in enumerate(stops):
            self.add(f'<stop offset="{i / (len(stops)-1):.3f}" stop-color="{colour}"/>')
        self.add(f'</{kind}></defs>')

    def rect(self, x, y, w, h, fill, radius=0, stroke=None, sw=1):
        line = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"{line}/>')

    def circle(self, x, y, r, fill, stroke=None, sw=1):
        line = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{line}/>')

    def path(self, path, fill='none', stroke=None, sw=1):
        line = f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"' if stroke else ''
        self.add(f'<path d="{path}" fill="{fill}"{line}/>')

    def text(self, label, x, y, size=10, colour='#333733', align='center', face='ArialMT', tracking=0.7, width=None, outline=False):
        shapes = [glyph(face, size, ch) for ch in label]
        length = sum(advance for _, advance in shapes) + max(0, len(shapes)-1) * tracking
        scale = min(1, width / length) if width and length else 1
        left = x - length*scale/2 if align == 'center' else x - length*scale if align == 'right' else x
        self.add(f'<!-- {escape(label)} -->')
        for path, advance in shapes:
            style = f'fill="none" stroke="{colour}" stroke-width="0.8"' if outline else f'fill="{colour}"'
            if path:
                self.add(f'<path d="{path}" transform="translate({left:.3f},{y}) scale({scale:.4f},-1)" {style}/>')
            left += (advance + tracking) * scale

    def save(self, path):
        path.write_text('\n'.join(self.parts + ['</svg>']) + '\n')
