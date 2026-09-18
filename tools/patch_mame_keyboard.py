#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# SDL patch based on BSD-3-Clause MAME input_sdl.cpp; see THIRD_PARTY.md.
"""Preserve short SDL key taps in this isolated MPC2000XL-only MAME build."""
import argparse
from pathlib import Path
import hashlib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True, help='Pinned MAME source directory')
source = parser.parse_args().source / 'src/osd/modules/input/input_sdl.cpp'
data = source.read_text()
existing = data
# The Classic and XL targets use the same keyboard pulse implementation.
# Normalize its comment, then reverse and verify every change against the
# pinned upstream hash below before accepting or writing that source.
data = data.replace('// Classic prototype: keep down/up in one SDL batch observable.',
                    '// MPC2000XL prototype: keep down/up in one SDL batch observable.')
changes = [
    ('\t\tsdl_device::poll(relative_reset);\n\n#ifdef __APPLE__',
     '\t\t// MPC2000XL prototype: keep down/up in one SDL batch observable.\n'
     '\t\tconst auto now = std::chrono::steady_clock::now();\n'
     '\t\tfor (unsigned key = 0; key < SDL_NUM_SCANCODES; ++key)\n'
     '\t\t{\n'
     '\t\t\tif (m_release_pending[key] && now >= m_key_release_after[key])\n'
     '\t\t\t{\n'
     '\t\t\t\tm_keyboard.state[key] = 0;\n'
     '\t\t\t\tm_release_pending[key] = false;\n'
     '\t\t\t}\n'
     '\t\t}\n'
     '\t\tsdl_device::poll(relative_reset);\n\n#ifdef __APPLE__'),
    ('\t\t\tm_keyboard.state[event.key.keysym.scancode] = 0x80;\n',
     '\t\t\tif (!event.key.repeat)\n'
     '\t\t\t\tm_key_release_after[event.key.keysym.scancode] = std::chrono::steady_clock::now() + std::chrono::milliseconds(30);\n'
     '\t\t\tm_release_pending[event.key.keysym.scancode] = false;\n'
     '\t\t\tm_keyboard.state[event.key.keysym.scancode] = 0x80;\n'),
    ('\t\t\tm_keyboard.state[event.key.keysym.scancode] = 0x00;\n',
     '\t\t\tif (std::chrono::steady_clock::now() < m_key_release_after[event.key.keysym.scancode])\n'
     '\t\t\t\tm_release_pending[event.key.keysym.scancode] = true;\n'
     '\t\t\telse\n'
     '\t\t\t\tm_keyboard.state[event.key.keysym.scancode] = 0x00;\n'),
    ('\t\tmemset(&m_keyboard, 0, sizeof(m_keyboard));\n',
     '\t\tmemset(&m_keyboard, 0, sizeof(m_keyboard));\n'
     '\t\tstd::fill(std::begin(m_release_pending), std::end(m_release_pending), false);\n'),
    ('\tkeyboard_state m_keyboard;\n',
     '\tkeyboard_state m_keyboard;\n'
     '\tstd::chrono::steady_clock::time_point m_key_release_after[SDL_NUM_SCANCODES]{};\n'
     '\tbool m_release_pending[SDL_NUM_SCANCODES]{};\n'),
]
pristine = 'de9b5c9f775fb1175408650246fea3032afff7768bbfc4a014cdef9f4785952c'
if 'MPC2000XL prototype: keep down/up' in data:
    original = data
    for before, after in reversed(changes):
        if original.count(after) != 1:
            raise SystemExit('Unexpected existing SDL keyboard patch')
        original = original.replace(after, before, 1)
    if hashlib.sha256(original.encode()).hexdigest() != pristine:
        raise SystemExit('Patched SDL source does not match pinned upstream')
    if data != existing:
        source.write_text(data)
else:
    if hashlib.sha256(data.encode()).hexdigest() != pristine:
        raise SystemExit('Unexpected upstream SDL keyboard source')
    for before, after in changes:
        if data.count(before) != 1:
            raise SystemExit('SDL patch anchor is not unique')
        data = data.replace(before, after, 1)
    source.write_text(data)
print('MPC2000XL SDL keyboard pulse patch ready')
