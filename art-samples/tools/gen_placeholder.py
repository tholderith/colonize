"""Generates styles/placeholder: labelled boxes. Used by engine agents to test the contract."""
import json, os
from PIL import Image, ImageDraw, ImageFont
D = os.path.join(os.path.dirname(__file__), "..", "styles", "placeholder"); os.makedirs(D, exist_ok=True)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)

def diamond(w, h, col, name):
    im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    d.polygon([(w/2, 0), (w-1, h/2), (w/2, h-1), (0, h/2)], fill=col, outline=(0, 0, 0, 90))
    im.save(os.path.join(D, name))

def block(fw, fh, height, col, label, name):
    w, dh = 64 * (fw + fh), 32 * (fw + fh)
    im = Image.new("RGBA", (w, dh + height)); d = ImageDraw.Draw(im)
    cx = 64 * fh  # x of footprint's top corner... (left = fh*64 from top corner)
    topc = (cx, 0); right = (w, 32 * fw); bot = (64 * fh + 64 * fw - 64 * fw + 64*fw - 64*fh + 64*fh - 64*fw + 64*fw, dh)
    T = [(64 * fh, 0), (w, 32 * fw), (64 * fw, dh), (0, 32 * fh)]  # footprint diamond, y offset later
    up = lambda pts, dy: [(x, y + dy) for x, y in pts]
    base = up(T, height); roof = T
    dark = tuple(int(c * .6) for c in col[:3]) + (255,); mid = tuple(int(c * .8) for c in col[:3]) + (255,)
    d.polygon([base[3], base[2], roof[2], roof[3]], fill=dark)
    d.polygon([base[2], base[1], roof[1], roof[2]], fill=mid)
    d.polygon(roof, fill=col, outline=(0, 0, 0, 120))
    d.text((w/2, dh/2), label, font=font, fill="black", anchor="mm")
    im.save(os.path.join(D, name))
    return [64 * fw, dh + height]  # anchor: south corner

diamond(128, 64, (24, 70, 120, 255), "deep.png"); diamond(128, 64, (60, 140, 180, 255), "shallow.png")
diamond(128, 64, (225, 205, 140, 255), "sand.png"); diamond(128, 64, (90, 160, 70, 255), "grass_0.png")
diamond(128, 64, (100, 170, 75, 255), "grass_1.png"); diamond(128, 64, (150, 110, 70, 255), "road.png")
S = {"deep_water": {"files": ["deep.png"], "anchor": [64, 64]},
     "shallow_water": {"files": ["shallow.png"], "anchor": [64, 64]},
     "sand": {"files": ["sand.png"], "anchor": [64, 64]},
     "grass": {"files": ["grass_0.png", "grass_1.png"], "anchor": [64, 64]},
     "road": {"files": ["road.png"], "anchor": [64, 64]}}
spec = [("tree", 1, 1, 50, (40, 110, 40, 255)), ("rock", 1, 1, 14, (130, 130, 130, 255)),
        ("house", 1, 1, 40, (200, 120, 90, 255)), ("farmhouse", 1, 1, 36, (210, 170, 90, 255)),
        ("windmill", 1, 1, 90, (230, 230, 210, 255)), ("lumberjack", 1, 1, 30, (140, 90, 50, 255)),
        ("chapel", 2, 2, 70, (235, 235, 245, 255)), ("warehouse", 2, 2, 50, (180, 140, 100, 255)),
        ("wheat_field", 2, 2, 0, (230, 200, 60, 255)), ("pier", 1, 1, 0, (120, 85, 50, 255)),
        ("ship", 2, 2, 100, (110, 70, 40, 255)), ("cart", 1, 1, 12, (160, 100, 40, 255)),
        ("colonist", 1, 1, 24, (240, 60, 60, 255))]
for key, fw, fh, h, col in spec:
    a = block(fw, fh, h, col, key, f"{key}.png"); S[key] = {"files": [f"{key}.png"], "anchor": a}
S["wheat_field"]["flat"] = True; S["pier"]["flat"] = True
bar = Image.new("RGBA", (1920, 64), (30, 30, 30, 220)); ImageDraw.Draw(bar).text((20, 32), "TOP BAR   gold 1200   wood 40   tools 12   food 88   pop 64", font=big, fill="white", anchor="lm"); bar.save(os.path.join(D, "ui_topbar.png"))
pan = Image.new("RGBA", (360, 300), (30, 30, 30, 220)); ImageDraw.Draw(pan).text((20, 20), "INFO PANEL", font=big, fill="white"); pan.save(os.path.join(D, "ui_panel.png"))
json.dump({"name": "Placeholder", "background": "#18466e", "filter": "linear", "sprites": S,
           "overlays": [{"file": "ui_topbar.png", "pos": [0, 0], "anchor": [0, 0]},
                        {"file": "ui_panel.png", "pos": [24, 1056], "anchor": [0, 300]}]},
          open(os.path.join(D, "manifest.json"), "w"), indent=1)
