"""Contact sheet (art/out/contact.png): every tile + every building (base | glow | composed) + a composed test patch."""
import json, os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "public", "assets")
man = json.load(open(os.path.join(OUT, 'manifest.json')))
img = lambda p: Image.open(os.path.join(OUT, p)).convert('RGBA')
BG = (12, 16, 24, 255)

def add_glow(canvas, g, pos):
    """additive: dst += rgb * alpha (canvas is an RGBA PIL image drawn on)."""
    x, y = pos; w, h = g.size
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, canvas.width), min(y + h, canvas.height)
    if x1 <= x0 or y1 <= y0: return
    ga = np.asarray(g).astype('float32') / 255; ga = ga[y0 - y:y1 - y, x0 - x:x1 - x]
    dst = np.asarray(canvas).astype('float32') / 255
    dst[y0:y1, x0:x1, :3] = np.clip(dst[y0:y1, x0:x1, :3] + ga[..., :3] * ga[..., 3:4], 0, 1)
    canvas.paste(Image.fromarray((dst * 255 + 0.5).astype('uint8'), 'RGBA'))

def put_tile(c, key, gx, gy, ox, oy):
    t = man['tiles'][key]; im = img(t['file']); sx = ox + (gx - gy) * 64; sy = oy + (gx + gy) * 32
    c.alpha_composite(im, (sx - t['anchor'][0], sy - t['anchor'][1]))

def patch():
    N = 11; ox, oy = 64 * N // 2 + 64, 90
    c = Image.new('RGBA', (64 * N + 140, 32 * N * 2 + 220), BG)
    land = set()
    for y in range(2, 9):
        for x in range(2, 9): land.add((x, y))
    land -= {(8, 2), (8, 3), (7, 2)}             # inlet (concave corners)
    land -= {(2, 8)}                              # convex notch
    road = {(x, 5) for x in range(2, 9)} | {(5, y) for y in range(2, 9)}
    water = lambda p: p not in land
    shallow = lambda p: any(abs(p[0] - a) <= 1 and abs(p[1] - b) <= 1 for a, b in land)
    for s in range(0, 2 * N):
        for gx in range(N):
            gy = s - gx
            if not (0 <= gy < N): continue
            p = (gx, gy)
            if p in land:
                if p in road and not any(water(q) for q in ((gx, gy - 1), (gx + 1, gy), (gx, gy + 1), (gx - 1, gy))): key = 'road'
                else:
                    m = sum(b for b, q in ((1, (gx, gy - 1)), (2, (gx + 1, gy)), (4, (gx, gy + 1)), (8, (gx - 1, gy))) if water(q))
                    key = 'land' if (m == 0 and p not in road) else 'shore_%d' % m
                    if p in road and m == 0: key = 'road'
            else: key = 'shallow_water' if shallow(p) else 'deep_water'
            put_tile(c, key, gx, gy, ox, oy)
    # buildings: footprint south corner = tile (gx+fw-1, gy+fh-1) south corner
    for key, gx, gy, fw in (('smelter', 3, 3, 2), ('depot', 6, 6, 2), ('pod_house', 4, 7, 1)):
        b = man['buildings'][key]; bx = gx + fw - 1; by = gy + fw - 1
        sx = ox + (bx - by) * 64; sy = oy + (bx + by) * 32 + 32
        c.alpha_composite(img(b['file']), (sx - b['anchor'][0], sy - b['anchor'][1]))
        add_glow(c, img(b['glow']), (sx - b['anchor'][0], sy - b['anchor'][1]))
    return c

def sheet():
    p = patch(); W = max(1500, p.width + 20)
    keys = list(man['tiles']); bk = list(man['buildings'])
    rows_h = 80 + 20 + 2 * 90 + 20
    sh = Image.new('RGBA', (W, 40 + 3 * 96 + 330 + p.height), BG); d = ImageDraw.Draw(sh)
    d.text((10, 6), 'TILES (anchor = south corner)', fill=(200, 220, 255, 255))
    for i, k in enumerate(keys):
        x = 10 + (i % 10) * 142; y = 24 + (i // 10) * 96
        sh.alpha_composite(img(man['tiles'][k]['file']), (x, y)); d.text((x, y + 74 + 8), k, fill=(180, 190, 200, 255))
    y0 = 24 + 3 * 96 + 6; d.text((10, y0), 'BUILDINGS: base | glow (alpha=lum) | composed (base + additive glow)', fill=(200, 220, 255, 255))
    x = 10; y = y0 + 18; rowh = 0
    for k in bk:
        b = man['buildings'][k]; bi = img(b['file']); gi = img(b['glow']); w, h = bi.size
        if x + 3 * (w + 6) > W: x = 10; y += rowh + 20; rowh = 0
        sh.alpha_composite(bi, (x, y))
        gtile = Image.new('RGBA', (w, h), (0, 0, 0, 255)); add_glow(gtile, gi, (0, 0)); sh.paste(gtile, (x + w + 6, y))
        comp = Image.new('RGBA', (w, h), BG); comp.alpha_composite(bi); add_glow(comp, gi, (0, 0)); sh.paste(comp, (x + 2 * (w + 6), y))
        d.text((x, y + h + 2), k, fill=(180, 190, 200, 255)); x += 3 * (w + 6) + 10; rowh = max(rowh, h)
    py = y + rowh + 30; d.text((10, py - 14), 'TEST PATCH: island with seawalls (inlet + notch), road, smelter / depot / pod_house with glow', fill=(200, 220, 255, 255))
    sh.alpha_composite(p, (10, py)); sh = sh.crop((0, 0, W, py + p.height + 10))
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True); sh.convert('RGB').save(os.path.join(HERE, 'out', 'contact.png')); p.convert('RGB').save(os.path.join(HERE, 'out', 'patch.png'))
    print('contact', sh.size)
sheet()
