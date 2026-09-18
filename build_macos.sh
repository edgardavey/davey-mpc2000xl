#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
if [[ "${1:-}" == --help ]]; then
    echo 'Usage: bash build_macos.sh [additional MAME make arguments]'
    echo 'First: python3 tools/fetch_mame.py; install Xcode command-line tools, Python 3 and SDL2.'
    echo 'Optional: SDL_INSTALL_ROOT=/path/to/sdl2 JOBS=6'
    exit 0
fi
if [[ "$(uname -s)" != Darwin ]]; then
    echo 'This build wrapper targets macOS. See docs/ARCHITECTURE.md for the MAME target.' >&2
    exit 1
fi
MAME_DIR="$PROJECT_DIR/vendor/mame"
if [[ ! -f "$MAME_DIR/makefile" ]]; then
    echo 'Fetch the pinned source first: python3 tools/fetch_mame.py' >&2
    exit 1
fi
if [[ -z "${SDL_INSTALL_ROOT:-}" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo 'Set SDL_INSTALL_ROOT to your SDL2 installation or install SDL2 with Homebrew.' >&2
        exit 1
    fi
    SDL_INSTALL_ROOT="$(brew --prefix sdl2)"
fi
if [[ ! -f "$SDL_INSTALL_ROOT/include/SDL2/SDL.h" ]]; then
    echo 'SDL2 headers not found in SDL_INSTALL_ROOT.' >&2
    exit 1
fi
JOBS="${JOBS:-6}"
[[ "$JOBS" =~ ^[1-9][0-9]*$ ]] || { echo 'JOBS must be a positive integer.' >&2; exit 1; }
python3 "$PROJECT_DIR/tools/integrate_mame.py" --source "$MAME_DIR"
export CLANG_MODULE_CACHE_PATH="$PROJECT_DIR/build/clang-cache"
mkdir -p "$PROJECT_DIR/build/bin" "$CLANG_MODULE_CACHE_PATH"
cd "$MAME_DIR"
make -j "$JOBS" SUBTARGET=mpc2000xldiag SOURCES=src/mame/akai/mpc2000xldiag.cpp \
    OSD=sdl USE_LIBSDL=1 SDL_INSTALL_ROOT="$SDL_INSTALL_ROOT" USE_QTDEBUG=0 \
    NO_USE_PORTAUDIO=1 NO_USE_MIDI=1 NOWERROR=1 IGNORE_GIT=1 OPTIMIZE=1 SYMBOLS=0 "$@"
cp mpc2000xldiag "$PROJECT_DIR/build/bin/mpc2000xldiag.new"
mv "$PROJECT_DIR/build/bin/mpc2000xldiag.new" "$PROJECT_DIR/build/bin/mpc2000xldiag"
echo "Built: $PROJECT_DIR/build/bin/mpc2000xldiag"

python3 "$PROJECT_DIR/tools/package_macos.py"
