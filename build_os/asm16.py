"""Kept for old imports: the one assembler is exp_reloc/mods/asm16.py (NEC V53-safe jumps + 386-opcode check).
A second copy here once got cached by Python first and built V53-unsafe chop code into the patcher (caught 2026-10-17)."""
import importlib.util, os
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exp_reloc', 'mods', 'asm16.py')
_s = importlib.util.spec_from_file_location('_asm16_v53', _p); _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
assemble, v53_safe, check_v53 = _m.assemble, _m.v53_safe, _m.check_v53
