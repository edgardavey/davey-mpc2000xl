# Third-party provenance

This project derives from Vubeatz MPC2000 Classic Emulator source. Its panel,
LCD/serial prototype and tooling were adapted for a separate MPC2000XL target.
The original project and upstream copyright/license notices are retained.

## MAME

Pinned commit: `774a180df2b6ef9c53e48337792256817c50f768`.
Archive identity and download URL: `mame.lock.json`.

- [Reference MPC driver](https://github.com/mamedev/mame/blob/774a180df2b6ef9c53e48337792256817c50f768/src/mame/akai/mpc2000.cpp):
  BSD-3-Clause, copyright R. Belmont. `src/mpc2000xldiag.cpp` adapts hardware
  wiring/LCD code and retains the attribution in its header.
- [SDL input backend](https://github.com/mamedev/mame/blob/774a180df2b6ef9c53e48337792256817c50f768/src/osd/modules/input/input_sdl.cpp):
  BSD-3-Clause, copyright Olivier Galibert, R. Belmont, Brad Hughes and Vas Crabb.
  `tools/patch_mame_keyboard.py` includes small source fragments and adds
  short-key-press retention for the dedicated build.

The exact upstream `COPYING` is included as `licenses/MAME-COPYING`, with
`licenses/BSD-3-Clause` and `licenses/GPL-2.0`. MAME as a whole is GPL-2.0;
individual files and dependencies have their own notices. Fetching MAME brings
its complete source and `docs/legal/` directory, which must be preserved when
preparing a distribution. This project's BSD license applies to its own work,
not to the combined executable as a whole.

No MAME executable is included. A future binary release needs the corresponding
complete source/build modifications and relevant license notices; the driver
file alone is not the complete source of such a release.

## Other dependencies and assets

SDL2, Python, compiler tools and macOS frameworks are system/build dependencies,
not redistributed in the source tree. SDL2 uses the
[zlib license](https://www.libsdl.org/license.php). A binary release must also
account for the exact runtime libraries it ships. The optional artwork
generator uses installed fonts
through CoreText and writes outlines of the panel labels; no font file or
reference photograph is bundled. The panel geometry and model lettering are
custom vector artwork. Product and project names remain their owners' marks.

No proprietary operating system, ROM, service-manual PDF, disk contents or
private modification payload is part of the source distribution.

## Documentation screenshot and proprietary inputs

`docs/images/emulator.png` is a reviewed capture of the corresponding emulator
on macOS. It is documentation, not a ROM or RAM dump. The depicted guest UI and
product names remain the property of their respective owners and are not
relicensed as project code.

User media in `system/`, saved configuration, runtime sessions and their contents
are private and ignored. The project license grants no rights to redistribute
AKAI firmware, third-party disk images or sample libraries. Including them in a
repository or binary bundle requires separate rights.

References: [MAME licensing](https://www.mamedev.org/legal.html),
[pinned upstream COPYING](https://github.com/mamedev/mame/blob/774a180df2b6ef9c53e48337792256817c50f768/COPYING),
[GPL version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html).
