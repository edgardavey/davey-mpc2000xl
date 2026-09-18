#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""Fetch only the pinned open-source MAME archive, never firmware or ROMs."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def extract(archive, destination, expected_root):
    # Write regular files first; links cannot redirect extraction outside it.
    with tarfile.open(archive, 'r:gz') as source:
        members = source.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if not path.parts or path.is_absolute() or '..' in path.parts or path.parts[0] != expected_root:
                raise ValueError('Unsafe archive path: ' + member.name)
            if not (member.isfile() or member.isdir() or member.issym()):
                raise ValueError('Unsupported archive entry: ' + member.name)
            if member.issym():
                target = posixpath.normpath(posixpath.join(str(path.parent), member.linkname))
                if member.linkname.startswith('/') or not target.startswith(expected_root + '/'):
                    raise ValueError('Unsafe archive link: ' + member.name)
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as incoming, target.open('xb') as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                target.chmod(member.mode & 0o777)
        for member in members:
            if member.issym():
                target = destination / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(member.linkname)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use a local copy instead of downloading')
    args = parser.parse_args()
    lock = json.loads((ROOT / 'mame.lock.json').read_text())
    vendor = ROOT / 'vendor'
    target = vendor / 'mame'
    if target.exists():
        marker = target / '.mpc2000xl-upstream.json'
        if marker.is_file() and json.loads(marker.read_text()) == lock:
            print('Pinned MAME source already present: ' + str(target))
            return
        raise ValueError('Refusing to replace an existing vendor/mame directory')
    vendor.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.mame-fetch-', dir=vendor) as temporary:
        temporary = Path(temporary)
        archive = temporary / 'mame.tar.gz'
        if args.archive:
            shutil.copyfile(args.archive, archive)
        else:
            request = urllib.request.Request(lock['archive_url'], headers={'User-Agent': 'mpc2000xl-emulator-source-fetch'})
            with urllib.request.urlopen(request, timeout=60) as incoming, archive.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing)
        digest = hashlib.sha256()
        with archive.open('rb') as incoming:
            for block in iter(lambda: incoming.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != lock['archive_sha256']:
            raise ValueError('MAME archive checksum mismatch; nothing installed')
        extract(archive, temporary, lock['archive_root'])
        extracted = temporary / lock['archive_root']
        (extracted / '.mpc2000xl-upstream.json').write_text(json.dumps(lock, indent=2) + '\n')
        os.rename(extracted, target)
    print('Verified MAME source: ' + str(target))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, tarfile.TarError) as error:
        raise SystemExit(str(error))
