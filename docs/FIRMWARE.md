# User-supplied MPC2000XL firmware

The supported input is a complete, unmodified MPC2000XL OS 1.20 image.
It is supplied externally by the user and is never bundled or downloaded.

| Property | Value |
| --- | --- |
| Usual filename | `MPC2KXL.BIN` |
| Size | 524288 bytes (`0x80000`) |
| SHA-256 | `100e3375b45072c209ffa2b1dbaecbf740c8c4ea29162827ac11cc6bf9cc7bab` |
| SHA-1 | `382be688972fe3d85caeca99abff4b6c391347fb` |
| CRC32 | `c082f188` |
| Main OS checksum | `0x5ACB` at file `0x77FFE` |
| Reset vector | file `0x7FFF0`, far jump to `FC00:0400` |

The checksum is the sum of little-endian 16-bit words in `[0, 0x77FFE)`,
modulo 65536. The boot area is `[0x78000, 0x80000)`.
This exact image's SHA-1/CRC32 match the pinned upstream MAME registration
`mpc2000xl_120.bin`. Internal `1.14c` development strings do not identify it
as release 1.14.

The launcher checks SHA-256, checksum and reset vector. The C++ quickloader
independently checks size, SHA-1 and checksum when invoked without the launcher.
Other releases, shortened update payloads, modified BINs and Classic EXE/SYS
files are rejected. Support is limited to the identity documented above.

The BIOS executes normally from ROM. Host code does not copy the OS into RAM,
preconfigure V53 XA page tables, or forge an OS initialization state. The boot
ROM's own routines perform those steps. Native boot to MAIN was observed in
the macOS XL build with the exact supported stock image.

The panel MCU's separate ROM is not required: the driver approximates panel
events as serial messages. Boot flash is mapped read-only as in upstream MAME;
flash programming and manufacturer-ID command behavior are not implemented.

Optional data floppies: HFE v1 (`HXCPICFE`) or raw 1.44 MB IMG. Header/size checks
do not verify filesystems or sample compatibility. No boot disk is required
by the loader contract. All guest writes target a fresh session copy, never
the selected source. Keep session copies and RAM dumps out of version control.
