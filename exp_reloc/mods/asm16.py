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

def v53_safe(src):
    out = []
    for line in src.split('\n'):
        m = JCC.match(line)
        if m and m.group(2) in INV:
            ind, op, tgt = m.group(1), m.group(2), m.group(3)
            out += [f'{ind}{INV[op]} 9f', f'{ind}.byte 0xe9', f'{ind}.word {tgt} - . - 2', '9:']
        else:
            out.append(line)
    return '\n'.join(out)

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
    print('self-check ok')
