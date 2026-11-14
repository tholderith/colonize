#!/usr/bin/env bash
# Neon Foundry: Blender 4.0 Cycles (CPU, no denoiser, 2x supersample) objects + numpy periodic terrain + Pillow bloom/UI.
# Usage: ./build.sh [all|terrain|objects [names...]|ui]     (full build ~6-8 min on 4 shared cores)
set -euo pipefail
cd "$(dirname "$0")"
export NWORK="${NWORK:-/tmp/neon_work}"; mkdir -p "$NWORK"
what="${1:-all}"; shift || true
if [[ "$what" == all || "$what" == terrain ]]; then python3 terrain.py; fi
if [[ "$what" == all || "$what" == objects ]]; then
  blender -b --python render_objects.py -- "$@"      # NSPP=n overrides samples (default 64-72 per sprite)
  python3 post.py "$@"                                # emissive bloom, crop, premultiplied Lanczos 2x->1x, anchors
fi
if [[ "$what" == all || "$what" == ui ]]; then python3 ui.py; fi
python3 make_manifest.py
