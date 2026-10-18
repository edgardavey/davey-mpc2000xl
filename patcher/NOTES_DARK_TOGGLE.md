# Dark mode as a runtime option that is remembered (analysis only, nothing built)

## What is established
- The LCD data goes through four loops in the refresh routine (0x1ac2a, 0x1ac6a, 0x1acbd, 0x1ad07). Inversion is one instruction (`not al`,
  bytes F6 D0) per byte in each loop. Stock cost plus about 3 clocks per byte.
- The code runs from RAM, so those instruction bytes can be changed while the machine is running. A **toggle** can therefore be: write
  `F6 D0` (dark) or `90 90` (two NOPs, normal) into the four sites, then refresh the screen. That costs nothing per pixel and cannot slow the
  refresh. (Design only; it has not been built or tested.)
- Writing 8 bytes while the refresh runs must happen with interrupts off or from the main loop, never half-way through a loop iteration.

## What is NOT established
- **Where the OS keeps persistent settings and whether the display contrast survives a power cycle.** The OS has an INIT page ("Initialize ALL
  PARAMETERS") that copies default tables (0x2274 -> ds:0x710, 256 bytes; 0x2374 -> ds:0x10, 1,792 bytes). I did not find a code path that
  saves them to non-volatile storage, and the emulator has no non-volatile memory, so persistence cannot be tested here.
- A forum remark says settings live "on the flash"; that is not verified.

## Designs, safest first
1. **Default chosen when you build (patcher option: "dark by default" or "light by default") plus a runtime toggle that is not remembered.**
   No dependence on unknown storage. At power-on the unit comes up in the build's default; the toggle changes it until power-off.
2. **Toggle control:** an unused soft key on OTHER > VER. (a page that runs only when you are on it, so it adds no cost elsewhere).
3. **True persistence** only after the OS's own settings store is located and shown, in the emulator, to survive INIT and a simulated power cycle.
   Until then it is not offered.

## Question for you (decides option 3)
Does your MPC remember the **display contrast** after you switch it off and on? If yes, the machine already has a place that survives power-off
and I can look for it.

## Gates before any build
The same release gate as every module (boot, update flow to erase, restore by update, restore by boot-from-disk), plus: toggling 200 times
without a missed refresh, toggling while the screen is changing, toggling during LOAD/SAVE, and an instruction count of the refresh loops equal to stock (+1 per byte).
