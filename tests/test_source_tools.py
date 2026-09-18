# SPDX-License-Identifier: BSD-3-Clause
"""Synthetic host-side checks. No firmware, MAME build, GUI or guest execution."""
import hashlib
import io
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools import firmware
from tools.audit_public import audit
from tools.fetch_mame import extract


class MediaStaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rom, self.disk = self.root / 'owned.bin', self.root / 'owned.hfe'
        # Artificial zero-filled image with a synthetic jump and checksum.
        # No bytes are taken from a proprietary operating system.
        data = bytearray(firmware.ROM_BYTES)
        data[firmware.RESET_OFFSET] = 0xea
        struct.pack_into('<HH', data, firmware.RESET_OFFSET + 1, 0x400, 0xfc00)
        self.rom.write_bytes(data)
        self.disk.write_bytes(b'HXCPICFE' + bytes(504))
        self.pin = patch.object(firmware, 'ROM_SHA256', hashlib.sha256(data).hexdigest())
        self.pin.start()
        self.addCleanup(self.pin.stop)

    def test_wrong_rom_is_rejected(self):
        self.rom.write_bytes(b'not an OS')
        with self.assertRaises(ValueError):
            firmware.validate(self.rom)

    def test_same_sized_unknown_rom_is_rejected(self):
        self.rom.write_bytes(bytes(firmware.ROM_BYTES))
        with self.assertRaisesRegex(ValueError, 'supported stock'):
            firmware.validate(self.rom)

    def test_checksum_failure_is_separate_from_identity(self):
        data = bytearray(self.rom.read_bytes())
        data[0] = 1
        self.rom.write_bytes(data)
        with patch.object(firmware, 'ROM_SHA256', hashlib.sha256(data).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                firmware.validate(self.rom)

    def test_reset_vector_failure_is_separate_from_identity(self):
        data = bytearray(self.rom.read_bytes())
        data[firmware.RESET_OFFSET] = 0
        self.rom.write_bytes(data)
        with patch.object(firmware, 'ROM_SHA256', hashlib.sha256(data).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'reset vector'):
                firmware.validate(self.rom)

    def test_disk_header_is_required(self):
        self.disk.write_bytes(b'wrong header' + bytes(512))
        with self.assertRaises(ValueError):
            firmware.validate(self.rom, self.disk)

    def test_original_is_unchanged_when_session_disk_is_written(self):
        expected = firmware.validate(self.rom, self.disk)
        before = self.disk.read_bytes()
        session = self.root / 'session'
        session.mkdir()
        copied_rom, copied_disk = firmware.stage(self.rom, self.disk, session, expected)
        self.assertEqual(copied_rom.read_bytes(), self.rom.read_bytes())
        self.assertEqual(copied_rom.stat().st_mode & 0o777, 0o400)
        copied_disk.write_bytes(b'guest write')
        self.assertEqual(self.disk.read_bytes(), before)

    def test_floppy_is_optional(self):
        expected = firmware.validate(self.rom)
        session = self.root / 'session'
        session.mkdir()
        copied_rom, copied_disk = firmware.stage(self.rom, None, session, expected)
        self.assertIsNone(copied_disk)
        self.assertEqual(copied_rom.read_bytes(), self.rom.read_bytes())

    def test_refuses_existing_session_media(self):
        expected = firmware.validate(self.rom, self.disk)
        session = self.root / 'session'
        session.mkdir()
        firmware.stage(self.rom, self.disk, session, expected)
        with self.assertRaises(FileExistsError):
            firmware.stage(self.rom, self.disk, session, expected)

    def test_changed_disk_is_detected_before_guest_execution(self):
        expected = firmware.validate(self.rom, self.disk)
        self.disk.write_bytes(b'HXCPICFE' + bytes(505))
        session = self.root / 'session'
        session.mkdir()
        with self.assertRaises(ValueError):
            firmware.stage(self.rom, self.disk, session, expected)

    def test_changed_rom_is_detected_before_guest_execution(self):
        expected = firmware.validate(self.rom)
        self.rom.write_bytes(bytes(firmware.ROM_BYTES))
        session = self.root / 'session'
        session.mkdir()
        with self.assertRaises(ValueError):
            firmware.stage(self.rom, None, session, expected)


class LaunchCommand(unittest.TestCase):
    def test_rom_boot_does_not_require_a_floppy(self):
        from run import launch_command
        command = launch_command(Path('emulator'), Path('session'), Path('rom.bin'))
        self.assertEqual(command[1], 'mpc2000xldiag')
        self.assertEqual(command[command.index('-quik') + 1], 'rom.bin')
        self.assertNotIn('-flop1', command)
        self.assertEqual(command[command.index('-sound') + 1], 'none')

    def test_optional_floppy_uses_supplied_session_path(self):
        from run import launch_command
        command = launch_command(Path('emulator'), Path('session'), Path('rom.bin'), Path('session/media/floppy.img'))
        self.assertEqual(command[command.index('-flop1') + 1], 'session/media/floppy.img')


class SourceArchive(unittest.TestCase):
    def test_rejects_archive_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            archive = folder / 'test.tar.gz'
            with tarfile.open(archive, 'w:gz') as output:
                entry = tarfile.TarInfo('source/../../escape')
                entry.size = 1
                output.addfile(entry, io.BytesIO(b'x'))
            with self.assertRaises(ValueError):
                extract(archive, folder / 'out', 'source')
            self.assertFalse((folder / 'out').exists())

    def test_regular_source_and_internal_link(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            archive = folder / 'test.tar.gz'
            with tarfile.open(archive, 'w:gz') as output:
                entry = tarfile.TarInfo('source/file.txt')
                entry.size = 3
                output.addfile(entry, io.BytesIO(b'abc'))
                link = tarfile.TarInfo('source/link.txt')
                link.type = tarfile.SYMTYPE
                link.linkname = 'file.txt'
                output.addfile(link)
            extract(archive, folder / 'out', 'source')
            self.assertEqual((folder / 'out/source/link.txt').read_bytes(), b'abc')


class PublicAudit(unittest.TestCase):
    def test_unknown_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / 'PUBLIC_FILES.txt').write_text('PUBLIC_FILES.txt\nREADME.md\n')
            (folder / 'README.md').write_text('Clean source\n')
            self.assertEqual(audit(folder, strict=True), 2)
            (folder / 'unexpected.data').write_bytes(bytes(8))
            with self.assertRaises(ValueError):
                audit(folder, strict=True)

    def test_binary_cannot_be_whitelisted_as_documentation(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / 'PUBLIC_FILES.txt').write_text('PUBLIC_FILES.txt\nREADME.md\n')
            (folder / 'README.md').write_bytes(b'MZ' + bytes(12))
            with self.assertRaises(ValueError):
                audit(folder, strict=True)


if __name__ == '__main__':
    unittest.main()
