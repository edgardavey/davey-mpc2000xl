# EXPERIMENTAL line: DAVEY EXP1 (not a release, not connected to build_os/, release/ or the patcher)

Why it exists: DAVEY code in older builds sat in 0x70000-0x741AF, which is RAM the OS uses for programs 18-24.
It got wiped once 18 programs existed (measured; see release/WARNING_PROGRAM_MEMORY.txt).

## Contents of DAVEY_EXP1.BIN
- vubeatz modules: Tune, Transpose, Mute 1-4, Param Copy, LPF/HPF, Input Thru, Format, Double STOP, Step Move
- MUTE 1-8 (code at 0x75CF0)
- Sampling Mode (0x77620): original black "processing..." box kept; at the end the stock 3e19:0c22 (UI event 0x19, what
  stock pages call after long jobs) + a redraw, so KEEP / RETRY shows its text at once
- Zone chop screen (code at 0x74F00), VU-style, in TRIM: ZONE page, press F3 (ZONE) again
  - F1 BACK (restore the zones found on entry), F2 EVEN / CLEAN, F3 16 -> 8 -> 4 -> LAZY, F4 UNDO (LAZY), F5 APPLY, F6 DONE
  - LAZY: hit a pad to start the sound, tap pads at each slice; zones and waveform highlight follow every tap
  - St/End/Zone stay editable; APPLY opens the stock Edit window (SLICE SOUND, Create new program) = ZONE page F5
  - output: normal sounds + a normal drum program; 16 LEVELS untouched

Left out: REGIONS + VU lazy chop (16 LEVELS), overdub fix (REGIONS only), old blind zone lazy window, EB16 delay, label, date.

## How it was made safe
- `cov/coverage.py`: write watch over 0x741B0-0x7FFFF during 18 suites (incl. 24 programs, sampling, disk, tour)
  on the base; only never-written, empty bytes are allowed (list in make_exp.py FREE).
- `make_exp.py` refuses: any byte in program RAM, any byte outside FREE, overlaps, non-empty targets, wrong stock input;
  recomputes the checksum and checks the boot region.
- `test_exp.py`: restore by update, restore by boot-from-disk, chop, sampling (model + box + KEEP text), 24 programs then
  chop + restore, use-then-restore, MUTE 1-8 matrix, VU features vs base, twin screen comparison (76 screens identical).
- Every loop in the new code is bounded (<= 16 slices, 36-word backup); nothing waits on hardware.

## Not covered by the emulator
real flash write, LCD timing, real audio input, real tap timing. First real-unit test only with the recovery path ready.
