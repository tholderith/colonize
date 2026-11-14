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
    N = 14; ox, oy = 64 * N // 2 + 64, 90
    c = Image.new('RGBA', (64 * N + 140, 32 * N * 2 + 260), BG)
    land = {(x, y) for y in range(2, 12) for x in range(2, 12)}
    land -= {(11, 2), (11, 3), (10, 2)}           # inlet (concave corners)
    land -= {(2, 11)}                             # convex notch
    # road network: E-W straight (3..10,6), T-junction at (6,6) with N spur, corner at (10,6)->S, corner at (10,8)->W, dead ends
    road = {(x, 6) for x in range(3, 11)} | {(6, 5), (6, 4), (10, 7), (10, 8), (9, 8), (8, 8)}
    water = lambda p: p not in land
    shallow = lambda p: any(abs(p[0] - a) <= 1 and abs(p[1] - b) <= 1 for a, b in land)
    for s in range(0, 2 * N):
        for gx in range(N):
            gy = s - gx
            if not (0 <= gy < N): continue
            p = (gx, gy)
            if p in land:
                nb = ((1, (gx, gy - 1)), (2, (gx + 1, gy)), (4, (gx, gy + 1)), (8, (gx - 1, gy)))
                m = sum(b for b, q in nb if water(q))
                if p in road and m == 0: key = 'road_%d' % sum(b for b, q in nb if q in road)
                elif m == 0: key = 'land_%d' % ((gx * 7 + gy * 13 + (gx * gy) % 5) % 3)    # mixed land variants
                else: key = 'shore_%d' % m
            else: key = 'shallow_water' if shallow(p) else 'deep_water'
            put_tile(c, key, gx, gy, ox, oy)
    # buildings: footprint south corner = tile (gx+fw-1, gy+fw-1) south corner
    for key, gx, gy, fw in (('ration_plant', 3, 4, 2), ('refinery', 7, 4, 2), ('fabricator', 3, 7, 2), ('pod_house', 8, 7, 1), ('pod_house_t2', 9, 7, 1),
                            ('smelter', 3, 9, 2), ('algae_skimmer', 6, 10, 2)):
        b = man['buildings'][key]; bx = gx + fw - 1; by = gy + fw - 1
        sx = ox + (bx - by) * 64; sy = oy + (bx + by) * 32 + 32
        c.alpha_composite(img(b['file']), (sx - b['anchor'][0], sy - b['anchor'][1]))
        add_glow(c, img(b['glow']), (sx - b['anchor'][0], sy - b['anchor'][1]))
    return c

def sheet():
    p = patch(); W = max(1500, p.width + 20)
    keys = list(man['tiles']); bk = list(man['buildings'])
    rows_h = 80 + 20 + 2 * 90 + 20
    sh = Image.new('RGBA', (W, 40 + 6 * 96 + 5200 + p.height), BG); d = ImageDraw.Draw(sh)
    d.text((10, 6), 'TILES (anchor = south corner)', fill=(200, 220, 255, 255))
    for i, k in enumerate(keys):
        x = 10 + (i % 10) * 142; y = 24 + (i // 10) * 96
        sh.alpha_composite(img(man['tiles'][k]['file']), (x, y)); d.text((x, y + 74 + 8), k, fill=(180, 190, 200, 255))
    y0 = 24 + ((len(keys) + 9) // 10) * 96 + 6; d.text((10, y0), 'BUILDINGS: base | glow (alpha=lum) | composed (base + additive glow)', fill=(200, 220, 255, 255))
    x = 10; y = y0 + 18; rowh = 0
    for k in bk:
        b = man['buildings'][k]; bi = img(b['file']); gi = img(b['glow']); w, h = bi.size
        if x + 3 * (w + 6) > W: x = 10; y += rowh + 20; rowh = 0
        sh.alpha_composite(bi, (x, y))
        gtile = Image.new('RGBA', (w, h), (0, 0, 0, 255)); add_glow(gtile, gi, (0, 0)); sh.paste(gtile, (x + w + 6, y))
        comp = Image.new('RGBA', (w, h), BG); comp.alpha_composite(bi); add_glow(comp, gi, (0, 0)); sh.paste(comp, (x + 2 * (w + 6), y))
        d.text((x, y + h + 2), k, fill=(180, 190, 200, 255)); x += 3 * (w + 6) + 10; rowh = max(rowh, h)
    y += rowh + 24; d.text((10, y), 'UNITS (anchor = tile centre at waterline). Per ship: ne | se | sw | nw composed on water tile (+ glow layer row). Bow points to the named screen diagonal.', fill=(200, 220, 255, 255)); y += 18
    uk = list(man.get('units', {}))
    for ship in ('hauler', 'trader', 'patrol'):
        for mode in ('composed', 'glow'):
            for i, dn in enumerate(('ne', 'se', 'sw', 'nw')):
                k = ship + '_' + dn
                if k not in man['units']: continue
                u = man['units'][k]; cx0 = 10 + i * 370; cy0 = y + 80
                cell = Image.new('RGBA', (360, 170), BG if mode == 'composed' else (0, 0, 0, 255))
                if mode == 'composed':
                    ta = man['tiles']['deep_water']; tim = img(ta['file']); cell.alpha_composite(tim, (180 - ta['anchor'][0], 144 - ta['anchor'][1]))
                    cell.alpha_composite(img(u['file']), (180 - u['anchor'][0], 112 - u['anchor'][1]))
                    add_glow(cell, img(u['glow']), (180 - u['anchor'][0], 112 - u['anchor'][1]))
                else: add_glow(cell, img(u['glow']), (180 - u['anchor'][0], 112 - u['anchor'][1]))
                sh.paste(cell, (cx0, y)); d.text((cx0 + 4, y + 4), k + ' (' + mode + ')', fill=(180, 190, 200, 255))
                d.ellipse((cx0 + 180 - 2, y + 112 - 2, cx0 + 180 + 2, y + 112 + 2), outline=(255, 255, 0, 255))
            y += 176
    py = y + 20; d.text((10, py - 14), 'TEST PATCH: island, road autotiles (straight/T/corners/dead ends), mixed land_0-2, new buildings with glow', fill=(200, 220, 255, 255))
    sh.alpha_composite(p, (10, py)); sh = sh.crop((0, 0, W, py + p.height + 10))
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True); sh.convert('RGB').save(os.path.join(HERE, 'out', 'contact.png')); p.convert('RGB').save(os.path.join(HERE, 'out', 'patch.png'))
    print('contact', sh.size)
sheet()
