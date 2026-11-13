#!/usr/bin/env bash
# Usage: render.sh <path-to-style-dir> <out.png>
# Builds the Bevy renderer if needed (cargo is incremental) and renders the scene
# headlessly (offscreen Vulkan via Mesa lavapipe; no X server / window needed).
set -euo pipefail
if [ $# -ne 2 ]; then echo "usage: $0 <style-dir> <out.png>" >&2; exit 2; fi
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STYLE="$(cd "$1" && pwd)"
OUT="$2"; case "$OUT" in /*) ;; *) OUT="$PWD/$OUT";; esac
LAYOUT="$HERE/../../scene/layout.json"
export CARGO_TARGET_DIR="$HERE/target"
# Bevy 0.20.1 declares rust-version 1.97.1; it builds fine on the installed 1.97.0.
cargo build --quiet --ignore-rust-version --manifest-path "$HERE/Cargo.toml"
# Software Vulkan (lavapipe) works headless; override with WGPU_BACKEND=gl if desired.
export WGPU_BACKEND="${WGPU_BACKEND:-vulkan}"
exec "$CARGO_TARGET_DIR/debug/colonize_bevy_render" --style "$STYLE" --out "$OUT" --layout "$LAYOUT"
