#!/usr/bin/env bash
# Cinematic style: full build (Blender 4.0 Cycles CPU + numpy/scipy/Pillow).  ~15-18 min on 4 cores.
#   ./build.sh            everything
#   ./build.sh terrain    fields + terrain underlay only;  ./build.sh objects [names];  ./build.sh ui
# env: TSPP (terrain samples, default 40)  OSPP (sprite samples, default 56)  CWORK (scratch dir)
set -euo pipefail
cd "$(dirname "$0")"
export CWORK="${CWORK:-/tmp/cin_work}"; mkdir -p "$CWORK"
what="${1:-all}"; shift || true
if [[ "$what" == all || "$what" == terrain ]]; then
  python3 fields.py                                            # continuous fields: coast SDF, height, depth, foam, ground albedo
  TSPP="${TSPP:-40}" blender -b --python terrain_render.py     # ONE terrain+water render, exact game camera, 3840x2160
  python3 post_terrain.py                                      # Lanczos 2x->1x, bloom, grade -> terrain_full.png (+ fallback tiles)
fi
if [[ "$what" == all || "$what" == objects ]]; then
  OSPP="${OSPP:-56}" blender -b --python objects.py -- "$@"    # buildings/trees/ship/props with shadow-catcher
  python3 post.py                                              # crop, premultiplied Lanczos, grade, anchors
fi
if [[ "$what" == all || "$what" == ui ]]; then
  ISPP="${ISPP:-64}" blender -b --python icons.py              # resource icons (Blender)
  python3 ui.py                                                # top bar, info panel, haze/vignette grade overlay
fi
python3 make_manifest.py
