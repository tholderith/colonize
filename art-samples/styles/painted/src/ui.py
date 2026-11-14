import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from lib import hexc, smooth_noise

FD = '/usr/share/fonts/truetype/dejavu/'
def font(sz, bold=True, serif=True):
    n = ('DejaVuSerif-Bold.ttf' if bold else 'DejaVuSerif.ttf') if serif else ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
    return ImageFont.truetype(FD + n, sz)

K = 3  # supersample for UI
def tex_wood(w, h, base='#6b4528', seed=1):
    rng = np.random.default_rng(seed)
    n1 = smooth_noise(w, h, 40, rng); n2 = smooth_noise(w, h, 3, rng)
    # grain: stretched horizontal noise
    g = np.asarray(Image.fromarray((rng.random((h // 2 + 2, max(2, w // 40))) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 - .5
    c = hexc(base)
    f = 1 + n1 * .25 + g * .35 + n2 * .08
    return np.clip(c[None, None, :] * f[..., None], 0, 255)

def tex_paper(w, h, base='#ead8ac', seed=2):
    rng = np.random.default_rng(seed)
    n = smooth_noise(w, h, 60, rng) * .5 + smooth_noise(w, h, 6, rng) * .3 + smooth_noise(w, h, 1.5, rng) * .25
    c = hexc(base)
    return np.clip(c[None, None, :] * (1 + n[..., None] * .22), 0, 255)

def icon_canvas(sz):
    im = Image.new('RGBA', (sz * K, sz * K), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)

def ic_gold(sz=40):
    im, d = icon_canvas(sz); s = sz * K
    for i, (cx, cy) in enumerate([(.42, .62), (.6, .56), (.5, .38)]):
        x, y, r = cx * s, cy * s, .26 * s
        d.ellipse([x - r, y - r * .55 + r * .25, x + r, y + r * .55 + r * .25], fill=(150, 100, 20, 255))
        d.ellipse([x - r, y - r * .55, x + r, y + r * .55], fill=(236, 190, 70, 255), outline=(120, 76, 16, 255), width=K)
        d.ellipse([x - r * .6, y - r * .3, x + r * .6, y + r * .3], outline=(255, 232, 140, 255), width=K)
    return im.resize((sz, sz), Image.LANCZOS)

def ic_wood(sz=40):
    im, d = icon_canvas(sz); s = sz * K
    for i, y in enumerate([.68, .5, .32]):
        x0 = .12 * s + (i % 2) * .08 * s
        d.rounded_rectangle([x0, y * s - .08 * s, x0 + .64 * s, y * s + .08 * s], radius=.08 * s, fill=(138, 92, 52, 255), outline=(70, 44, 24, 255), width=K)
        cx = x0 + .64 * s
        d.ellipse([cx - .09 * s, y * s - .1 * s, cx + .09 * s, y * s + .1 * s], fill=(222, 184, 120, 255), outline=(90, 58, 30, 255), width=K)
        d.ellipse([cx - .04 * s, y * s - .05 * s, cx + .04 * s, y * s + .05 * s], outline=(160, 118, 70, 255), width=K // 2 + 1)
    return im.resize((sz, sz), Image.LANCZOS)

def ic_brick(sz=40):
    im, d = icon_canvas(sz); s = sz * K
    rows = [(.62, [.1, .4]), (.4, [.2, .5]), (.18, [.1, .4])]
    for y, xs in rows:
        for x in xs:
            d.rounded_rectangle([x * s, y * s, (x + .32) * s, (y + .2) * s], radius=3, fill=(188, 88, 56, 255), outline=(98, 40, 24, 255), width=K)
            d.line([(x * s + 4, y * s + 4), ((x + .2) * s, y * s + 4)], fill=(224, 134, 96, 255), width=K)
    return im.resize((sz, sz), Image.LANCZOS)

def ic_tools(sz=40):
    im, d = icon_canvas(sz); s = sz * K
    d.line([(.22 * s, .84 * s), (.7 * s, .26 * s)], fill=(112, 72, 38, 255), width=int(.1 * s))
    d.polygon([(.5 * s, .14 * s), (.82 * s, .12 * s), (.88 * s, .36 * s), (.62 * s, .4 * s)], fill=(170, 176, 184, 255), outline=(70, 76, 84, 255))
    d.line([(.8 * s, .86 * s), (.3 * s, .26 * s)], fill=(150, 104, 58, 255), width=int(.09 * s))
    d.ellipse([.14 * s, .12 * s, .42 * s, .38 * s], outline=(150, 156, 164, 255), width=int(.07 * s))
    return im.resize((sz, sz), Image.LANCZOS)

def ic_food(sz=40):
    im, d = icon_canvas(sz); s = sz * K
    d.line([(.5 * s, .9 * s), (.5 * s, .22 * s)], fill=(140, 130, 60, 255), width=K * 2)
    for i in range(5):
        y = .22 + i * .11
        for sgn in (-1, 1):
            d.ellipse([(.5 + sgn * .08 - .075) * s, (y - .06) * s, (.5 + sgn * .08 + .075) * s, (y + .075) * s],
                      fill=(232, 192, 84, 255), outline=(150, 108, 30, 255), width=K)
    d.ellipse([.43 * s, .06 * s, .57 * s, .22 * s], fill=(240, 206, 100, 255), outline=(150, 108, 30, 255), width=K)
    return im.resize((sz, sz), Image.LANCZOS)

def ic_cloth(sz=40):
    im, d = icon_canvas(sz); s = sz * K
    d.polygon([(.14 * s, .36 * s), (.62 * s, .2 * s), (.9 * s, .34 * s), (.9 * s, .64 * s), (.4 * s, .82 * s), (.14 * s, .62 * s)], fill=(70, 120, 170, 255), outline=(30, 60, 100, 255))
    d.polygon([(.14 * s, .36 * s), (.4 * s, .52 * s), (.9 * s, .34 * s), (.62 * s, .2 * s)], fill=(110, 160, 208, 255), outline=(30, 60, 100, 255))
    d.line([(.4 * s, .52 * s), (.4 * s, .82 * s)], fill=(30, 60, 100, 255), width=K)
    d.ellipse([.1 * s, .38 * s, .3 * s, .66 * s], fill=(210, 190, 140, 255), outline=(120, 90, 50, 255), width=K)
    return im.resize((sz, sz), Image.LANCZOS)

def ic_pop(sz=40):
    im, d = icon_canvas(sz); s = sz * K
    d.ellipse([.34 * s, .1 * s, .66 * s, .42 * s], fill=(232, 184, 144, 255), outline=(110, 70, 40, 255), width=K)
    d.pieslice([.2 * s, .44 * s, .8 * s, 1.1 * s], 180, 360, fill=(70, 110, 150, 255), outline=(30, 50, 80, 255), width=K)
    d.polygon([(.3 * s, .14 * s), (.7 * s, .14 * s), (.62 * s, .02 * s), (.38 * s, .02 * s)], fill=(104, 70, 44, 255))
    return im.resize((sz, sz), Image.LANCZOS)

ICONS = [('gold', ic_gold), ('wood', ic_wood), ('bricks', ic_brick), ('tools', ic_tools), ('food', ic_food), ('cloth', ic_cloth), ('pop', ic_pop)]

def brass_rule(d, x0, y, x1, k=1):
    d.line([(x0, y), (x1, y)], fill=(236, 200, 110, 255), width=2 * k)
    d.line([(x0, y + 2 * k), (x1, y + 2 * k)], fill=(120, 84, 30, 255), width=k)

def shadowtext(im, xy, text, f, fill, sh=(30, 16, 8, 200), off=2, anchor='la'):
    d = ImageDraw.Draw(im)
    d.text((xy[0] + off, xy[1] + off), text, font=f, fill=sh, anchor=anchor)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)

def topbar(W=1920, H=76):
    wood = Image.fromarray(tex_wood(W, H, '#6a4428', 5).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(wood)
    # gradient highlight top/bottom
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(H):
        t = y / H
        a = int(60 * (1 - t) ** 2) if t < .5 else int(90 * ((t - .5) * 2) ** 2)
        od.line([(0, y), (W, y)], fill=(255, 220, 160, int(60 * (1 - t) ** 3)) if t < .5 else (20, 8, 0, a))
    wood.alpha_composite(ov)
    # planks seams
    for x in range(0, W, 240):
        d.line([(x, 0), (x, H)], fill=(40, 24, 12, 120), width=2)
        d.line([(x + 2, 0), (x + 2, H)], fill=(160, 112, 64, 70), width=1)
    # brass rail along bottom
    d.rectangle([0, H - 7, W, H], fill=(150, 104, 40, 255))
    d.line([(0, H - 7), (W, H - 7)], fill=(250, 214, 120, 255), width=2)
    d.line([(0, H - 2), (W, H - 2)], fill=(80, 50, 14, 255), width=2)
    d.line([(0, 1), (W, 1)], fill=(210, 160, 90, 180), width=1)
    # slots
    labels = ['Gold', 'Timber', 'Bricks', 'Tools', 'Food', 'Cloth', 'Settlers']
    vals = ['1,248', '86', '42', '17', '312', '28', '64']
    slot_w, gap = 214, 16
    x0 = 28
    fv = font(25); fl = font(12, serif=False)
    for i, ((nm, fn), lab, val) in enumerate(zip(ICONS, labels, vals)):
        x = x0 + i * (slot_w + gap)
        y0, y1 = 10, H - 16
        # recessed parchment plaque
        pl = Image.fromarray(tex_paper(slot_w, y1 - y0, '#e6d2a0', 10 + i).astype(np.uint8)).convert('RGBA')
        m = Image.new('L', (slot_w, y1 - y0), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, slot_w - 1, y1 - y0 - 1], radius=8, fill=255)
        # inner shadow
        sh = Image.new('RGBA', pl.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([0, 0, slot_w - 1, y1 - y0 - 1], radius=8, outline=(60, 36, 16, 150), width=4)
        sd.line([(6, 3), (slot_w - 8, 3)], fill=(70, 40, 16, 120), width=3)
        pl.alpha_composite(sh)
        wood.paste(pl, (x, y0), m)
        d.rounded_rectangle([x - 1, y0 - 1, x + slot_w, y1], radius=9, outline=(40, 24, 10, 255), width=2)
        d.rounded_rectangle([x - 3, y0 - 3, x + slot_w + 2, y1 + 2], radius=11, outline=(214, 166, 80, 140), width=1)
        ic = fn(44)
        # icon shadow
        shd = Image.new('RGBA', ic.size, (0, 0, 0, 0)); shd.paste((50, 30, 10, 120), mask=ic.split()[3]); wood.alpha_composite(shd.filter(ImageFilter.GaussianBlur(2)), (x + 10, y0 + 6))
        wood.alpha_composite(ic, (x + 8, y0 + 3))
        d.text((x + 64, y0 + 6), lab.upper(), font=fl, fill=(120, 84, 44, 255))
        d.text((x + 64, y0 + 20), val, font=fv, fill=(58, 34, 14, 255))
        if i < 6:
            pass
    # right end: date/season medallion
    f2 = font(18)
    xr = W - 240
    d.rounded_rectangle([xr, 10, W - 24, H - 16], radius=8, fill=(40, 24, 12, 180), outline=(214, 166, 80, 255), width=2)
    shadowtext(wood, (xr + 14, 14), 'Spring, 1604', f2, (246, 224, 170, 255), off=1)
    d.text((xr + 14, 38), 'Paused  ·  ❙❙', font=font(14, serif=False), fill=(200, 170, 110, 255))
    return wood

def panel(W=360, Hh=300):
    k = 2
    w, h = W * k, Hh * k
    wood = Image.fromarray(tex_wood(w, h, '#654126', 8).astype(np.uint8)).convert('RGBA')
    # parchment area
    m = 16 * k
    pap = Image.fromarray(tex_paper(w - 2 * m, h - 2 * m, '#ecd9ab', 21).astype(np.uint8)).convert('RGBA')
    pd = ImageDraw.Draw(pap)
    # stained edges vignette
    vg = Image.new('L', pap.size, 0); ImageDraw.Draw(vg).rectangle([14, 14, pap.size[0] - 14, pap.size[1] - 14], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(26))
    dark = Image.new('RGBA', pap.size, (110, 70, 30, 120)); dark.putalpha(Image.eval(vg, lambda v: int((255 - v) * .5)))
    pap.alpha_composite(dark)
    d = ImageDraw.Draw(pap)
    pw, ph = pap.size
    # header ribbon
    d.rectangle([0, 0, pw, 56 * k // 2 * 2 // 2 + 6], fill=(0, 0, 0, 0))
    d.rounded_rectangle([10 * k, 8 * k, pw - 10 * k, 38 * k], radius=6 * k, fill=(150, 62, 44, 255), outline=(90, 34, 22, 255), width=2)
    d.line([(14 * k, 10 * k), (pw - 14 * k, 10 * k)], fill=(206, 110, 84, 255), width=2)
    shadowtext(pap, (pw // 2, 23 * k), 'Harbour Warehouse', font(34), (250, 232, 190, 255), off=2, anchor='mm')
    d.text((12 * k, 44 * k), 'Stock', font=font(30, serif=False), fill=(100, 66, 34, 255))
    d.text((pw - 12 * k, 44 * k), '143 / 300', font=font(32), fill=(70, 42, 18, 255), anchor='ra')
    # capacity bar
    bx0, by0, bx1, by1 = 12 * k, 64 * k, pw - 12 * k, 78 * k
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=5 * k, fill=(120, 84, 46, 255), outline=(70, 44, 20, 255), width=2)
    d.rounded_rectangle([bx0 + 2, by0 + 2, bx0 + (bx1 - bx0) * .48, by1 - 2], radius=4 * k, fill=(106, 154, 64, 255))
    d.line([(bx0 + 8, by0 + 5), (bx0 + (bx1 - bx0) * .48 - 6, by0 + 5)], fill=(160, 204, 100, 255), width=3)
    # stock rows
    rows = [('Timber', 86, .55, ic_wood), ('Bricks', 42, .3, ic_brick), ('Tools', 17, .12, ic_tools), ('Food', 312, .9, ic_food), ('Cloth', 28, .2, ic_cloth)]
    y = 160
    for i, (nm, v, fr, fn) in enumerate(rows):
        ic = fn(52)
        pap.alpha_composite(ic, (20, y - 4))
        d.text((72 * k // 1 + 8, y + 6), nm, font=font(32, serif=False), fill=(70, 44, 20, 255))
        # bar
        x0, x1 = 300, 450
        d.rounded_rectangle([x0, y + 12, x1, y + 38], radius=6, fill=(206, 184, 140, 255), outline=(110, 78, 40, 255), width=2)
        col = (106, 154, 64, 255) if fr > .25 else (200, 100, 60, 255)
        d.rounded_rectangle([x0 + 3, y + 15, x0 + 3 + (x1 - x0 - 6) * fr, y + 35], radius=5, fill=col)
        d.text((pw - 12 * k, y + 6), str(v), font=font(34), fill=(60, 36, 14, 255), anchor='ra')
        d.line([(12 * k, y + 70), (pw - 12 * k, y + 70)], fill=(150, 116, 70, 110), width=1)
        y += 84
    wood.paste(pap, (m, m))
    wd = ImageDraw.Draw(wood)
    # inner dark inset line + frame bevel
    wd.rectangle([m - 2, m - 2, w - m + 1, h - m + 1], outline=(36, 20, 8, 255), width=3)
    wd.rectangle([0, 0, w - 1, h - 1], outline=(30, 16, 6, 255), width=4)
    wd.line([(4, 4), (w - 5, 4)], fill=(190, 140, 78, 200), width=3)
    wd.line([(4, 4), (4, h - 5)], fill=(190, 140, 78, 160), width=3)
    wd.line([(w - 5, 6), (w - 5, h - 5)], fill=(30, 16, 6, 200), width=3)
    # brass corner studs
    for (cx, cy) in [(8 * k, 8 * k), (w - 8 * k, 8 * k), (8 * k, h - 8 * k), (w - 8 * k, h - 8 * k)]:
        wd.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(190, 140, 50, 255), outline=(70, 44, 10, 255), width=2)
        wd.ellipse([cx - 5, cy - 6, cx + 1, cy], fill=(255, 232, 150, 255))
    return wood.resize((W, Hh), Image.LANCZOS)
