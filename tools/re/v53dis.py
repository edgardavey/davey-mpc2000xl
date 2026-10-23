#!/usr/bin/env python3
"""dis.py BIN SEG OFF [N]: disassemble N instructions (16-bit, V53) at SEG:OFF of an MPC2000XL OS image."""
import sys, capstone
d = open(sys.argv[1], 'rb').read()
seg, off = int(sys.argv[2], 16), int(sys.argv[3], 16); n = int(sys.argv[4]) if len(sys.argv) > 4 else 40
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16); md.skipdata = True
L = seg * 16
for k, i in enumerate(md.disasm(d[L + off:L + off + 0x1000], off)):
    if k >= n: break
    print(f"{i.address:04x}: {i.bytes.hex():16s} {i.mnemonic} {i.op_str}")
