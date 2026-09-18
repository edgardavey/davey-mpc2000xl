#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    echo 'Python 3.9 or newer is required. See README.md.' >&2
    exit 1
fi
if [[ $# -eq 0 ]]; then
    exec python3 "$PROJECT_DIR/run.py" --auto --remember
else
    exec python3 "$PROJECT_DIR/run.py" "$@"
fi
