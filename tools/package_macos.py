#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""Wrap the local XL binary in a macOS application identity (no installer)."""
from pathlib import Path
import plistlib
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    binary = ROOT / 'build/bin/mpc2000xldiag'
    if not binary.is_file():
        raise SystemExit('Build the MPC2000XL executable first.')
    contents = ROOT / 'build/MPC2000XL.app/Contents'
    executable = contents / 'MacOS/mpc2000xldiag'
    executable.parent.mkdir(parents=True, exist_ok=True)
    staged = executable.with_name(executable.name + ".new")
    shutil.copy2(binary, staged)
    staged.replace(executable)
    info = {'CFBundleDisplayName': 'MPC2000XL', 'CFBundleName': 'MPC2000XL',
            'CFBundleExecutable': 'mpc2000xldiag',
            'CFBundleIdentifier': 'com.vubeatz.mpc2000xl.prototype',
            'CFBundlePackageType': 'APPL', 'CFBundleVersion': '1',
            'NSHighResolutionCapable': True}
    with (contents / 'Info.plist').open('wb') as output:
        plistlib.dump(info, output)
    print('Local app identity: ' + str(contents.parent))
    print('Start with Launch Emulator.command or run.py to stage your ROM/session.')


if __name__ == '__main__':
    main()
