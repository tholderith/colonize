"""UI overlays (Pillow): dark glass + brass hairlines, serif numerals, hand-shaded small icons."""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = '/usr/share/fonts/truetype/dejavu/'
def F(name, size): return ImageFont.truetype(FD + name, size)
SERIF_B = 'DejaVuSerif-Bold.ttf'; SERIF = 'DejaVuSerif.ttf'; SANS = 'DejaVuSans.ttf'; SANS_B = 'DejaVuSans-Bold.ttf'
BRASS = (186, 150, 96); BRASS_D = (112, 88, 54); TXT = (232, 224, 208); TXT_D = (150, 146, 136); GREEN = (128, 168, 108)
S = 4   # icon supersample

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))

def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float)[None, None, :] * (1 - t) + np.array(bot, float)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, 1).astype('uint8'), 'RGBA')

def shade_shape(mask, light, dark, angle=-60):
    """fill mask (L) with a diagonal gradient light->dark (light at upper-left)"""
    w, h = mask.size
    yy, xx = np.mgrid[0:h, 0:w]
    t = ((xx / w) * 0.55 + (yy / h) * 0.75).clip(0, 1)[..., None]
    arr = np.array(light, float)[None, None, :] * (1 - t) + np.array(dark, float)[None, None, :] * t
    im = Image.fromarray(arr.astype('uint8'), 'RGB').convert('RGBA'); im.putalpha(mask); return im

def new(sz): return Image.new('RGBA', (sz * S, sz * S), (0, 0, 0, 0))

def paste_shape(canvas, draw_fn, light, dark, blur=0.0):
    m = Image.new('L', canvas.size, 0); d = ImageDraw.Draw(m); draw_fn(d)
    canvas.alpha_composite(shade_shape(m, light, dark)); return m

def drop_shadow(icon, off=(2, 3), blur=3, alpha=150):
    a = icon.split()[3].filter(ImageFilter.GaussianBlur(blur * S / 2))
    sh = Image.new('RGBA', icon.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * alpha / 255)))
    out = Image.new('RGBA', icon.size, (0, 0, 0, 0)); out.alpha_composite(sh, (off[0] * S // 2, off[1] * S // 2)); out.alpha_composite(icon); return out

def icon_gold(sz=44):
    c = new(sz); u = sz * S / 44
    def coin(cx, cy, r=9, thick=4, rot=1.0):
        # side
        for k in range(int(thick * u), -1, -1):
            e = Image.new('L', c.size, 0); ImageDraw.Draw(e).ellipse((cx - r * u, cy - r * u * 0.5 + k, cx + r * u, cy + r * u * 0.5 + k), fill=255)
            c.alpha_composite(shade_shape(e, (176, 128, 44), (110, 74, 22)))
        e = Image.new('L', c.size, 0); ImageDraw.Draw(e).ellipse((cx - r * u, cy - r * u * 0.5, cx + r * u, cy + r * u * 0.5), fill=255)
        c.alpha_composite(shade_shape(e, (246, 214, 120), (190, 142, 52)))
        e2 = Image.new('L', c.size, 0); ImageDraw.Draw(e2).ellipse((cx - r * u * 0.72, cy - r * u * 0.36, cx + r * u * 0.72, cy + r * u * 0.36), outline=255, width=max(1, int(0.8 * u)))
        c.alpha_composite(shade_shape(e2, (150, 106, 36), (120, 84, 26)))
    coin(16 * u, 32 * u, 9, 3.2); coin(16 * u, 28.5 * u, 9, 3.2); coin(16 * u, 25 * u, 9, 3.2)
    coin(29 * u, 31 * u, 9, 3.2); coin(29 * u, 27.5 * u, 9, 3.2)
    coin(23 * u, 17 * u, 9, 3.2)
    return drop_shadow(c).resize((sz, sz), Image.LANCZOS)

def icon_wood(sz=44):
    c = new(sz); u = sz * S / 44
    rng = random.Random(3)
    def log(cx, cy, r):
        # side body (cylinder going back-left) + end disc
        m = Image.new('L', c.size, 0); d = ImageDraw.Draw(m)
        d.rectangle((cx - 12 * u, cy - r * u, cx, cy + r * u), fill=255); d.ellipse((cx - 12 * u - r * u * 0.45, cy - r * u, cx - 12 * u + r * u * 0.45, cy + r * u), fill=255)
        c.alpha_composite(shade_shape(m, (120, 86, 56), (58, 38, 24)))
        e = Image.new('L', c.size, 0); ImageDraw.Draw(e).ellipse((cx - r * u * 0.45, cy - r * u, cx + r * u * 0.45, cy + r * u), fill=255)
        c.alpha_composite(shade_shape(e, (210, 172, 118), (170, 128, 80)))
        d2 = ImageDraw.Draw(c)
        for k in (0.75, 0.5, 0.25):
            d2.ellipse((cx - r * u * 0.45 * k, cy - r * u * k, cx + r * u * 0.45 * k, cy + r * u * k), outline=(140, 98, 58, 200), width=max(1, int(0.7 * u)))
        d2.ellipse((cx - 1 * u, cy - 1.6 * u, cx + 1 * u, cy + 1.6 * u), fill=(120, 84, 48, 255))
    log(30 * u, 14 * u, 6.4); log(30 * u, 28 * u, 6.4); log(21 * u, 36 * u, 6.0) if False else None
    log(33 * u, 36 * u, 6.4); log(24 * u, 21 * u, 6.4)
    return drop_shadow(c).resize((sz, sz), Image.LANCZOS)

def icon_bricks(sz=44):
    c = new(sz); u = sz * S / 44
    def brick(x, y, w=22, h=8, dep=6):
        # front face, top face, side face (3/4 view)
        front = Image.new('L', c.size, 0); ImageDraw.Draw(front).rectangle((x * u, y * u, (x + w) * u, (y + h) * u), fill=255)
        top = Image.new('L', c.size, 0); ImageDraw.Draw(top).polygon([(x * u, y * u), ((x + w) * u, y * u), ((x + w + dep) * u, (y - dep * 0.7) * u), ((x + dep) * u, (y - dep * 0.7) * u)], fill=255)
        side = Image.new('L', c.size, 0); ImageDraw.Draw(side).polygon([((x + w) * u, y * u), ((x + w + dep) * u, (y - dep * 0.7) * u), ((x + w + dep) * u, (y + h - dep * 0.7) * u), ((x + w) * u, (y + h) * u)], fill=255)
        c.alpha_composite(shade_shape(front, (176, 84, 54), (130, 56, 36)))
        c.alpha_composite(shade_shape(top, (214, 128, 92), (186, 100, 68)))
        c.alpha_composite(shade_shape(side, (110, 46, 30), (88, 36, 24)))
        rng = random.Random(int(x * 7 + y)); d = ImageDraw.Draw(c)
        for _ in range(14): 
            px, py = rng.uniform(x, x + w) * u, rng.uniform(y, y + h) * u; d.point((px, py), fill=(90, 36, 24, 140))
    brick(5, 32, 24, 7); brick(11, 24, 24, 7); brick(5, 16, 24, 7)
    return drop_shadow(c).resize((sz, sz), Image.LANCZOS)

def icon_tools(sz=44):
    c = new(sz); u = sz * S / 44
    d = ImageDraw.Draw(c)
    def handle(p0, p1, w=3.6):
        m = Image.new('L', c.size, 0); dd = ImageDraw.Draw(m); dd.line([(p0[0] * u, p0[1] * u), (p1[0] * u, p1[1] * u)], fill=255, width=int(w * u))
        dd.ellipse((p0[0] * u - w * u / 2, p0[1] * u - w * u / 2, p0[0] * u + w * u / 2, p0[1] * u + w * u / 2), fill=255); dd.ellipse((p1[0] * u - w * u / 2, p1[1] * u - w * u / 2, p1[0] * u + w * u / 2, p1[1] * u + w * u / 2), fill=255)
        c.alpha_composite(shade_shape(m, (176, 128, 80), (100, 68, 40)))
    handle((8, 38), (34, 10)); handle((36, 38), (10, 10))
    # hammer head at (34,10) direction; pick head at (10,10)
    def head(poly, light=(190, 194, 198), dark=(84, 88, 96)):
        m = Image.new('L', c.size, 0); ImageDraw.Draw(m).polygon([(x * u, y * u) for x, y in poly], fill=255)
        c.alpha_composite(shade_shape(m, light, dark))
    head([(27, 3), (41, 9), (38, 15), (24, 9)])
    head([(3, 6), (16, 5), (18, 11), (14, 14), (6, 12), (2, 10)], (200, 204, 208), (90, 94, 102))
    return drop_shadow(c).resize((sz, sz), Image.LANCZOS)

def icon_food(sz=44):
    c = new(sz); u = sz * S / 44
    d = ImageDraw.Draw(c)
    gold1, gold2 = (232, 196, 100), (160, 118, 44)
    stalks = [(-12, 0.0), (-6, 0.0), (0, 0.0), (6, 0.0), (12, 0.0)]
    for i, (dx, _) in enumerate(stalks):
        bx = 22 + dx * 0.15; ex = 22 + dx * 1.25
        d.line([(bx * u, 40 * u), (ex * u, (8 + abs(dx) * 0.35) * u)], fill=(172, 134, 62, 255), width=int(1.4 * u))
        # ears: stacked grain ellipses
        for k in range(7):
            t = k / 6
            gx = ex + (bx - ex) * (0.0) ; gy = (8 + abs(dx) * 0.35) * u + k * 2.6 * u
            for sgn in (-1, 1):
                m = Image.new('L', c.size, 0); ImageDraw.Draw(m).ellipse((ex * u + sgn * 1.9 * u - 1.6 * u, gy - 2.0 * u, ex * u + sgn * 1.9 * u + 1.6 * u, gy + 2.0 * u), fill=255)
                c.alpha_composite(shade_shape(m, gold1, gold2))
    # band
    m = Image.new('L', c.size, 0); ImageDraw.Draw(m).rounded_rectangle((15 * u, 26 * u, 29 * u, 31 * u), 2 * u, fill=255)
    c.alpha_composite(shade_shape(m, (150, 70, 52), (96, 40, 30)))
    return drop_shadow(c).resize((sz, sz), Image.LANCZOS)

def icon_cloth(sz=44):
    c = new(sz); u = sz * S / 44
    def bolt(y, col_l, col_d, stripe):
        m = Image.new('L', c.size, 0); dd = ImageDraw.Draw(m)
        dd.rounded_rectangle((6 * u, y * u, 34 * u, (y + 9) * u), 4 * u, fill=255)
        c.alpha_composite(shade_shape(m, col_l, col_d))
        d = ImageDraw.Draw(c)
        for k in range(5): d.line([(8 * u + k * 5.5 * u, (y + 1) * u), (8 * u + k * 5.5 * u, (y + 8) * u)], fill=stripe + (90,), width=int(0.9 * u))
        e = Image.new('L', c.size, 0); ImageDraw.Draw(e).ellipse((29 * u, y * u, 40 * u, (y + 9) * u), fill=255)
        c.alpha_composite(shade_shape(e, tuple(min(255, v + 20) for v in col_l), col_d))
        d.ellipse((32.5 * u, (y + 3) * u, 36.5 * u, (y + 6) * u), outline=(40, 50, 72, 255), width=int(0.8 * u))
    bolt(31, (112, 136, 176), (62, 82, 118), (210, 220, 236)); bolt(21, (178, 150, 112), (120, 96, 66), (230, 214, 186)); bolt(11, (132, 70, 62), (82, 40, 36), (210, 170, 150))
    return drop_shadow(c).resize((sz, sz), Image.LANCZOS)

def icon_pop(sz=44):
    c = new(sz); u = sz * S / 44
    def person(cx, sc, light, dark, hat=None):
        m = Image.new('L', c.size, 0); dd = ImageDraw.Draw(m)
        dd.ellipse(((cx - 6 * sc) * u, 6 * u, (cx + 6 * sc) * u, (6 + 12 * sc) * u), fill=255)
        dd.rounded_rectangle(((cx - 12 * sc) * u, (20 * sc + 4) * u, (cx + 12 * sc) * u, 42 * u), 9 * u, fill=255)
        c.alpha_composite(shade_shape(m, light, dark))
    person(28, 0.8, (150, 140, 124), (84, 78, 68)); person(17, 1.0, (232, 222, 200), (148, 136, 112))
    return drop_shadow(c).resize((sz, sz), Image.LANCZOS)

def icon_pause(sz=22):
    im = Image.new('RGBA', (sz * 4, sz * 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for x in (0.27, 0.58): d.rounded_rectangle((x * sz * 4, 0.22 * sz * 4, (x + 0.15) * sz * 4, 0.78 * sz * 4), 4, fill=BRASS + (255,))
    return im.resize((sz, sz), Image.LANCZOS)

ICONS = dict(gold=icon_gold, wood=icon_wood, bricks=icon_bricks, tools=icon_tools, food=icon_food, cloth=icon_cloth, pop=icon_pop)

def spaced(d, xy, text, font, fill, sp=1.5, anchor='l'):
    x, y = xy
    if anchor == 'r':
        total = sum(d.textlength(ch, font=font) + sp for ch in text) - sp; x -= total
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + sp

def glass_bg(w, h, top=(26, 31, 34, 232), bot=(13, 16, 18, 238), seed=1):
    bg = vgrad(w, h, top, bot)
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 3.2, (h, w))
    arr = np.asarray(bg).astype(float); arr[..., :3] += n[..., None]
    return Image.fromarray(arr.clip(0, 255).astype('uint8'), 'RGBA')

def topbar():
    W, H = 1920, 76
    bg = glass_bg(W, H, seed=2)
    # soft shadow below bar region (last 4px) then main bar 72px
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = vgrad(W, 8, (0, 0, 0, 110), (0, 0, 0, 0)); base.alpha_composite(sh, (0, 68))
    main = bg.crop((0, 0, W, 72)); base.alpha_composite(main, (0, 0))
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.line([(0, 71), (W, 71)], fill=BRASS + (255,), width=1); d.line([(0, 70), (W, 70)], fill=(255, 240, 210, 26), width=1)
    d.line([(0, 0), (W, 0)], fill=(255, 255, 255, 28))
    # left plate: settlement name + season
    d.text((28, 12), 'PORT HALDANE', font=F(SERIF_B, 20), fill=TXT)
    d.text((28, 41), 'Spring  ·  1608', font=F(SERIF, 15), fill=TXT_D)
    d.line([(262, 12), (262, 58)], fill=BRASS_D + (200,), width=1)
    items = [('gold', 'GOLD', '1,250', '+12'), ('wood', 'WOOD', '184', '+6'), ('bricks', 'BRICKS', '62', '+2'), ('tools', 'TOOLS', '17', '+1'),
             ('food', 'FOOD', '438', '-4'), ('cloth', 'CLOTH', '41', '+3')]
    x0 = 290; cw = 196
    for i, (k, lab, val, delta) in enumerate(items):
        x = x0 + i * cw
        ic = ICONS[k](44); base.alpha_composite(ic, (x, 14))
        spaced(d, (x + 54, 12), lab, F(SANS_B, 11), TXT_D, 1.6)
        d.text((x + 54, 26), val, font=F(SERIF_B, 26), fill=TXT)
        col = GREEN if delta[0] == '+' else (196, 120, 104)
        d.text((x + 54 + d.textlength(val, font=F(SERIF_B, 26)) + 10, 38), delta, font=F(SANS, 13), fill=col)
        d.line([(x + cw - 14, 16), (x + cw - 14, 56)], fill=BRASS_D + (120,), width=1)
    # population block (right)
    px = x0 + len(items) * cw + 8
    base.alpha_composite(ICONS['pop'](44), (px, 14))
    spaced(d, (px + 54, 12), 'POPULATION', F(SANS_B, 11), TXT_D, 1.6)
    d.text((px + 54, 26), '76', font=F(SERIF_B, 26), fill=TXT); d.text((px + 54 + 38, 36), '/ 120', font=F(SANS, 14), fill=TXT_D)
    # speed controls
    d.line([(W - 170, 16), (W - 170, 56)], fill=BRASS_D + (200,), width=1)
    cx = W - 140
    base.alpha_composite(icon_pause(22), (cx, 25))
    for i, lab in enumerate(['1x', '2x', '3x']):
        bx = cx + 40 + i * 34
        d.rounded_rectangle((bx, 24, bx + 28, 48), 4, outline=BRASS_D + (230,) if i else BRASS + (255,), width=1, fill=(255, 255, 255, 14 if i else 40))
        d.text((bx + 14, 36), lab, font=F(SANS_B, 12), fill=TXT if i == 0 else TXT_D, anchor='mm')
    base.alpha_composite(layer); base.save(os.path.join(OUT, 'ui_topbar.png'))

def panel():
    W, H = 360, 300
    base = Image.new('RGBA', (W + 16, H + 16), (0, 0, 0, 0))
    sh = Image.new('RGBA', (W + 16, H + 16), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((8, 10, W + 8, H + 10), 10, fill=(0, 0, 0, 130))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    bg = glass_bg(W, H, (28, 33, 36, 238), (13, 16, 18, 244), seed=5)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, W - 1, H - 1), 8, fill=255)
    bg.putalpha(ImageChops.multiply(bg.split()[3], m))
    base.alpha_composite(bg, (4, 4))
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    ox, oy = 4, 4
    d.rounded_rectangle((ox, oy, ox + W - 1, oy + H - 1), 8, outline=BRASS + (255,), width=1)
    d.rounded_rectangle((ox + 4, oy + 4, ox + W - 5, oy + H - 5), 6, outline=BRASS_D + (150,), width=1)
    # header
    d.text((ox + 20, oy + 16), 'Harbour Warehouse', font=F(SERIF_B, 21), fill=TXT)
    d.text((ox + 20, oy + 46), 'Level II  ·  Storage 412 / 600', font=F(SANS, 13), fill=TXT_D)
    # ornament line
    d.line([(ox + 20, oy + 70), (ox + W - 20, oy + 70)], fill=BRASS + (200,), width=1)
    d.line([(ox + 20, oy + 72), (ox + W - 20, oy + 72)], fill=(255, 240, 210, 24), width=1)
    rows = [('wood', 'Timber', 184, 300), ('bricks', 'Bricks', 62, 150), ('tools', 'Tools', 17, 60), ('food', 'Grain', 138, 200), ('cloth', 'Cloth', 41, 100)]
    y = oy + 86
    for k, name, v, cap in rows:
        ic = ICONS[k](34); base.alpha_composite(ic, (ox + 20, y))
        d.text((ox + 64, y + 2), name, font=F(SANS, 15), fill=TXT)
        d.text((ox + W - 22, y + 2), str(v), font=F(SERIF_B, 17), fill=TXT, anchor='ra')
        # capacity bar
        bx0, bx1, by = ox + 64, ox + W - 22, y + 26
        d.rounded_rectangle((bx0, by, bx1, by + 5), 2, fill=(255, 255, 255, 22))
        fw = int((bx1 - bx0) * v / cap)
        d.rounded_rectangle((bx0, by, bx0 + fw, by + 5), 2, fill=(176, 142, 88, 235) if v / cap < 0.85 else (190, 120, 96, 235))
        d.rounded_rectangle((bx0, by, bx0 + fw, by + 1), 1, fill=(255, 235, 190, 90))
        y += 40
    # footer
    base.alpha_composite(layer); base.save(os.path.join(OUT, 'ui_panel.png'))

def vignette():
    W, H = 1920, 1080
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = (np.clip(r - 0.75, 0, 1) ** 1.8 * 150).astype('uint8')
    im = Image.new('RGBA', (W, H), (4, 8, 12, 0)); im.putalpha(Image.fromarray(a))
    im.save(os.path.join(OUT, 'ui_vignette.png'))

if __name__ == '__main__':
    topbar(); panel(); vignette(); print('ui done')
