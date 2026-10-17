#!/bin/bash
# Usage: tools/make_floppy.sh out.img file.wav [more files...]  (1.44 MB FAT12, files go in the root)
set -euo pipefail
out="$1"; shift
rm -f "$out"; dd if=/dev/zero of="$out" bs=1k count=1440 2>/dev/null
dev=$(hdiutil attach -nomount "$out" | awk '{print $1; exit}')
newfs_msdos -f 1440 -v MPCDISK "$dev" >/dev/null
hdiutil detach "$dev" >/dev/null
dev=$(hdiutil attach "$out" | awk '{print $1; exit}'); mnt=$(mount | awk -v d="$dev" '$1==d{print $3}')
cp "$@" "$mnt"/; sync; hdiutil detach "$dev" >/dev/null
echo "Wrote $out"
