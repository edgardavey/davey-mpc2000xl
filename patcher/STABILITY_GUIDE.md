# Why more features can make an MPC2000XL unstable, and the rules we follow

Golden rule: **every build must be restorable, and that is tested for every build before it is delivered.**
Nothing else in this document outranks it.

Labels used below: **measured** = observed in the emulator or by running code here; **derived** = follows from numbers in the OS code;
**suspected** = plausible, flagged by review, not confirmed; **unknown** = can only be settled on real hardware.

---------------------------------------------------------------------------------------------------

## 1. The machine in numbers (derived from the OS and the emulator driver)

| Resource | Value | Consequence |
|---|---|---|
| CPU | NEC V53A, 32 MHz crystal, 16 MHz core (one clock = 62.5 ns) | A 16-bit multiply is tens of clocks, a far call+return about 60. Per-event code adds up fast. |
| Sequencer tick | 96 PPQN: 192 ticks/s at 120 BPM (5.2 ms), 480 ticks/s at 300 BPM (2.1 ms) | Everything that runs per tick or per note must finish well inside one tick, or timing slips. |
| Front panel link | 31,250 baud serial, one byte every 320 microseconds | Interrupts blocked for more than about 300 microseconds can drop a key, pad or wheel byte. |
| LCD refresh | 248 x 60 pixels, 1,860 data bytes per full refresh, each one a port write | Any per-byte cost is multiplied by about 1,900. |
| OS image | 512 KiB file; 0x00000-0x77FFF (480 KiB) is code and data copied to RAM; 0x78000-0x7FFFF is the boot program | Only the first 480 KiB can hold patches. The boot region must never change. |
| Free space in the image | Empty in the FILE is not free in RAM: 0x65AE0-0x741AF holds the 24 program slots (0x99E bytes each), so 0x70000-0x741AF is overwritten once 18+ programs exist. Real free space = never written at runtime (measured by exp_reloc/cov over 18 suites incl. 24 programs) and empty after the VU base: ~10 KB in 0x749A4-0x77FFD without REGIONS. | Space is finite; every module needs a measured-free home. The patcher refuses any byte in 0x70000-0x741AF. |
| RAM and flash | Code runs from RAM. The flash holds the file. "Copy Operating System" writes the pristine file (measured: byte identical even after using Sampling Mode). | Runtime state written into the code segment does not reach flash. |

## 2. The ways a patched OS goes unstable

### 2.1 Time: too much work in the hot paths (measured once, in anger)
The OS is a main loop plus interrupts (sequencer tick, panel serial, DMA, LCD refresh). Anything we add to a path that runs per note, per
voice, per pad hit, per sequencer step or per LCD byte is multiplied by how often that path runs.

Our own incident is the clean example (**measured**):
- The first dark-mode build called a stub for every LCD pixel byte, about 1,900 extra far calls per refresh (roughly +100,000 clocks, about 6-8 ms).
- With 720 stub calls (one LCD half) the OS update screen still worked; with 1,200 (the other half) it did not. In the emulator DO IT did
  nothing for 200 seconds. A rewrite that inverts the same pixels in place, at stock cost, works.
- Our reading (**derived, consistent with the measurements, not proven**): the refresh grew from about 3.5 ms to well over a tick period and
  starved something the update step waits for.

How "too many features" turns into this: each feature that hooks a hot path adds a little. One is invisible, eight together can push the worst
case (many voices, dense sequence, screen redraw, disk access at the same time) over a limit. That is what the **points** estimate:
2 = per note/voice/pad/LCD/record, 1 = disk or edit paths, 0 = limits/screens/text.

### 2.2 Interrupts disabled for too long (derived)
Disk DMA (floppy), the panel serial byte (every 320 us) and the sample-RAM DMA all need prompt service. Code that runs with interrupts off
(`cli`) or spends a long time inside an interrupt handler can overrun the floppy controller, lose panel bytes (stuck or missing keys, missed
pads) or lose MIDI bytes. The Sampling Mode resample loop calls OS DMA routines with interrupts off for each 16-word chunk (**suspected**
to be up to a few hundred microseconds per call; not measured on hardware).

### 2.3 Memory: where code and state live
- Patch code goes into free space in the image. Two modules must never use the same bytes (the patcher keeps an ownership map and refuses overlaps).
- State kept inside the code segment is fine for the running machine (RAM copy) but must never be needed in the file.
- The area 0x78000-0x7FFFF is used by the stock memory test and by a DMA bounce buffer at 0x7F000; vubeatz keeps state at 0x78000-0x78F2F.
  A reviewer flagged that the stock memory test (called from 0x54EFC) might clobber that state if it runs after initialisation (**suspected**,
  to be confirmed with a watchpoint). We do not add anything there.
- The stack is small and shared with interrupts: each far call costs 4 bytes, nested interrupts add more. Stubs must be balanced on every path.

### 2.3b Measured incident: code in program memory (2026-10-16)
DAVEY code placed at 0x70100-0x706A0 (zone lazy chop, MUTE 1-8, the version label) was wiped when the 18th program was
created; OTHER > VER. then froze the unit (power cycle recovers, flash untouched). VU's own LPF/HPF boot loop also rewrites
byte +0x2B of every program pad record, which corrupted code placed there. Fixed by relocating everything into measured-free RAM
and adding a hard guard to make_exp.py and both patcher engines.

### 2.4 Collisions between modules
Two modules that patch the same routine only work if their interaction is defined (vubeatz handles this with a **rules** table: the first
matching variant wins, which is order-dependent). A selection nobody tested can contain a pair that was never run together.
DAVEY modules were measured not to overlap each other or any vubeatz module, except MUTE 1-8, which intentionally builds on Mute and Regions
and carries conditions for that.

### 2.4b What only real hardware can show (unknown)
The emulator has no flash chip, ignores the LCD ready flag (`lcd_status` returns 0 so the wait branch never runs), has no audio input, and its
timer clock is an approximation. So these cannot be tested here: the real flash write, LCD timing, real input, real tempo-clock calibration
(zone lazy chop positions), and the true duration of interrupt-off sections.

### 2.5 The boot and update chain
- The boot program (top 32 KB of the file) identifies the flash chip, checks for a valid executable header, then runs the OS from flash.
  If there is no valid OS it asks for a disk. A key code at power-on can force that loader.
- The OS update screen is part of the **running** OS. A build that cannot run its own update screen cannot update itself; recovery then needs
  the boot loader, the recovery ROM chip, or a programmer.
- The checksum word (0x77FFE) and the boot region must be right. The OS update does not verify the checksum before erasing (**measured**:
  an OS file with a wrong checksum still reached the flash-erase step), so a wrong checksum is not caught for you.

## 3. Rules we follow (checklist for every change)

1. **Restorable or it does not ship.** Before any file is called finished, the release gate (section 4) must pass for that exact file.
2. **Never add per-byte, per-pixel, per-event or per-refresh cost** unless it is fewer instructions than it replaces. Prefer in-place rewrites to calls.
3. **No far calls in hot paths.** If unavoidable, count clocks and show the number.
4. **Do not disable interrupts** for longer than about 100 microseconds; split work into chunks.
5. **Keep state out of RAM we do not own.** Document every byte range a module touches; the data file asserts the old bytes.
6. **One owner per byte.** The patcher fails on overlap; new modules are checked against the ownership map.
7. **Budget points.** Stay at or below the tested-set marker unless the extra module has its own gate results.
8. **Experimental flag** for anything touching the refresh path, boot path, flash, or interrupt handling; it needs a typed acknowledgement.
9. **Test the update screen and the restore path in the emulator on the exact file**, every time, not "a similar build".
10. **Say what was not tested.** The report states emulator-only and lists real-hardware items.
11. **Never claim a build is safe.** Only "passed these gates".

## 4. The release gate (automated; patcher/test_matrix.py and patcher/test_features.py)

For every selectable module alone and for every named set (recommended, vubeatz base, light, everything, recommended+dark, none):
1. Build with the engine; verify input hash, patch old-bytes, checksum, boot region, size.
2. **Boot** to the main page; screens equal the untouched original (inverted for dark).
3. **Version page** shows the expected text.
4. **Restore by update:** LOAD, select the ORIGINAL MPC2KXL.BIN, DO IT, DO IT: must reach "Loading" and "Flash block 1-7 erase".
5. **Restore by boot-from-disk:** force the boot loader with the ORIGINAL file on disk: must show "Loading:MPC2KXL.BIN", start the original OS,
   and every later screen equals the original (never inverted): proof that a build can be replaced.
6. Feature suites per module (zone chop, REGIONS with lazy and overdub fix, MUTE matrix, tune/transpose/ALL/double STOP, dark inversion,
   Sampling Mode on both channels with the KEEP/RETRY text check).
7. Browser engine equals the Python engine on every selection.
8. **Use, then restore (test_restore_after_use.py):** exercise the feature with a real suite (zone chop, REGIONS, MUTE, sequencer, Sampling Mode
   SP1200 and S900, dark pages), then run the update flow with the ORIGINAL file: prompt, Loading, Flash block erase must equal the original's.

Things the gate cannot do, and the human step that covers them: test on the real unit with a **working recovery path ready**. For this owner the
proven path is the hardware recovery ROM chip. The boot loader (REC + OVER DUB) reads a floppy or SCSI ID 0 and did not find their flash card, so it
is NOT counted as their safety net.
