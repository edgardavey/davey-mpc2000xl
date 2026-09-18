# SPDX-License-Identifier: BSD-3-Clause
"""Host-side file selection and launch helpers. No firmware is included."""
import json
import os
from pathlib import Path
import subprocess
import sys


def choose_file(prompt):
    if sys.platform == 'darwin':
        result = subprocess.run(
            ['osascript', '-e', 'POSIX path of (choose file with prompt ' + json.dumps(prompt) + ')'],
            check=True, capture_output=True, text=True)
        return Path(result.stdout.strip())
    if sys.platform == 'win32':
        try:
            import tkinter
            from tkinter import filedialog
        except ImportError as error:
            raise ValueError('The Windows picker needs Python with Tcl/Tk (included in the standard python.org installer). '
                             'Alternatively, pass the file paths on the command line.') from error
        window = tkinter.Tk()
        window.withdraw()
        try:
            window.attributes('-topmost', True)
            selected = filedialog.askopenfilename(parent=window, title=prompt)
        finally:
            window.destroy()
        if not selected:
            raise ValueError('File selection cancelled.')
        return Path(selected)
    raise ValueError('File pickers support macOS and Windows. Supply file paths or --system-dir on this platform.')


def read_config(path):
    config = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('config.local.json must contain a JSON object.')
    return config


def existing_path(value):
    path = Path(value).expanduser().resolve() if value else None
    return path if path and path.is_file() else None


def named_file(folder, names):
    """Case-insensitive names, but never silently choose between two images."""
    if not folder.is_dir():
        return None
    names = {name.casefold() for name in names}
    matches = sorted(p for p in folder.iterdir() if p.is_file() and p.name.casefold() in names)
    if len(matches) > 1:
        raise ValueError('More than one matching system file in ' + str(folder) + ': ' +
                         ', '.join(p.name for p in matches) + '. Keep one or select files explicitly.')
    return matches[0] if matches else None


def system_files(root, folder, specification):
    directory = Path(folder).expanduser().resolve() if folder is not None else root / 'system'
    if folder is not None and not directory.is_dir():
        raise ValueError('System folder does not exist: ' + str(directory))
    return {key: named_file(directory, names) for key, names in specification.items()}


def require_files(values, prompts, auto=False):
    """Only missing paths trigger a picker; invalid supplied files fail validation."""
    for key, prompt in prompts.items():
        if values.get(key) is None:
            if not auto:
                raise ValueError('Missing ' + key + '. Supply explicit paths, --system-dir, or --choose. '
                                 'Double-click Launch Emulator for automatic selection.')
            values[key] = choose_file(prompt)
    return {key: Path(value).expanduser().resolve() if value else None for key, value in values.items()}


def resolve_binary(root, target, explicit=None, remembered=None, bundle=None):
    if explicit:
        return Path(explicit).expanduser().resolve()
    saved = existing_path(remembered)
    # A shared source folder may contain a saved path from the other platform.
    if saved and ((sys.platform == 'win32') == (saved.suffix.lower() == '.exe')):
        return saved
    if sys.platform == 'darwin' and bundle and bundle.is_file():
        return bundle
    filename = target + ('.exe' if sys.platform == 'win32' else '')
    return root / 'build/bin' / filename


def remember(path, values):
    with open(path, 'w', encoding='utf-8', opener=lambda name, flags: os.open(name, flags, 0o600)) as output:
        json.dump({key: str(value) if value is not None else None for key, value in values.items()}, output, indent=2)
        output.write('\n')
    path.chmod(0o600)


def execute(binary, command, environment, session):
    if sys.platform == 'win32':
        # Keep the .cmd window alive until MAME exits; no shell interpolation.
        raise SystemExit(subprocess.call(command, cwd=session, env=environment))
    os.chdir(session)
    os.execve(binary, command, environment)
