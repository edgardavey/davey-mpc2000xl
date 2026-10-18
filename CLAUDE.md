# DAVEY MPC2000XL: rules for every contributor and their AI agent

This repo is a fork of [dariuszchynek/mpc2000xl-emulator](https://github.com/dariuszchynek/mpc2000xl-emulator) (BSD-3) by **vubeatz** (dariuszchynek)
extended with **DAVEY OS**: patches for the Akai MPC2000XL OS 1.20 (chop screen, Program MONO, TRIM pad select,
Sampling Mode, …), a **patcher app** and an emulator-based **test suite**. Builds go onto real units, so the rules below
are not optional.

## Golden rule
Every build must be restorable, and that is **tested before it is delivered**: restore by update (LOAD the original
`MPC2KXL.BIN` → DO IT) and boot-from-disk. Never claim something works on hardware when only the emulator saw it.
Say "emulator-tested only".

## Hard rules for OS patches
1. **Never commit Akai's OS** or anything containing it (`*.BIN`, floppy images, REMEDY, card backups). Each contributor
   uses their own stock `MPC2KXL.BIN` 1.20 (sha256 starts `100e3375`).
2. **NEC V53 = 80186-class.** No 386 instructions. clang `-m16` silently emits `0F 8x` long jumps that crash the unit.
   Assemble only through `exp_reloc/mods/asm16.py` (rewrites jumps, refuses `0F`/`66`/`67`).
3. **Program-slot RAM 0x65AE0–0x741AF** is overwritten when programs are created (24 × 0x99E). No code or data there.
   New code goes only into measured-free ranges (`exp_reloc/make_exp.py` `FREE`, guarded by `Img._check`).
4. The boot area `0x78000–0x7FFFF` never changes; the checksum word at `0x77FFE` is recomputed.
5. Change only what a feature needs; keep stock behaviour everywhere else (the `twin` test compares 76 screens with
   the VU base).
6. Every fix gets a test in `exp_reloc/test_exp.py` that **fails on the old build and passes on the new one**.

## Layout
| Path | What |
|---|---|
| `src/`, `tools/`, `run.py` | the emulator (MAME target `mpc2000xldiag`); `tools/dev/` = scripted test runner |
| `exp_reloc/` | current OS build line: `make_exp.py` (guarded builder), `mods/` (chop, sampling, mute8, prog_mono, asm16), `test_exp.py` (suite), `gate_presets.py` (patcher restore gates), `cov/` (free-RAM measurement) |
| `build_os/` | older builders + `suite/` test harness (`harness.py`, `phases.py`) |
| `patcher/` | patcher: `gen_data.py` → `modules.json`, `engine.py`/`engine.js` (must agree byte for byte), `app_template.html`, `build_app.py`, `native/` (macOS app) |
| `docs/` | emulator architecture/status; `DAVEY_CHEAT_SHEET.md` = user guide (EN/RU) |

## Setup (macOS)
1. Build the emulator: `python3 tools/fetch_mame.py`, then `SDL_INSTALL_ROOT=/path/to/sdl2 bash build_macos.sh`.
2. Put your stock OS at `build_os/sys_stock/MPC2KXL.BIN`; build the test floppies (`tools/make_floppy.sh`).
3. VU's module data: `patcher/modules.json` is committed. To regenerate it you need VU's *MPC2000XL Updater 2.app*;
   point `VU_UPDATER_JSON` at its `Contents/Resources/modular.json`.
4. Build an OS: `python3 exp_reloc/make_exp.py exp_reloc/DAVEY_EXPn.BIN`; test:
   `PAR=1 python3 exp_reloc/test_exp.py exp_reloc/DAVEY_EXPn.BIN` (one emulator at a time; `PAR=1`).
5. Patcher: `python3 patcher/gen_data.py` (asserts the DAVEY preset equals the tested EXP file), `python3 exp_reloc/gate_presets.py`,
   `python3 patcher/build_app.py`.

## Emulator caveats (see docs and the audit notes)
Recording input is not modelled; flash writes are modelled only on the `emu-dev` branch (Intel 28F400BV-T, WIP);
pad velocity is fixed; timing is approximate; Lua read taps don't fire for CPU reads (use debugger watchpoints,
NEC register names `ps`/`pc`/`ds0`/`ds1`/`aw`). Emulator fixes need evidence (OS code, datasheet, or a real-unit
measurement), never "it makes a test pass".

## Credits
Emulator: **vubeatz** ([dariuszchynek](https://github.com/dariuszchynek), BSD-3). VU base features and their module data: **vubeatz**
(included with his permission, given 2026-10-18, on his terms: free and open source, never sold; credit him in anything you share; project link in README). MAME: its own licenses (`vendor/` is fetched, not committed).
