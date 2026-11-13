#!/usr/bin/env bash
# Usage: render.sh <path-to-style-dir> <out.png>
# Renders art-samples/scene/layout.json with the given style via Godot (Compatibility/OpenGL renderer under Xvfb).
# Godot is taken from $GODOT, else /home/user/tools/godot (or $GODOT_DIR), else downloaded there.
set -euo pipefail
[ $# -eq 2 ] || { echo "usage: $0 <style-dir> <out.png>" >&2; exit 2; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STYLE="$(realpath "$1")"
OUT="$(realpath -m "$2")"
[ -f "$STYLE/manifest.json" ] || { echo "no manifest.json in $STYLE" >&2; exit 2; }
mkdir -p "$(dirname "$OUT")"

GODOT_VERSION="${GODOT_VERSION:-4.7.2}"
GODOT_DIR="${GODOT_DIR:-/home/user/tools/godot}"
if [ -z "${GODOT:-}" ]; then
  GODOT="$(ls -1 "$GODOT_DIR"/Godot_v4*_linux.x86_64 2>/dev/null | sort -V | tail -n1 || true)"
  if [ -z "$GODOT" ]; then
    echo "Godot not found; downloading $GODOT_VERSION to $GODOT_DIR ..." >&2
    mkdir -p "$GODOT_DIR"
    curl -fsSL -o "$GODOT_DIR/godot.zip" \
      "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"
    (cd "$GODOT_DIR" && unzip -oq godot.zip && rm -f godot.zip)
    GODOT="$GODOT_DIR/Godot_v${GODOT_VERSION}-stable_linux.x86_64"
    chmod +x "$GODOT"
  fi
fi

rm -f "$OUT"
CMD=("$GODOT" --path "$HERE" --rendering-driver opengl3 --audio-driver Dummy --resolution 1920x1080
     -- --style "$STYLE" --out "$OUT")
if [ -n "${DISPLAY:-}" ] && [ -z "${FORCE_XVFB:-}" ]; then
  "${CMD[@]}"
else
  xvfb-run -a -s "-screen 0 1920x1080x24" "${CMD[@]}"
fi
[ -s "$OUT" ] || { echo "render failed: $OUT not written" >&2; exit 1; }
