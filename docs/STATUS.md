# Project status

The macOS Apple Silicon development build boots stock OS 1.20 from its native
reset vector to the guest MAIN screen. The LCD displays pixels written by the
guest firmware, and panel LEDs follow modeled hardware output latches.

Observed controls include MAIN/Open Window from the keyboard, and Open Window,
Next Sequence, Track Mute and bank B by mouse. Bank B in Track Mute selects
tracks 17–32 and updates the bank LED. Other bank contexts and complete input
coverage have not been verified.

## Limitations

- Audio is disabled. Sampling, playback and sonic accuracy are unverified.
- Floppy loading/saving, save states and full reset are unverified.
- The panel MCU is approximated with serial messages and fixed pad velocity.
- Boot flash is read-only; flash command emulation and firmware updates are unsupported.
- SCSI/ATA buses have no attached virtual disks. MIDI I/O is not implemented.
- Timer, LCD and CPU timing are approximate; physical hardware behavior is unverified.
- The loader accepts only the documented stock BIN identity.

## Platform coverage

macOS Apple Silicon has development-build runtime coverage. A clean-checkout
release build, other macOS architectures, Windows and Linux have not been verified.
Windows launch scripts and the file picker are provided, but their operation
requires validation on Windows with the dedicated SDL executable.

The source audit, syntax checks and synthetic host-side tests are independent
of guest execution. Passing them does not establish emulator compatibility.
