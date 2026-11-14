#!/usr/bin/env bash
# Realistic style: build everything (Blender 4.0 + Cycles CPU, numpy+Pillow in system python).
# Usage: ./build.sh            full build (~12 min on 4 cores)
#        ./build.sh terrain    only terrain textures+tiles;  ./build.sh objects [names];  ./build.sh ui
set -euo pipefail
cd "$(dirname "$0")"
export RWORK="${RWORK:-/tmp/realistic_work}"
mkdir -p "$RWORK"
what="${1:-all}"; shift || true
if [[ "$what" == all || "$what" == terrain ]]; then
  python3 terrain_tex.py                                   # lattice-periodic colour/height maps (numpy)
  TSPP="${TSPP:-48}" blender -b --python terrain.py        # 5 types x 16 variants, flat planes, Cycles
fi
if [[ "$what" == all || "$what" == objects ]]; then
  OSPP="${OSPP:-72}" blender -b --python objects.py -- "$@"   # buildings, trees, ship, props (shadow-catcher sprites)
fi
python3 post.py                                            # crop, premultiplied Lanczos 2x -> 1x, anchors
if [[ "$what" == all || "$what" == ui ]]; then python3 ui.py; fi
python3 make_manifest.py
