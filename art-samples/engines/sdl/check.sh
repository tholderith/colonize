#!/usr/bin/env bash
# Usage: check.sh <style-dir> [out.png]
# Renders with this engine and with tools/render_ref.py, prints the mean absolute
# per-channel difference, and exits non-zero if it is >= 2.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
STYLE="$(cd "$1" && pwd)"
OUT="${2:-$ROOT/renders/sdl/$(basename "$STYLE").png}"
REF="$(mktemp --suffix=.png)"; trap 'rm -f "$REF"' EXIT
"$HERE/render.sh" "$STYLE" "$OUT"
python3 "$ROOT/tools/render_ref.py" "$STYLE" "$REF"
python3 - "$OUT" "$REF" <<'PY'
import sys, numpy as np
from PIL import Image
a, b = (np.asarray(Image.open(p).convert("RGB")).astype(int) for p in sys.argv[1:3])
d = np.abs(a - b); m = d.mean()
print(f"mean abs diff {m:.4f} (max {d.max()}) -> {'PASS' if m < 2 else 'FAIL'}")
sys.exit(0 if m < 2 else 1)
PY
