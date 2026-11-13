#!/usr/bin/env bash
# Produces site/: a self-contained static website (viewer + every style with a manifest + layout).
#   site/index.html, site/assets/*.js      <- dist/ (relative URLs, vite base './')
#   site/layout.json                       <- art-samples/scene/layout.json
#   site/styles/index.json                 <- [{"name": "<folder>", "title": "<manifest name>"}, ...]
#   site/styles/<name>/manifest.json+PNGs  <- art-samples/styles/<name>/
# Host site/ anywhere (any sub-path); open index.html?style=<name>.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ART="$(cd "$HERE/../.." && pwd)"
SITE="$HERE/site"
"$HERE/build.sh"
rm -rf "$SITE"
cp -r "$HERE/dist" "$SITE"
cp "$ART/scene/layout.json" "$SITE/layout.json"
mkdir -p "$SITE/styles"
for d in "$ART"/styles/*/; do
  [ -f "$d/manifest.json" ] || continue
  cp -r "$d" "$SITE/styles/$(basename "$d")"
done
node -e '
const fs = require("fs"), path = require("path"), dir = process.argv[1];
const order = ["painted", "lowpoly", "pixel", "parchment", "placeholder"];
const rank = (n) => (order.indexOf(n) + 1 || 99);
const styles = fs.readdirSync(dir).filter((n) => fs.existsSync(path.join(dir, n, "manifest.json")))
  .sort((a, b) => rank(a) - rank(b) || a.localeCompare(b))
  .map((name) => ({ name, title: JSON.parse(fs.readFileSync(path.join(dir, name, "manifest.json"), "utf8")).name || name }));
fs.writeFileSync(path.join(dir, "index.json"), JSON.stringify(styles, null, 1));
console.log("styles:", styles.map((s) => s.name).join(", "));
' "$SITE/styles"
echo "site ready: $SITE ($(du -sh "$SITE" | cut -f1)). Preview: node $HERE/scripts/static-server.cjs $SITE 8080"
