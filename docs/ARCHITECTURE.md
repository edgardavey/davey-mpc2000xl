# Architecture

`mpc2000xldiag` is a separate MAME target derived from the Classic project's
panel/LCD infrastructure and the pinned upstream MPC2000XL board model.

## CPU and native boot

A V53A runs at 32 MHz. Its physical map has eight 512 KiB RAM windows starting
at `0x000000`, `0x100000`, ... `0x700000` (4 MiB total). The 512 KiB ROM maps at
`0x080000–0x0FFFFF`, mirrored by `0x700000`. Sample RAM is a separate 32 MiB DSP
space. This differs from the Classic diagnostic first-MiB RAM map.

Initially the CPU is suspended. Quickload verifies the external 512 KiB BIN,
copies it into the allocated ROM region, resets the CPU/integrated peripherals
and resumes it. The CPU's reset address is physical `0xFFFF0`; the ROM vector
branches to `FC00:0400`. The native BIOS configures XA/page tables, checks the
OS and copies it into RAM. No Classic MZ header stripping, C000:0215 entry,
relocations or provisional handoff data are used. A reset retains the loaded
ROM; a different ROM requires a fresh process. Full reset behavior is untested.

## Devices

The board map follows MAME's `src/mame/akai/mpc2000.cpp`: MB89352 SCSI, uPD72069
FDC, MB89371 serial, ATA interface, two LCD banks and two HC259 LED latches.
SIO channel A DTR selects the FDC/ATA IRQ3 and DMA request path. The selector
recomputes both signals when changed; no host filesystem hooks are used.
Controllers start with empty ATA/SCSI buses; only the optional floppy is
exposed by the launcher. The approximate 4 MHz timer clock comes from upstream.

The LCD adapter collects guest writes into a pixel buffer (visible 248×60).
Guest LED output names are wired to the panel layout. Audio is disabled in
the launcher; including the DSP does not establish sound or sampling support.
MIDI ports and optional effects/flash expansion are not implemented.

## Panel protocol

Mouse/keyboard events become 31250-baud, 8N1 serial frames on V53 RX:
`84`/`85` key down/up, `80`/`81` wheel, `86` fader, `90..9F` pad events.
The guest interrupt handler interprets them; Lua never writes guest RAM.

The XL additions are protocol IDs `2A` Next Seq, `2B` Track Mute, `2C–2E` banks
B–D. ID `25` directly selects A.
Next Sequence, Track Mute and bank B selecting tracks 17–32 in Track Mute
were observed in the macOS guest. Other bank contexts and complete protocol
coverage remain unverified.

The panel MCU is not executed. Fixed pad velocity and immediately-ready LCD
status remain approximations. Pointer release, multi-frame clicks, Shift and
transport latches and fader dragging come from the Classic project. Its SDL
short-key patch is retained in the dedicated XL build.

## Source/build separation

`tools/fetch_mame.py` verifies the pinned archive. `tools/integrate_mame.py`
copies the driver and applies the keyboard patch to this project's own source
tree. `build_macos.sh` uses `SUBTARGET=mpc2000xldiag` and
`SOURCES=src/mame/akai/mpc2000xldiag.cpp`. No Classic binary is reused.

`run.py` and `tools/firmware.py` own external file selection and session copies.
Sources contain identity hashes and protocol metadata, not firmware bytes.
The build also wraps the executable in a local macOS app identity; the launcher
still owns firmware/session arguments. Artwork is loaded externally. The two
emulators use independent runtime
configuration, save directories or mutable MAME source/build directories.
