# MPC2000XL controls

Mappings below are implemented in source. Native MAIN boot, MAIN/Open Window,
Next Sequence, Track Mute and bank B within Track Mute were exercised on macOS.
Full control coverage remains unverified; see STATUS.md. All controls are clickable.

| Control | Keyboard |
| --- | --- |
| Soft keys | F1–F6 |
| MAIN / OPEN WINDOW | M or Home / H or End |
| Cursor | Arrow keys |
| Data wheel − / + | `-` / `=`; keypad minus/plus |
| Digits / ENTER | 0–9 / Return; numeric keypad equivalents |
| SHIFT | Hold either Shift; click panel Shift to toggle latch |
| Modes | Shift + 1–9: Song, Misc, Load, Sample, Trim, Program, Mixer, Other, MIDI/Sync |
| AFTER / TAP TEMPO | O / B |
| UNDO / ERASE | Delete / backslash |
| STEP backward / forward | semicolon / apostrophe |
| GO TO / BAR backward / forward | G / Page Up / Page Down |
| REC / OVER DUB | J or F10 / K or F11 |
| STOP / PLAY / PLAY START | Backspace / Space / P or F12 |
| Bank A | N or F7 |
| Banks B / C / D | F13 / F14 / F15; mouse on compact keyboards |
| FULL LEVEL / 16 LEVELS | comma or F8 / period or F9 |
| TRACK MUTE / NEXT SEQUENCE | F16 / F17; mouse on compact keyboards |
| Note Variation | Drag fader; `[` / `]`, Control+bracket for endpoints, L for centre |

Pads from bottom row to top: `Z X C V`, `A S D F`, `Q W E R`, `T Y U I`.
Pad velocity is fixed; pressure sensitivity is not modeled.

Right-click REC, OVER DUB, ERASE, TAP or GO TO to latch it while using another
control; right-click again to release. Left-click is a momentary press. MAME's
UI/menu mode can be toggled with Scroll Lock; the launcher starts with UI hotkeys
inactive so keyboard shortcuts reach the panel. macOS may reserve function keys.

Button tint shows host input; the separate red LEDs follow guest HC259 output
latches. Main Volume and Rec Gain knobs are decorative. Audio is disabled.
