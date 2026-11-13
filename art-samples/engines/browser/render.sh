#!/usr/bin/env bash
# Usage: render.sh <path-to-style-dir> <out.png>
# Builds dist/ if missing or stale, serves it with the style folder, screenshots a 1920x1080 PNG.
set -euo pipefail
[ $# -eq 2 ] || { echo "usage: $0 <style-dir> <out.png>" >&2; exit 2; }
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$HERE/build.sh" >&2
exec node "$HERE/scripts/render.cjs" "$1" "$2"  # paths resolved against the caller's cwd
