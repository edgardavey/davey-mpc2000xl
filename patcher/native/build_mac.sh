#!/bin/bash
# Build the macOS patcher binary (universal: arm64 + x86_64) into build/DaveyPatcher. The app bundle is assembled from it.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p build
for a in arm64 x86_64; do swiftc -O -target $a-apple-macos12 main.swift -o build/m_$a -framework Cocoa -framework WebKit; done
lipo -create build/m_arm64 build/m_x86_64 -output build/DaveyPatcher
lipo -info build/DaveyPatcher
