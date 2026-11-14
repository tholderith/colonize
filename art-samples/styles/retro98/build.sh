#!/usr/bin/env bash
# Pre-rendered '98 style: regenerate everything. Needs Blender 4.0 (Cycles, CPU), python3 + numpy + Pillow.
# ./build.sh            full build (~1.5 min)       ./build.sh sprites [name-prefixes]   re-render just those sprites
set -euo pipefail
cd "$(dirname "$0")/src"
export R98WORK="${R98WORK:-/tmp/retro98_work}"; mkdir -p "$R98WORK/raw"
what="${1:-all}"; shift || true
python3 palette.py                                   # writes palette_preview.png (the 256-colour palette)
if [[ "$what" == all || "$what" == terrain ]]; then python3 terrain.py; fi          # numpy: periodic procedural tiles, Bayer dithered
if [[ "$what" == all || "$what" == sprites ]]; then blender -b --python render.py -- "$@"; fi   # Cycles: object pass + shadow-catcher pass
if [[ "$what" != terrain && "$what" != ui ]]; then python3 post.py "$@"; fi         # Lanczos 2x->1x, binary alpha, Floyd-Steinberg to palette, 2x nearest
if [[ "$what" == all || "$what" == ui ]]; then python3 ui.py; fi
python3 make_manifest.py
