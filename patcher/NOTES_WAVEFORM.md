# Waveform visibility in the two lazy chop modes (report only, nothing changed)

Source: screens captured in the emulator (test_log/runs/zone_suite and regions_suite2, same on stable and DAVEY builds, so the REGIONS
behaviour is inherent to the vubeatz base: our base is byte-identical to his module output).

## REGIONS lazy chop (vubeatz style, TRIM > REGION EDIT, F3 -> LAZY)
- While chopping and walking the 14 regions: the waveform is visible and the active region is highlighted. OK.
- **After ZOOM on, region 1:** the waveform is drawn as a low, smeared wavy line (not a clean enlarged wave).
- **After ZOOM off:** the waveform line is **flat, no waveform** until you leave and re-enter the editor.
- **After CLEAN (back to one region):** **flat line, no waveform**, even though the region spans the whole sound.
  Screens: regions_suite2 #33 (zoom on), #34 (zoom off), #35 (clean).
- This is in the vubeatz code (REGIONS), not in anything we added.

## Zone lazy chop (our REMEDY-style, TRIM > ZONE > OPEN WINDOW > F6 LAZY)
- While the "Lazy chop" window is open the window covers almost the whole screen: **the waveform is hidden** behind it (only a sliver at the
  left edge shows). You tap blind and see the waveform only after DO IT.
- After DO IT the ZONE page shows the waveform with the chosen zone highlighted. OK.
- Cause: our window is the stock "Number of Zones" window frame, enlarged to hold the instructions and the tap counter.

## Options (to decide before any change)
1. Zone: shrink the window to two lines at the top (tap counter and soft keys) so the waveform shows below; needs a layout change in mod_zone_lazy.
2. Zone: leave the window and draw tick marks for taps on the waveform line after each tap.
3. REGIONS: find the redraw that ZOOM/CLEAN skip (the waveform draw routine) and call it after those two actions.
Each option touches UI code only (low points), but option 3 changes vubeatz code, so it would be a DAVEY-side fix module.
