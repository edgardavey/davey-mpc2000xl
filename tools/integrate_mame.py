#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""Integrate the MPC2000XL driver into a dedicated pinned MAME source tree."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'vendor/mame')
    args = parser.parse_args()
    source = args.source.resolve()
    lock = json.loads((ROOT / 'mame.lock.json').read_text())
    reference = source / 'src/mame/akai/mpc2000.cpp'
    if hashlib.sha256(reference.read_bytes()).hexdigest() != lock['reference_driver_sha256']:
        raise ValueError('Unexpected upstream driver; use the pinned MAME source')
    subprocess.run([sys.executable, str(ROOT / 'tools/patch_mame_keyboard.py'), '--source', str(source)], check=True)
    shutil.copyfile(ROOT / 'src/mpc2000xldiag.cpp', source / 'src/mame/akai/mpc2000xldiag.cpp')
    listing = source / 'src/mame/mame.lst'
    text = listing.read_text()
    entry = '@source:akai/mpc2000xldiag.cpp\nmpc2000xldiag\n'
    if entry not in text:
        if 'mpc2000xldiag' in text:
            raise ValueError('Unexpected existing MPC2000XL registration')
        listing.write_text(text.rstrip() + '\n\n' + entry)
    print('MPC2000XL driver and SDL keyboard patch integrated')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
