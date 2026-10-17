#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""Start MPC2000XL with your own stock MPC2KXL.BIN. No firmware is included."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from tools.firmware import validate, stage
from tools.launcher import (choose_file, read_config, existing_path, system_files,
                            require_files, resolve_binary, remember, execute)

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'config.local.json'
TARGET = 'mpc2000xldiag'
VIEW = 'MPC2000XL panel'


def launch_command(binary, session, rom, disk=None, debug=False):
    command = [str(binary), TARGET, '-noreadconfig', '-noplugins', '-noautosave', '-quik', str(rom)]
    if disk is not None:
        command += ['-flop1', str(disk)]
    for option, name in [('cfg_directory', 'cfg'), ('nvram_directory', 'nvram'),
                         ('state_directory', 'state'), ('snapshot_directory', 'snap'),
                         ('diff_directory', 'diff')]:
        command += ['-' + option, str(session / name)]
    command += ['-artpath', str(ROOT / 'artwork'), '-view', VIEW, '-snapview', VIEW,
                '-snapsize', '1280x980', '-autoboot_script', str(ROOT / 'panel/startup.lua'),
                '-autoboot_delay', '0', '-window', '-resolution', '1280x980', '-video', 'soft',
                '-noui_active', '-uimodekey', 'SCRLOCK', '-sound', 'sdl' if os.environ.get('MPC2000XL_SOUND') else 'none', '-nosamples', '-skip_gameinfo']
    # MAME shows a "press any key" warning for this driver unless the debug flag is set. With no debugger front-end
    # ('-debugger none') this opens no window, changes nothing visible, and the emulator starts straight away.
    command += ['-debug', '-debugger', 'none']
    if debug:
        command += ['-log']
    return command

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, help='Your stock MPC2KXL.BIN (OS 1.20, 512 KiB)')
    disks = parser.add_mutually_exclusive_group()
    disks.add_argument('--disk', type=Path, help='Optional data floppy (.hfe or 1.44 MB .img)')
    disks.add_argument('--no-disk', action='store_true', help='Ignore a remembered floppy')
    disks.add_argument('--choose-disk', action='store_true', help='Choose an optional data floppy on macOS or Windows')
    parser.add_argument('--binary', type=Path, help='Executable built with the MPC2000XL target')
    parser.add_argument('--choose', action='store_true', help='Choose the ROM with the macOS or Windows file picker')
    parser.add_argument('--system-dir', type=Path, help='Folder containing the standard system filenames; see system/README.md')
    parser.add_argument('--auto', action='store_true', help='Open file pickers for missing inputs')
    parser.add_argument('--remember', action='store_true', help='Remember input paths in ignored config.local.json')
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument('--check', action='store_true', help='Validate media and report build presence, without executing MAME')
    operation.add_argument('--prepare-only', action='store_true', help='Copy media and print the command, without executing MAME')
    parser.add_argument('--debug', action='store_true', help='Enable MAME debugger and private logs')
    args = parser.parse_args()
    config = read_config(CONFIG)
    auto = args.auto or len(sys.argv) == 1
    if args.choose and (args.rom is not None or args.system_dir is not None):
        parser.error('--choose cannot be combined with --rom or --system-dir.')
    if args.rom is not None and args.system_dir is not None:
        parser.error('Use --rom or --system-dir, not both.')
    if args.choose:
        rom = choose_file('Choose your MPC2000XL MPC2KXL.BIN (stock OS 1.20)')
    elif args.rom is not None:
        rom = args.rom
    else:
        found = system_files(ROOT, args.system_dir, {'rom': ['MPC2KXL.BIN']})
        rom = found['rom']
        if rom is None and args.system_dir is None:
            rom = existing_path(config.get('rom'))
        if rom is None and args.system_dir is not None:
            parser.error('The selected system folder must contain MPC2KXL.BIN.')
    disk = None if args.no_disk else args.disk or config.get('disk')
    if args.choose_disk:
        disk = choose_file('Choose your MPC2000XL data floppy (.hfe or .img)')
    media = require_files({'rom': rom, 'disk': disk},
                          {'rom': 'Choose your MPC2000XL MPC2KXL.BIN (stock OS 1.20)'}, auto)
    rom, disk = media['rom'], media['disk']
    expected = validate(rom, disk)
    binary = resolve_binary(ROOT, TARGET, args.binary, config.get('binary'),
                            ROOT / 'build/MPC2000XL.app/Contents/MacOS' / TARGET)
    built = binary.is_file() and os.access(binary, os.X_OK)
    if args.check:
        print('MPC2000XL 1.20 ROM identity, checksum and reset vector validated.')
        print('Floppy container validated; filesystem contents unverified.' if disk else 'No data floppy selected.')
        print('Executable found (not executed or identified).' if built else 'Executable absent: follow the build instructions in README.md.')
        print('No firmware executed; no runtime or hardware result established.')
        return
    if not built and not args.prepare_only:
        raise ValueError('XL executable not found. See README.md for macOS/Windows build instructions, or supply --binary.')
    if args.remember:
        remember(CONFIG, {'rom': rom, 'disk': disk, 'binary': binary})
    run_root = ROOT / 'run'
    run_root.mkdir(mode=0o700, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix='session-', dir=run_root))
    staged_rom, staged_disk = stage(rom, disk, session, expected)
    for name in ['cfg', 'nvram', 'state', 'snap', 'diff']:
        (session / name).mkdir(mode=0o700)
    command = launch_command(binary, session, staged_rom, staged_disk, args.debug)
    environment = dict(os.environ, MPC2000XL_PANEL_INPUT=str(ROOT / 'panel/panel_input.lua'))
    (session / 'launch.json').write_text(json.dumps({'command': command, 'prepared_only': args.prepare_only}, indent=2) + '\n')
    print('Private session: ' + str(session), flush=True)
    if args.prepare_only:
        if sys.platform == 'win32':
            print('Environment: MPC2000XL_PANEL_INPUT=' + environment['MPC2000XL_PANEL_INPUT'])
            print(subprocess.list2cmdline(command))
        else:
            print('MPC2000XL_PANEL_INPUT=' + shlex.quote(environment['MPC2000XL_PANEL_INPUT']) + ' ' + shlex.join(command))
        print('Run from the session directory; original files are unchanged.')
        if not built:
            print('Build the XL executable before executing this command.')
        return
    execute(binary, command, environment, session)


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        if '-128' in (error.stderr or ''):
            raise SystemExit('File selection cancelled.')
        raise SystemExit(error.stderr or str(error))
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
