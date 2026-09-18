#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""Audit the publication manifest, file content and documentation images."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRS = {'.git', 'vendor', 'build', 'dist', 'run', 'local', 'firmware', 'roms', 'media',
                '.cache', '__pycache__', '.agents', '.codex', '.claude', '.cursor'}
PRIVATE_NAMES = {'config.local.json', '.ds_store', 'agents.md', 'agents.override.md',
                 'claude.md', 'gemini.md', '.cursorrules', '.env', 'copilot-instructions.md'}
PRIVATE_SUFFIXES = {'.exe', '.sys', '.rom', '.bin', '.hfe', '.img', '.wav', '.snd', '.pgm',
                    '.aps', '.zip', '.gz', '.7z', '.dmg', '.dmp', '.log', '.pem', '.key', '.p12', '.pfx'}
PUBLIC_IMAGES = {'docs/images/emulator.png': '4a9e77ff437610c48b12dc70b401a421ebbfa0c17b124fcf7201936eefa527db'}
UPSTREAM_NOTICES = {'licenses/MAME-COPYING': '60e9b2e1e0832d74696a9a0317693bb6cbe317747caad589a338e2c7636933e4'}
CHECKS = {
    'Private home-directory path': re.compile(r'/(?:Users|home)/[^/\s]+|\b[A-Za-z]:[\\/]+(?:Users|Documents and Settings)[\\/]+[^\\/\s]+', re.I),
    'Private key': re.compile(r'-----BEGIN\s+(?:(?:RSA|EC|DSA|OPENSSH)\s+)?PRIVATE\s+KEY-----'),
    'Credential-shaped token': re.compile(r'\b(?:gh[pousr]_|github_pat_|xox[baprs]-|sk-proj-)[A-Za-z0-9_-]{12,}|\bAKIA[A-Z0-9]{16}\b|\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}'),
    'Large encoded payload': re.compile(r'[A-Za-z0-9+/=]{256,}'),
    'Embedded URL credentials': re.compile(r'https?://[^\s/:@]+:[^\s/@]+@'),
    'Hard-coded secret assignment': re.compile(r'''\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd)\s*[=:]\s*["'][^"'\s]{8,}["']''', re.I),
    'Conversation residue': re.compile(r'''\b(?:as\s+requested|in\s+this\s+turn|this\s+conversation|our\s+(?:agreement|conversation)|(?:user['’]s|supplied|provided)\s+(?:hardware\s+)?(?:photo|reference|instructions)|(?:system|developer)\s+prompt)\b|<\/?(?:oai-mem-citation|analysis|assistant|user)>''', re.I),
    'Agent permission instruction': re.compile(r'''\b(?:do\s+not|don't|never)\s+(?:use\s+skills|build\s+or\s+launch)|without\s+(?:explicit\s+)?user\s+(?:authorization|approval)''', re.I),
    'Invisible or directional control': re.compile('[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]'),
}
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def private_path(name):
    path = PurePosixPath(name)
    return (any(part.casefold() in PRIVATE_DIRS or part.casefold() in PRIVATE_NAMES
                or part.casefold().startswith('.env.') for part in path.parts)
            or path.suffix.lower() in PRIVATE_SUFFIXES
            or ('system' in path.parts and name != 'system/README.md'))


def image_errors(name, data):
    if not data.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(data).hexdigest() != PUBLIC_IMAGES[name]:
        return ['Unreviewed or invalid documentation image: ' + name]
    position = 8
    while position + 12 <= len(data):
        size = struct.unpack_from('>I', data, position)[0]
        kind = data[position + 4:position + 8]
        position += size + 12
        if position > len(data):
            break
        if kind in {b'tEXt', b'zTXt', b'iTXt', b'eXIf', b'tIME'}:
            return ['Unexpected documentation image metadata: ' + name]
        if kind == b'IEND':
            return [] if position == len(data) else ['Data after PNG end: ' + name]
    return ['Malformed documentation image: ' + name]


def audit(root, strict=False):
    root = Path(root)
    entries = [line.strip() for line in (root / 'PUBLIC_FILES.txt').read_text(encoding='utf-8').splitlines()
               if line.strip() and not line.startswith('#')]
    expected = set(entries)
    if len(expected) != len(entries):
        raise ValueError('Duplicate public manifest entry')
    for name in expected:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or path.as_posix() != name:
            raise ValueError('Unsafe path in public manifest')
        if private_path(name):
            raise ValueError('Private file cannot be included in public manifest: ' + name)
    if not strict and (root / '.git').exists():
        output = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'])
        actual = {name.decode('utf-8') for name in output.split(b'\0') if name}
    else:
        actual = set()
        def visit(directory):
            for path in directory.iterdir():
                relative = path.relative_to(root)
                if relative.parts[0] == '.git':
                    continue
                if not strict:
                    if relative.parts[0].casefold() in PRIVATE_DIRS or path.name == '__pycache__':
                        continue
                    if len(relative.parts) == 1 and path.name.casefold() in PRIVATE_NAMES:
                        continue
                    if relative.parts[0] == 'system' and len(relative.parts) > 1 and relative.as_posix() != 'system/README.md':
                        continue
                if path.is_symlink():
                    actual.add(relative.as_posix())
                elif path.is_dir():
                    visit(path)
                else:
                    actual.add(relative.as_posix())
        visit(root)
    errors = []
    if expected - actual:
        errors.append('Missing public files: ' + ', '.join(sorted(expected - actual)))
    if actual - expected:
        errors.append('Unexpected files: ' + ', '.join(sorted(actual - expected)))
    for name in sorted(expected & actual):
        path = root / name
        if any((root / parent).is_symlink() for parent in [PurePosixPath(name), *PurePosixPath(name).parents]):
            errors.append('Symlink in public file path: ' + name)
            continue
        data = path.read_bytes()
        if name in PUBLIC_IMAGES:
            errors.extend(image_errors(name, data))
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            errors.append('Binary payload: ' + name)
            continue
        if b'\0' in data or data.startswith((b'MZ', b'HXCPICFE', b'\x7fELF')):
            errors.append('Binary/firmware signature: ' + name)
        for label, pattern in CHECKS.items():
            for match in pattern.finditer(text):
                line = text.count('\n', 0, match.start()) + 1
                # Report location only; never print a possible secret.
                errors.append(f'{label}: {name}:{line}')
        for match in EMAIL.finditer(text):
            if UPSTREAM_NOTICES.get(name) == hashlib.sha256(data).hexdigest():
                continue
            errors.append(f'Unreviewed contact address: {name}:{text.count(chr(10), 0, match.start()) + 1}')
    if errors:
        raise ValueError('\n'.join(errors))
    return len(expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true', help='Also reject ignored/generated files in a clean export')
    args = parser.parse_args()
    try:
        print(f'Public source audit passed: {audit(ROOT, args.strict)} source/documentation/artwork files.')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
