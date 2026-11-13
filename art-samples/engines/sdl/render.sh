#!/usr/bin/env bash
# Usage: render.sh <path-to-style-dir> <out.png> [extra colonize_sdl args, e.g. --renderer opengl]
# Builds (incrementally) if needed, then renders the scene headlessly at 1920x1080.
# Works from any cwd; relative paths are resolved against the caller's cwd.
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: $0 <style-dir> <out.png> [extra args]" >&2
  exit 2
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="$HERE/build"
STYLE="$(cd "$1" && pwd)"
OUT_DIR="$(mkdir -p "$(dirname "$2")" && cd "$(dirname "$2")" && pwd)"
OUT="$OUT_DIR/$(basename "$2")"
shift 2

if [ ! -f "$BUILD/CMakeCache.txt" ]; then
  cmake -S "$HERE" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release >&2
fi
cmake --build "$BUILD" -j"$(nproc 2>/dev/null || echo 4)" >&2

exec "$BUILD/colonize_sdl" --style "$STYLE" --out "$OUT" "$@"
