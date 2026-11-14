"""Cinematic UI overlays (Pillow): translucent dark glass, brass hairlines, DejaVu Serif headings, DejaVu Sans numerals,
Blender-rendered resource icons (icons.py), soft drop shadows.  Also writes ui_grade.png (haze + vignette + warm light)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WORK = os.environ.get('CWORK', '/tmp/cin_work')
FD = '/usr/share/fonts/truetype/dejavu/'
def F(n, s): return ImageFont.truetype(FD + n, s)
SERIF_B, SERIF, SANS, SANS_B = 'DejaVuSerif-Bold.ttf', 'DejaVuSerif.ttf', 'DejaVuSans.ttf', 'DejaVuSans-Bold.ttf'
BRASS = (201, 166, 107); BRASS_D = (122, 98, 60); BRASS_L = (240, 214, 160)
TXT = (240, 233, 218); TXT_D = (158, 160, 154); GREEN = (140, 190, 120); RED = (212, 128, 108)

def icon(k, sz):
    im = Image.open(os.path.join(WORK, 'icons', k + '.png')).convert('RGBA')
    bb = im.split()[3].point(lambda v: 255 if v > 20 else 0).getbbox()
    im = im.crop(bb); s = sz / max(im.size) ; im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    c = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); c.alpha_composite(im, ((sz - im.width) // 2, (sz - im.height) // 2 + 1))
    # soft drop shadow
    a = c.split()[3].filter(ImageFilter.GaussianBlur(2.0)); sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * 0.55)))
    out = Image.new('RGBA', (sz + 6, sz + 6), (0, 0, 0, 0)); out.alpha_composite(sh, (3, 5)); out.alpha_composite(c, (3, 3)); return out

def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float)[None, None, :] * (1 - t) + np.array(bot, float)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, 1).clip(0, 255).astype('uint8'), 'RGBA')

def glass(w, h, r=0, seed=1, top=(40, 45, 47, 214), bot=(14, 18, 20, 232)):
    bg = vgrad(w, h, top, bot)
    arr = np.asarray(bg).astype(float)
    # faint diagonal sheen + grain
    yy, xx = np.mgrid[0:h, 0:w]
    sheen = np.clip(1 - np.abs((xx * 0.5 - yy) / max(w, 1) * 1.2 - 0.25), 0, 1) * 7
    n = np.random.default_rng(seed).normal(0, 2.2, (h, w))
    arr[..., :3] += (sheen + n)[..., None]
    im = Image.fromarray(arr.clip(0, 255).astype('uint8'), 'RGBA')
    # inner shadow: darken edges
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    inner = ImageChops.invert(m.filter(ImageFilter.GaussianBlur(7))).point(lambda v: int(v * 0.5))
    dark = Image.new('RGBA', (w, h), (0, 0, 0, 0)); dark.putalpha(inner)
    # (inner is ~0 inside, rises at the edge)
    im.alpha_composite(Image.composite(dark, Image.new('RGBA', (w, h), (0, 0, 0, 0)), m))
    im.putalpha(ImageChops.multiply(im.split()[3], m)); return im

def spaced(d, xy, text, font, fill, sp=1.6, anchor='l'):
    x, y = xy
    tot = sum(d.textlength(c, font=font) + sp for c in text) - sp
    if anchor == 'r': x -= tot
    for c in text: d.text((x, y), c, font=font, fill=fill); x += d.textlength(c, font=font) + sp
    return tot

def hair(d, x0, y0, x1, y1, col=BRASS, fade=True):
    """gradient-faded brass hairline (vertical or horizontal)"""
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(n + 1):
        t = i / max(n, 1); a = (np.sin(np.pi * t) ** 0.6 if fade else 1.0)
        x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
        d.point((x, y), fill=col + (int(235 * a),))

def diamond(d, cx, cy, r, col=BRASS):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=col + (255,))

def topbar():
    W, H = 1920, 82
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = vgrad(W, 10, (0, 0, 0, 120), (0, 0, 0, 0)); base.alpha_composite(sh, (0, 72))
    base.alpha_composite(glass(W, 72, 0, 2, (36, 41, 43, 206), (12, 15, 17, 228)), (0, 0))
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.line([(0, 71), (W, 71)], fill=BRASS + (255,)); d.line([(0, 70), (W, 70)], fill=(255, 238, 200, 30)); d.line([(0, 68), (W, 68)], fill=BRASS_D + (120,))
    d.line([(0, 0), (W, 0)], fill=(255, 255, 255, 34))
    d.text((30, 11), 'Port Haldane', font=F(SERIF_B, 21), fill=TXT)
    spaced(d, (31, 43), 'SPRING  ·  1608', F(SANS, 12), TXT_D, 1.8)
    hair(d, 268, 12, 268, 60)
    items = [('gold', 'GOLD', '1,250', '+12'), ('wood', 'TIMBER', '184', '+6'), ('bricks', 'BRICKS', '62', '+2'), ('tools', 'TOOLS', '17', '+1'),
             ('food', 'FOOD', '438', '-4'), ('cloth', 'CLOTH', '41', '+3')]
    x0, cw = 290, 192
    for i, (k, lab, val, dl) in enumerate(items):
        x = x0 + i * cw
        base.alpha_composite(icon(k, 48), (x - 4, 9))
        spaced(d, (x + 56, 14), lab, F(SANS_B, 10), TXT_D, 1.8)
        fv = F(SANS_B, 23); d.text((x + 56, 29), val, font=fv, fill=TXT)
        d.text((x + 56 + d.textlength(val, font=fv) + 8, 38), dl, font=F(SANS, 12), fill=GREEN if dl[0] == '+' else RED)
        hair(d, x + cw - 10, 14, x + cw - 10, 58, BRASS_D)
    px = x0 + len(items) * cw + 6
    base.alpha_composite(icon('pop', 48), (px, 12))
    spaced(d, (px + 56, 14), 'POPULATION', F(SANS_B, 10), TXT_D, 1.8)
    d.text((px + 56, 29), '76', font=F(SANS_B, 23), fill=TXT); d.text((px + 56 + 34, 38), '/ 120', font=F(SANS, 12), fill=TXT_D)
    hair(d, W - 188, 14, W - 188, 58, BRASS_D)
    cx = W - 168
    # pause glyph + speed pills
    for x in (cx + 4, cx + 13): d.rounded_rectangle((x, 26, x + 5, 44), 1, fill=BRASS + (255,))
    for i, lab in enumerate(['1×', '2×', '3×']):
        bx = cx + 34 + i * 38; act = i == 0
        d.rounded_rectangle((bx, 24, bx + 32, 48), 5, outline=(BRASS if act else BRASS_D) + (255 if act else 200,), width=1, fill=(255, 235, 190, 46 if act else 12))
        d.text((bx + 16, 36), lab, font=F(SANS_B, 12), fill=TXT if act else TXT_D, anchor='mm')
    base.alpha_composite(L); base.save(os.path.join(OUT, 'ui_topbar.png'))

def panel():
    W, H = 360, 300; P = 8
    base = Image.new('RGBA', (W + 16, H + 16), (0, 0, 0, 0))
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((P - 2, P + 3, P + W + 2, P + H + 5), 12, fill=(0, 0, 0, 150))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    ox = oy = 4
    base.alpha_composite(glass(W, H, 9, 5, (40, 45, 47, 218), (13, 16, 18, 238)), (ox, oy))
    L = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle((ox, oy, ox + W - 1, oy + H - 1), 9, outline=BRASS + (255,), width=1)
    d.rounded_rectangle((ox + 5, oy + 5, ox + W - 6, oy + H - 6), 6, outline=BRASS_D + (130,), width=1)
    for (cx, cy) in ((ox + 5, oy + 5), (ox + W - 6, oy + 5), (ox + 5, oy + H - 6), (ox + W - 6, oy + H - 6)): diamond(d, cx, cy, 3)
    d.text((ox + 24, oy + 17), 'Harbour Warehouse', font=F(SERIF_B, 21), fill=TXT)
    spaced(d, (ox + 25, oy + 49), 'LEVEL II   ·   STORAGE 412 / 600', F(SANS, 10), TXT_D, 1.5)
    hair(d, ox + 24, oy + 72, ox + W // 2 - 10, oy + 72); hair(d, ox + W // 2 + 10, oy + 72, ox + W - 24, oy + 72); diamond(d, ox + W // 2, oy + 72, 3.5)
    rows = [('wood', 'Timber', 184, 300), ('bricks', 'Bricks', 62, 150), ('tools', 'Tools', 17, 60), ('food', 'Grain', 138, 200), ('cloth', 'Cloth', 41, 100)]
    y = oy + 88
    for k, name, v, cap in rows:
        base.alpha_composite(icon(k, 34), (ox + 22, y - 1))
        d.text((ox + 66, y + 1), name, font=F(SANS, 14), fill=TXT)
        d.text((ox + W - 26, y + 0), str(v), font=F(SANS_B, 16), fill=TXT, anchor='ra')
        bx0, bx1, by = ox + 66, ox + W - 26, y + 24
        d.rounded_rectangle((bx0, by, bx1, by + 5), 2, fill=(0, 0, 0, 120), outline=(255, 255, 255, 22))
        fw = max(4, int((bx1 - bx0) * v / cap)); hot = v / cap > 0.85
        bar = vgrad(fw, 4, (232, 196, 130, 255) if not hot else (226, 150, 120, 255), (160, 120, 66, 255) if not hot else (150, 78, 60, 255))
        mk = Image.new('L', (fw, 4), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, fw - 1, 3), 1, fill=255); bar.putalpha(mk)
        L.alpha_composite(bar, (bx0 + 1, by + 1))
        y += 40
    base.alpha_composite(L); base.save(os.path.join(OUT, 'ui_panel.png'))

def grade_overlay():
    """screen-space: atmospheric haze toward the frame edge, soft vignette, warm golden-hour glow from the upper left"""
    W, H = 1920, 1080
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    r = np.sqrt(nx ** 2 + ny ** 2)
    haze_a = np.clip((r - 0.55) / 0.9, 0, 1) ** 1.6 * 0.46
    vig_a = np.clip((r - 0.70) / 0.9, 0, 1) ** 2.0 * 0.48
    glow = np.exp(-(((xx - 330) / 700) ** 2 + ((yy - 120) / 450) ** 2))
    glow_a = glow * 0.10
    # composite three layers into a single RGBA (straight alpha)
    layers = [((18, 58, 72), haze_a), ((3, 8, 14), vig_a), ((255, 196, 120), glow_a)]
    col = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
    for c, a in layers:
        c = np.array(c, np.float32)
        out_a = a + al * (1 - a)
        col = (c * a[..., None] + col * (al * (1 - a))[..., None]) / np.maximum(out_a, 1e-5)[..., None]
        al = out_a
    rgba = np.concatenate([col, al[..., None] * 255], -1)
    Image.fromarray(rgba.clip(0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'ui_grade.png'))

if __name__ == '__main__':
    topbar(); panel(); grade_overlay(); print('ui done')
