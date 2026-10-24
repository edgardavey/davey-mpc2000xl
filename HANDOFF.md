# HANDOFF: DAVEY MPC2000XL, for a second Claude Code session (2026-10-23)

Read this file and `CLAUDE.md` (hard rules) before anything else. Two sessions now develop in parallel on two
devices. Coordinate through git branches (below), never by editing the same files at the same time.

## 1. The user and how to work with them

- The user is edgardavey (GitHub). They test every build on a **real MPC2000XL** and talk by voice dictation, so
  messages are informal. Answer briefly: about half of a normal long report, with structure, no fluff.
- **GOLDEN RULE:** every build must stay restorable (LOAD original OS > DO IT, plus boot-from-disk), and that is
  **tested before delivery**. A past build (dark mode) broke a real unit. Never overclaim; say "emulator-tested
  only". The user's words: "dont play mr confident".
- Versioning: **EXP7 = last stable** (`release/`, GitHub `patcher-exp7`). EXP8+ is the **experimental** line
  (`release/experimental/`, GitHub pre-releases `experimental-expN`, git branch `experimental`).
- Workflow: when one feature is done, start the next one from the queue.
- Credit **vubeatz** (VU, github.com/dariuszchynek) in everything you share. His permission: free, open source,
  never sold.
- Never enter passwords; the user signs in themselves. Commit email: `17052599+edgardavey@users.noreply.github.com`.
- **Dark mode stays OUT** of EXP13 and later builds and of the patcher until the user says otherwise.

## 2. Setup on the new device

1. Clone `https://github.com/edgardavey/davey-mpc2000xl`, check out the work branch (section 4).
2. Build the emulator: `python3 tools/fetch_mame.py`, then `SDL_INSTALL_ROOT=/path/to/sdl2 bash build_macos.sh`.
3. Files that are **never in git** (Akai's OS and private data). Get them from the user:
   - the stock OS 1.20 `build_os/sys_stock/MPC2KXL.BIN` (sha256 `100e3375b4...`);
   - floppy images in `floppy/` (`funky.img`; `gold_floppy.img` = funky.img plus the ORIGINAL `MPC2KXL.BIN`
     stamped **2004-11-11 15:11**; the time matters, see 6);
   - VU's updater JSON for `patcher/gen_data.py`: `VU_UPDATER_JSON=.../MPC2000XL Updater 2.app/Contents/Resources/modular.json`
     (`exp_reloc/mods/sampling.py` can rebuild VU's sampling block from it).
4. Build: `python3 exp_reloc/make_exp.py exp_reloc/DAVEY_EXPn.BIN` (options `--mute8`, `--chop=even|lazy`).
   Test: `PAR=1 python3 exp_reloc/test_exp.py exp_reloc/DAVEY_EXPn.BIN [test ...]`. Only **one emulator at a
   time** per machine.
5. Patcher: `python3 patcher/gen_data.py` (asserts the DAVEY preset == the tested EXP file),
   `PAR=1 python3 exp_reloc/gate_presets.py` (restore gates, writes `patcher/verified_extra.json`),
   `python3 patcher/build_app.py`, parity check `jsc tools/re/parity.js` (JS engine == Python engine),
   Mac app `bash patcher/native/build_mac.sh`, Windows exe `ZIG=/path/zig python3 patcher/native/windows/build_win.py`
   (Zig 0.13; check PE subsystem = 2/GUI).

## 3. State right now

| What | State |
|---|---|
| EXP12 | RELEASED experimental (GitHub `experimental-exp12`, branch `experimental`): full Timing list (+1/4, 1/4(3)), stock-safe .ALL files ("DAVEYTC" trailer), patcher options Chop: even split / Lazy chop |
| EXP13 | **RELEASED 2026-10-24** (GitHub `experimental-exp13`, branch `experimental` = `exp13-wip`). Contents below |

EXP13 contents (user reports from 2026-10-23):

- `exp_reloc/mods/rec_start0.py`: Start = 0 after sampling. Stock sets St to the Pre-rec length (3E19:B6FA).
  Patcher option "Start at 0 after sampling", in the DAVEY preset.
- `zone_chop.py`: LAZY, hitting the pad of the LAST slice again plays on from that slice and keeps tapping armed,
  also after playback ended (`v_res`). Bug found on the way: the stock stop call 3E19:39EE does not keep BX.
- `timing_full.py`: DATA wheel order OFF, 1/4, 1/4(3), 1/8 ... 1/32(3) via a hook in the value-step routine 0:4509
  (al = up, cx = down). Stored values are unchanged (1/4 = 7, 1/4(3) = 8). The module moved to 0x75A80 (572 bytes).
- Dark mode hidden in the patcher.
- Tests: `timing`, `timing_disk`, `lazy_resume`, `rec_start0`, `chop_opts` (plus the full suite). The `mute`
  (1-8 matrix) test needs a `--mute8` build; on the default build it fails by design.

Release steps after the tests pass: full suite, gates, patcher/apps, `release/experimental/` (move the old build to
`superseded/`), README + guides (TUTORIAL.md, DAVEY_TUTORIAL.txt, DAVEY_CHEAT_SHEET.md EN/RU), commit, push
`experimental`, `gh release create experimental-expN ... --prerelease`. Never upload a .BIN.

## 4. Who does what (proposal, user to confirm)

- **Device 1 (this session):** released EXP13 (done). Next: whatever the user assigns (EXP14 if device 2 doesn't take it).
- **Device 2 (you):** **EXP14 = Sampling Mode on any sound** (section 5) on a new branch `exp14-sound-lofi`
  from `experimental`. Put the code in a NEW module `exp_reloc/mods/sound_lofi.py`; touch `make_exp.py`,
  `test_exp.py`, `gen_data.py` and `app_template.html` only with small additive blocks. Rebase on `experimental`
  once EXP13 is released.
- Do not edit `zone_chop.py`, `timing_full.py` or `rec_start0.py` without agreeing with the other session first.
- Free-memory placements are shared, see 6. **Claim a range in this file before using it.**

## 5. EXP14 plan (approved by the user 2026-10-23)

User flow: SHIFT+5 TRIM, hit a pad (our TRIM pad select makes its sound current) → F5 EDIT → `Edit:` new entry
**SAMPLING MODE** → SP1200 / S900 / custom rate → **New sound** (default; original untouched) or **Replace**
(warning "Used by N pads. No undo!") → DO IT → "processing" box → for a new sound, a window like the stock
after-sampling KEEP/RETRY: name (default `<name>-SP`/`-S9`, editable) and **hit any pad** to assign (or OFF).
The PARAMS screen is NOT an option: all its WINDOW keys are already taken (user).

Facts (static analysis by three advisor agents; **verify in the emulator first**):

- Stock Edit window: list of 9 far ptrs at **582B:25DC** (data follows, so relocate the table to add a 10th entry);
  draw code 3E19:ED5B (name via `[8D4C]*4 + 25DC`, then per-function draw jump, `cmp ax,8`);
  DO IT **3E19:EBF6** jumps on `[8D4C]` (`cmp ax,7; ja` = slice). Hooks needed: name, list max,
  parameter lines, DO IT branch, the field max for `[8D4C]` (not located yet).
- VU's sampling block (linear 0x77620-0x77E51, seg 0x7762): processing entry **7762:019D** works **in place**
  (16-word DMA chunks via 35B0:0566/056C with cli). It takes the header pointer from `[8B4A]` (`les` at
  block+0x1F4) and needs header +0x0A (DSP addr), +0x0E (buffer size), +0x25 (stereo), +0x2E (length).
  Settings cs:0x730 mode (1 SP1200, 2 S900), cs:0x736 rate. Status 0x77D62 (2 started, 1 done, 3 empty).
  It **hard-codes 44100**, so scale by header +0x38 for other rates. S900 = saturation + IIR (no decimation).
  **Unknown:** +0x0E on sounds loaded from disk; dump mono and stereo headers first.
- Stock create/copy: template allocator 3E19:328E(out, src, name, frames); raw allocator 3388 (errors
  "Sound directory full", "not enough memory"); **Copy Sound 3E19:23C6(out, src, name)**; Section 2A0A.
  Name buffer ds:8FCB. After creating: set [D7C2] = new sound, call 35B0:84B2 (waveform cache), 3E19:0C22.
  Stock RE-SAMPLE 4E16:9694 exists (clean filter, no 12-bit), so it is not used for the SP1200 sound.
- Assign to a pad: KEEP 3E19:BB16 writes `prog[0x752 + note*4] = far sound ptr` (prog via 35B0:0418(0x5C+[D7BE])),
  then calls 3E19:A5F2.
- Refuse while the sequencer plays (DMA writes to sample RAM). Check free memory; the copy needs as much as the
  original.

## 6. Technical ground rules (learned the hard way)

- **NEC V53 = 80186.** No 0F/66/67 opcodes. Assemble only through `exp_reloc/mods/asm16.py` (fixes jcc, rewrites
  ret/retf, fails on prefixes). Write near calls as `.byte 0xe8; .word t - . - 2`; load addresses with
  `mov si, offset X`; return with `.byte 0xc3/0xcb`.
- Image 0x00000-0x77FFF = RAM; checksum word 0x77FFE; 0x78000+ never changes. **Program-slot RAM 0x65AE0-0x741AF:
  no code there.** New code only in `make_exp.FREE` ranges (guarded by `Img._check`).
- Placed now: wave_fast 0x74A00 (144), zone_chop 0x74F00 (~2650), **timing_full 0x75A80-0x75CBC**, mute8
  0x75CF0 (exp builds) / 0x77F00 (patcher), prog_mono 0x75E00, sampling block 0x77620-0x77E51, mute_all 0x77E60.
  **Still free:** 0x749A4-0x749FF, 0x74A90-0x74CB1, 0x74CF1-0x74EF5, 0x75E50-0x761E1, 0x761EC-0x762F3,
  0x762FD-0x76540, 0x76DCB-0x77000. Device 2 claims **0x76000-0x76540** for EXP14 (adjust here if needed).
- Event tables: 5-byte entries {code, off, seg}; never hook a field's per-field slot (it is also the
  value-changed callback). INT 8F = display ops (one op per int, inline data after `int 8f`).
- Every fix gets a test in `exp_reloc/test_exp.py` that **fails on the old build and passes on the new one**.
- OS update refuses OS files with a FAT time before 01:14 ("OS version too old") on 16-bit-flash units. The
  Mac/Windows apps stamp 01:14.
- Emulator caveats: no real audio input (sampling tests inject data), flash writes only on `emu-dev`, timing
  approximate. Debugger **watchpoints on hot variables stall the emulator**: use `bpset` on code addresses (linear
  addresses, e.g. `bpset 401`), Lua write taps, or printf-to-console + read `debugger.consolelog`. NEC register
  names: ps/pc/ds0/ds1/aw/bw/cw/dw/ix/iy.
- Watch out: `pgrep -f "test_exp.py"` also matches your own waiting shell. Check `ps` for the real Python process.
- Tools: `tools/re/v53dis.py BIN SEG OFF [N]` (disassembler); `tools/re/*.py` are probe scripts (debugger
  breakpoints, write taps, sampling/TRIM probes); `exp_reloc/fat12.py` reads a file from a floppy image.

## 7. Queue after EXP14

- `<Filter>` label on PROGRAM PARAMS as a cursor stop: only if the TRIM route is rejected (medium risk).
- Limited "trim while the sequence plays" (analysed, not built; user decision pending).
- Emulator `emu-dev`: finish the flash model (update → power cycle → boot from flash), then record input, CF/ATA.
- The Windows patcher has never run on a real Windows PC.
