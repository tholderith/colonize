#!/usr/bin/env bash
# Neon Foundry art pipeline: Blender 4.0 Cycles CPU (no denoiser) buildings (base + additive glow layer) + numpy terrain + manifest + contact sheet.
# Usage: art/build.sh [all|terrain|objects [names,comma,sep]|icons [names]|manifest|contact]   NSPP=n overrides base samples (default 64).
set -euo pipefail
cd "$(dirname "$0")"
export NWORK="${NWORK:-/tmp/colonize_art_work}"; mkdir -p "$NWORK" out ../public/assets
what="${1:-all}"; shift || true
if [[ "$what" == all || "$what" == terrain ]]; then python3 terrain.py; fi
if [[ "$what" == all || "$what" == objects ]]; then
  if [[ "$what" == all ]]; then rm -rf "$NWORK/raw" out/buildings_meta.json; fi
  blender -b --python render_objects.py -- "$@" 2>&1 | grep -E "RAW|FAILED|Error|Traceback" || true
  python3 post.py
fi
if [[ "$what" == all || "$what" == icons ]]; then blender -b --python icons.py -- "$@" 2>&1 | grep -E "ICON|FAILED|Error|Traceback|line" || true; python3 icons_post.py; fi
python3 make_manifest.py
python3 contact.py
