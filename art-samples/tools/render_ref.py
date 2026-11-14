"""Reference renderer: python3 tools/render_ref.py styles/<style> out.png
Implements SPEC.md exactly; every engine must produce the same picture."""
import json, os, sys
from PIL import Image

FOOT = {"warehouse": (2, 2), "wheat_field": (2, 2), "ship": (2, 2), "chapel": (2, 2)}

def top(x, y): return 960 + (x - y) * 64, -72 + (x + y) * 32
def south(x, y):
    sx, sy = top(x, y); return sx, sy + 64

def main(style_dir, out):
    m = json.load(open(os.path.join(style_dir, "manifest.json")))
    lay = json.load(open(os.path.join(os.path.dirname(__file__), "..", "scene", "layout.json")))
    cache = {}
    def img(f):
        if f not in cache: cache[f] = Image.open(os.path.join(style_dir, f)).convert("RGBA")
        return cache[f]
    canvas = Image.new("RGBA", (1920, 1080), m["background"])
    def blit(im, x, y):  # true alpha-over compositing, tolerant of off-canvas offsets
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); layer.paste(im, (x, y))
        canvas.alpha_composite(layer)
    def draw(key, x, y, p):
        s = m["sprites"][key]; files = s["files"]
        im = img(files[(x * 7 + y * 13) % len(files)])
        blit(im, p[0] - s["anchor"][0], p[1] - s["anchor"][1])
    legend = lay["terrain_legend"]
    tiles = [(x, y) for y in range(lay["height"]) for x in range(lay["width"])]
    for x, y in sorted(tiles, key=lambda t: (t[0] + t[1], t[0])):
        draw(legend[lay["terrain"][y][x]], x, y, south(x, y))
    # 2b. underlays: world-space images (e.g. a continuous baked terrain), drawn over tiles, under objects
    for ul in m.get("underlays", []):
        im = img(ul["file"]); a = ul.get("anchor", [0, 0])
        blit(im, ul["pos"][0] - a[0], ul["pos"][1] - a[1])
    objs = list(enumerate(lay["objects"]))
    def anchor_tile(o):
        fw, fh = FOOT.get(o["sprite"], (1, 1)); return o["x"] + fw - 1, o["y"] + fh - 1
    flat = [o for i, o in objs if m["sprites"][o["sprite"]].get("flat")]
    rest = [(i, o) for i, o in objs if not m["sprites"][o["sprite"]].get("flat")]
    for o in flat: draw(o["sprite"], o["x"], o["y"], south(*anchor_tile(o)))
    rest.sort(key=lambda io: (sum(anchor_tile(io[1])), anchor_tile(io[1])[0], io[0]))
    for _, o in rest: draw(o["sprite"], o["x"], o["y"], south(*anchor_tile(o)))
    for ov in m.get("overlays", []):
        im = img(ov["file"]); a = ov.get("anchor", [0, 0])
        blit(im, ov["pos"][0] - a[0], ov["pos"][1] - a[1])
    canvas.convert("RGB").save(out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
