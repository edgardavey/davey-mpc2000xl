# Your own system files

Place `MPC2KXL.BIN` (stock OS 1.20, full 512 KiB BIN) in this folder, then double-click
**Launch Emulator.command** on macOS or **Launch Emulator.cmd** on Windows.
Filenames are matched without regard to case. A data floppy is optional and selected with `--disk` or `--choose-disk`.

No system files are included or downloaded. Renaming an incompatible file does
not make it compatible; the original identity checks still apply.
The launcher uses private session copies and leaves your originals unchanged.

Everything in this folder except this README is ignored by Git. Do not force-add
system files, disks or samples. See the main [README](../README.md) for the file
picker, command-line paths, other folders and platform build requirements.
