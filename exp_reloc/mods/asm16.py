#!/usr/bin/env python3
"""Assemble a 16-bit intel-syntax .S with clang for the MPC2000XL's NEC V53 (80186-class) and return the raw .text bytes.

The V53 has no 386 instructions. clang's 16-bit mode is a 386 assembler and silently turns a conditional jump whose target
is more than 127 bytes away into the 386-only form 0F 8x rel16, which the V53 executes as garbage (measured 2026-10-16:
it crashed the chop screen). So:
  1. v53_safe() rewrites every conditional jump to a label into   j<inverse> 9f / near jmp target / 9:
     (both pieces exist on the 8086), whatever the distance;
  2. after assembling, the object is disassembled and the build FAILS on any 0F-prefixed instruction or 66/67 size prefix.
No relocations are allowed (the code is position-fixed by its segment)."""
import re, subprocess, struct, sys, tempfile, os

INV = {'je': 'jne', 'jz': 'jnz', 'jne': 'je', 'jnz': 'jz', 'jb': 'jae', 'jnae': 'jae', 'jc': 'jnc', 'jae': 'jb', 'jnb': 'jb', 'jnc': 'jc',
       'ja': 'jbe', 'jnbe': 'jbe', 'jbe': 'ja', 'jna': 'ja', 'jl': 'jge', 'jnge': 'jge', 'jge': 'jl', 'jnl': 'jl', 'jg': 'jle', 'jnle': 'jle',
       'jle': 'jg', 'jng': 'jg', 'js': 'jns', 'jns': 'js', 'jo': 'jno', 'jno': 'jo', 'jp': 'jnp', 'jpe': 'jnp', 'jnp': 'jp', 'jpo': 'jp'}
JCC = re.compile(r'^(\s*)(j[a-z]+)\s+([.A-Za-z_][\w.]*)\s*(/\*.*\*/)?\s*$')

RET = re.compile(r'^(\s*)(retf|ret)\s*(/\*.*\*/)?\s*$')

def v53_safe(src):
    out = []
    for line in src.split('\n'):
        r = RET.match(line)
        if r:                                  # clang's 16-bit 'ret' can come out as 66 C3 (386 size prefix): emit the plain byte
            out.append(f"{r.group(1)}.byte {'0xcb' if r.group(2) == 'retf' else '0xc3'}")
            continue
        m = JCC.match(line)
        if m and m.group(2) in INV:
            ind, op, tgt = m.group(1), m.group(2), m.group(3)
            out += [f'{ind}{INV[op]} 9f', f'{ind}.byte 0xe9', f'{ind}.word {tgt} - . - 2', '9:']
        else:
            out.append(line)
    return '\n'.join(out)

DATA = re.compile(r'^(\s*(?:[.\w]+:\s*)?)\.(ascii|asciz|byte|word|long|fill)\b\s*(.*?)\s*(/\*.*\*/)?\s*$')

def _data_size(kind, args):
    if kind in ('ascii', 'asciz'):
        n = len(bytes(args.strip()[1:-1], 'utf-8').decode('unicode_escape').encode('latin-1'))
        return n + (kind == 'asciz')
    if kind == 'fill':
        f = [x.strip() for x in args.split(',')]
        return int(f[0], 0) * (int(f[1], 0) if len(f) > 1 else 1)
    return len([x for x in args.split(',') if x.strip()]) * {'byte': 1, 'word': 2, 'long': 4}[kind]

def code_only(src):
    """same layout, every data directive replaced by NOPs (0x90, one byte each, so decoding never loses step after a
    gap): what remains decodes as real instructions only"""
    out = []
    for line in src.split('\n'):
        m = DATA.match(line)
        out.append(f'{m.group(1)}.fill {_data_size(m.group(2), m.group(3))}, 1, 0x90' if m else line)
    return '\n'.join(out)

def check_prefixes(src):
    """build fails on any 0F / 66 / 67 instruction outside data (V53 = 80186 class: no 386 prefixes or 0F opcodes)"""
    p = tempfile.mktemp(suffix='.S'); open(p, 'w').write(code_only(src))
    obj = tempfile.mktemp(suffix='.o')
    subprocess.run(['clang', '-c', '-target', 'i386-none-elf', '-m16', '-x', 'assembler', p, '-o', obj], check=True)
    dis = subprocess.run(['objdump', '-d', '-M', 'intel', '--triple=i386-unknown-unknown-code16', obj], capture_output=True, text=True).stdout
    os.remove(p); os.remove(obj)
    bad = [l.strip() for l in dis.split('\n') if re.search(r':\s+(0f|66|67) ', l)]
    if bad: raise SystemExit('386-only encodings in V53 code:\n  ' + '\n  '.join(bad))

def check_v53(obj):
    dis = subprocess.run(['objdump', '-d', '-M', 'intel', '--triple=i386-unknown-unknown-code16', obj], capture_output=True, text=True).stdout
    bad = [l.strip() for l in dis.split('\n') if re.search(r':\s+(0f [0-9a-f]{2}|66 |67 )', l)]
    # inline text after int 0x8f decodes as junk; only real instruction streams matter, so data lines are listed for review
    jumps = [l for l in bad if re.search(r':\s+0f 8[0-9a-f]', l)]
    if jumps: raise SystemExit('386-only conditional jumps in V53 code:\n  ' + '\n  '.join(jumps))
    return bad

def assemble(path):
    src = open(path).read(); safe = v53_safe(src)
    if safe != src: open(path, 'w').write(safe)
    obj = tempfile.mktemp(suffix='.o')
    subprocess.run(['clang', '-c', '-target', 'i386-none-elf', '-m16', '-x', 'assembler', path, '-o', obj], check=True)
    check_v53(obj)
    check_prefixes(safe)
    d = open(obj, 'rb').read(); os.remove(obj)
    assert d[:4] == b'\x7fELF' and d[4] == 1
    shoff, = struct.unpack_from('<I', d, 0x20); shentsize, shnum, shstrndx = struct.unpack_from('<HHH', d, 0x2e)
    secs = [struct.unpack_from('<IIIIIIIIII', d, shoff + i * shentsize) for i in range(shnum)]
    strtab = secs[shstrndx]
    name = lambda n: d[strtab[4] + n:d.index(b'\0', strtab[4] + n)].decode()
    out = None
    for s in secs:
        if name(s[0]) == '.text': out = d[s[4]:s[4] + s[5]]
        if name(s[0]).startswith('.rel'):
            if s[5]: raise SystemExit('relocations present: ' + name(s[0]))
    return out

if __name__ == '__main__':
    assert v53_safe('    jne .Lx\n') == '    je 9f\n    .byte 0xe9\n    .word .Lx - . - 2\n9:\n'
    assert v53_safe('    jmp .Lx') == '    jmp .Lx' and v53_safe('    loop .Lx') == '    loop .Lx'
    assert v53_safe('    ret') == '    .byte 0xc3' and v53_safe('    retf  /* x */') == '    .byte 0xcb'
    assert code_only('a: .asciz "ab"\n .byte 1, 2, 3\n .word 5\n .fill 4, 1, 0') == 'a: .fill 3, 1, 0x90\n .fill 3, 1, 0x90\n .fill 2, 1, 0x90\n .fill 4, 1, 0x90'
    print('self-check ok')
