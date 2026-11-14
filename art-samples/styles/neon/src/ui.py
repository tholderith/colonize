"""Neon Foundry HUD: CRT-amber/cyan monospace, chamfered panels, warning stripes, glow, scanlines. Pillow only."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
FD = '/usr/share/fonts/truetype/jetbrains-mono/'
def F(sz, bold=True): return ImageFont.truetype(FD + ('JetBrainsMono-Bold.ttf' if bold else 'JetBrainsMono-Regular.ttf'), sz)
AMBER = (255, 176, 40); CYAN = (40, 232, 255); MAG = (255, 46, 166); GREEN = (70, 255, 134); RED = (255, 60, 50)
DIM = (120, 140, 150); PANEL = (9, 12, 18); STEEL = (28, 36, 46)
S2 = 2

def chamfer(x0, y0, x1, y1, c, cuts=(1, 1, 1, 1)):
    """polygon with 45-deg cut corners: cuts = (tl, tr, br, bl) flags"""
    tl, tr, br, bl = [c if f else 0 for f in cuts]
    return [(x0 + tl, y0), (x1 - tr, y0), (x1, y0 + tr), (x1, y1 - br), (x1 - br, y1), (x0 + bl, y1), (x0, y1 - bl), (x0, y0 + tl)]

def hazard(d, x0, y0, x1, y1, s=10, col=(210, 160, 20), dark=(18, 18, 20)):
    d.rectangle([x0, y0, x1, y1], fill=dark)
    k = x0 - (y1 - y0)
    while k < x1 + (y1 - y0):
        d.polygon([(k, y1), (k + s, y1), (k + s + (y1 - y0), y0), (k + (y1 - y0), y0)], fill=col); k += 2 * s
    # clip to rect by re-painting outside
    return

def glow_text(base, xy, txt, font, col, g=0.8, anchor='la'):
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.text(xy, txt, font=font, fill=col + (255,), anchor=anchor)
    gl = layer.filter(ImageFilter.GaussianBlur(5)); gl2 = layer.filter(ImageFilter.GaussianBlur(2))
    for gg, a in ((gl, 0.9 * g), (gl2, 0.6 * g)):
        arr = np.asarray(gg).astype('float32'); arr[..., 3] *= a
        base.alpha_composite(Image.fromarray(arr.clip(0, 255).astype('uint8'), 'RGBA'))
    base.alpha_composite(layer)

def scan(img, alpha=34, period=3):
    arr = np.asarray(img).astype('float32')
    h = arr.shape[0]
    rows = (np.arange(h) % period == 0)
    arr[rows, :, :3] *= 0.78
    return Image.fromarray(arr.clip(0, 255).astype('uint8'), 'RGBA')

# ------------------------------------------------------------------ icons (drawn at 2x, centre cx,cy, size r)
def icon(d, kind, cx, cy, r, col):
    if kind == 'credits':
        pts = [(cx + r * math.cos(math.radians(60 * i + 30)), cy + r * math.sin(math.radians(60 * i + 30))) for i in range(6)]
        d.polygon(pts, outline=col, width=3 * S2 // 2)
        d.text((cx, cy), 'C', font=F(int(r * 1.15 * S2 // 1) if False else int(r * 1.1)), fill=col, anchor='mm')
    elif kind == 'scrap':
        for a in (35, -35):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            d.polygon([(cx - r * ca - 2 * sa, cy - r * sa + 2 * ca), (cx + r * ca - 2 * sa, cy + r * sa + 2 * ca), (cx + r * ca + 2 * sa, cy + r * sa - 2 * ca), (cx - r * ca + 2 * sa, cy - r * sa - 2 * ca)], fill=col)
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=PANEL)
    elif kind == 'alloy':
        d.polygon([(cx - r, cy + r * 0.6), (cx + r, cy + r * 0.6), (cx + r * 0.65, cy - r * 0.2), (cx - r * 0.65, cy - r * 0.2)], outline=col, width=3)
        d.polygon([(cx - r * 0.65, cy - r * 0.2), (cx + r * 0.65, cy - r * 0.2), (cx + r * 0.4, cy - r * 0.7), (cx - r * 0.4, cy - r * 0.7)], fill=col)
    elif kind == 'power':
        d.polygon([(cx + r * 0.2, cy - r), (cx - r * 0.55, cy + r * 0.15), (cx - r * 0.05, cy + r * 0.15), (cx - r * 0.2, cy + r), (cx + r * 0.55, cy - r * 0.2), (cx + r * 0.05, cy - r * 0.2)], fill=col)
    elif kind == 'rations':
        d.rounded_rectangle([cx - r * 0.7, cy - r * 0.6, cx + r * 0.7, cy + r * 0.8], 3, outline=col, width=3)
        d.line([(cx - r * 0.7, cy - r * 0.15), (cx + r * 0.7, cy - r * 0.15)], fill=col, width=3)
        d.rectangle([cx - r * 0.4, cy + r * 0.1, cx + r * 0.4, cy + r * 0.4], fill=col)
    elif kind == 'polymer':
        d.polygon([(cx, cy - r), (cx + r * 0.7, cy + r * 0.25), (cx + r * 0.5, cy + r * 0.85), (cx - r * 0.5, cy + r * 0.85), (cx - r * 0.7, cy + r * 0.25)], outline=col, width=3)
        d.ellipse([cx - r * 0.25, cy + r * 0.05, cx + r * 0.25, cy + r * 0.55], fill=col)
    elif kind == 'pop':
        d.ellipse([cx - r * 0.35, cy - r * 0.9, cx + r * 0.35, cy - r * 0.2], fill=col)
        d.pieslice([cx - r * 0.85, cy - r * 0.05, cx + r * 0.85, cy + r * 1.7], 180, 360, fill=col)

def topbar():
    W, H = 1920, 76
    big = Image.new('RGBA', (W * S2, H * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    # backing gradient
    grad = np.zeros((H * S2, W * S2, 4), 'uint8')
    t = np.linspace(0, 1, H * S2)[:, None]
    grad[..., 0] = (14 + 8 * t); grad[..., 1] = (18 + 10 * t); grad[..., 2] = (26 + 12 * t); grad[..., 3] = 236
    big = Image.fromarray(grad, 'RGBA'); d = ImageDraw.Draw(big)
    # bottom edge: amber rule + hazard end caps
    d.rectangle([0, (H - 5) * S2, W * S2, (H - 3) * S2], fill=(255, 176, 40, 200))
    d.rectangle([0, (H - 2) * S2, W * S2, H * S2], fill=(0, 0, 0, 160))
    for (x0, x1) in ((0, 150), (W - 150, W)):
        hz = Image.new('RGBA', ((x1 - x0) * S2, 6 * S2), (0, 0, 0, 0)); hd = ImageDraw.Draw(hz)
        hazard(hd, 0, 0, (x1 - x0) * S2, 6 * S2, s=12 * S2 // 2 + 6)
        big.alpha_composite(hz, (x0 * S2, (H - 10) * S2))
    cells = [('credits', 'CREDITS', '12,480', AMBER, '+38/c'), ('scrap', 'SCRAP', '1,206', AMBER, '+12/c'), ('alloy', 'ALLOY', '348', CYAN, '+4/c'),
             ('power', 'POWER', '412/500', CYAN, 'MW'), ('rations', 'RATIONS', '2,150', GREEN, '-9/c'), ('polymer', 'POLYMER', '96', MAG, '+2/c'), ('pop', 'COLONISTS', '214', AMBER, '/260')]
    x = 190
    # left badge
    d.polygon([(p[0] * S2, p[1] * S2) for p in chamfer(14, 8, 176, 62, 12, (1, 0, 0, 1))], fill=(26, 20, 6, 255), outline=(255, 176, 40, 255), width=2)
    cw = 170; gap = 8
    layout = []
    for i, (ic, lab, val, col, sub) in enumerate(cells):
        x0 = x + i * (cw + gap); x1 = x0 + cw
        d.polygon([(p[0] * S2, p[1] * S2) for p in chamfer(x0, 8, x1, 62, 10, (1, 0, 1, 0))], fill=(10, 14, 20, 255), outline=col + (150,), width=2)
        icon(d, ic, (x0 + 26) * S2, 35 * S2, 13 * S2, col + (255,)) if False else None
        layout.append((ic, lab, val, col, sub, x0))
    # right: tariff + clock
    rx0 = 1920 - 440
    d.polygon([(p[0] * S2, p[1] * S2) for p in chamfer(rx0, 8, 1920 - 170, 62, 10, (0, 1, 0, 1))], fill=(26, 8, 20, 255), outline=MAG + (220,), width=2)
    small = big.resize((W, H), Image.LANCZOS)
    # icons at 1x via 2x temp
    ic_layer = Image.new('RGBA', (W * S2, H * S2), (0, 0, 0, 0)); idr = ImageDraw.Draw(ic_layer)
    for (ic, lab, val, col, sub, x0) in layout: icon(idr, ic, (x0 + 28) * S2, 35 * S2, 13 * S2, col + (255,))
    ic_small = ic_layer.resize((W, H), Image.LANCZOS)
    glow = ic_small.filter(ImageFilter.GaussianBlur(4)); small.alpha_composite(glow); small.alpha_composite(ic_small)
    for (ic, lab, val, col, sub, x0) in layout:
        small_d = ImageDraw.Draw(small)
        small_d.text((x0 + 52, 17), lab, font=F(12, False), fill=DIM + (255,))
        glow_text(small, (x0 + 52, 31), val, F(24), col, 0.9)
        small_d.text((x0 + cw - 10, 17), sub, font=F(11, False), fill=(130, 150, 160, 255), anchor='ra')
    sd = ImageDraw.Draw(small)
    sd.text((30, 18), 'FOUNDRY-7', font=F(17), fill=AMBER + (255,)); sd.text((30, 41), 'SECTOR 3 // COLONY', font=F(11, False), fill=DIM + (255,))
    glow_text(small, (30, 18), 'FOUNDRY-7', F(17), AMBER, 0.5)
    sd.text((rx0 + 18, 14), 'CONCORDAT TARIFF', font=F(11, False), fill=(255, 140, 200, 255))
    glow_text(small, (rx0 + 18, 29), '18%', F(26), MAG, 0.9)
    sd.text((rx0 + 84, 36), 'NEXT LEVY 04:12', font=F(13), fill=(255, 120, 190, 255))
    sd.text((1920 - 150, 15), 'CYCLE 047', font=F(11, False), fill=DIM + (255,))
    glow_text(small, (1920 - 150, 30), '21:14', F(24), CYAN, 0.8)
    sd.text((1920 - 22, 34), '>>', font=F(20), fill=CYAN + (255,), anchor='ra')
    # subtle independence hint thin bar bottom of tariff box
    small = scan(small)
    small.save(os.path.join(OUT, 'ui_topbar.png'))

def panel():
    W, H = 360, 300
    big = Image.new('RGBA', (W * S2, H * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    poly = chamfer(0, 0, W - 1, H - 1, 22, (1, 1, 0, 0))
    d.polygon([(p[0] * S2, p[1] * S2) for p in poly], fill=(8, 12, 18, 238))
    d.line([(p[0] * S2, p[1] * S2) for p in poly + [poly[0]]], fill=(255, 176, 40, 230), width=3)
    # inner frame
    inner = chamfer(7, 7, W - 8, H - 8, 18, (1, 1, 0, 0))
    d.line([(p[0] * S2, p[1] * S2) for p in inner + [inner[0]]], fill=(40, 60, 70, 255), width=2)
    # header band with hazard end
    hz = Image.new('RGBA', (120 * S2, 7 * S2), (0, 0, 0, 0)); hd = ImageDraw.Draw(hz); hazard(hd, 0, 0, 120 * S2, 7 * S2, s=14)
    big.alpha_composite(hz, (210 * S2, 14 * S2))
    d.rectangle([16 * S2, 50 * S2, (W - 16) * S2, 51 * S2], fill=(255, 176, 40, 160))
    # bars
    rows = [('SCRAP', 612, 800, AMBER), ('ALLOY', 148, 400, CYAN), ('POLYMER', 66, 400, MAG), ('RATIONS', 410, 600, GREEN), ('POWER', 18, 40, CYAN)]
    y = 62
    for (lab, v, mx, col) in rows:
        x0, x1 = 112, 258
        d.rectangle([x0 * S2, (y + 5) * S2, x1 * S2, (y + 15) * S2], fill=(20, 28, 36, 255), outline=(60, 80, 90, 255), width=1)
        fw = int((x1 - x0 - 4) * v / mx)
        for k in range(0, fw, 6):
            d.rectangle([(x0 + 2 + k) * S2, (y + 7) * S2, (x0 + 2 + min(k + 4, fw)) * S2, (y + 13) * S2], fill=col + (255,))
        y += 28
    # independence meter
    d.rectangle([20 * S2, 214 * S2, (W - 20) * S2, 226 * S2], fill=(20, 8, 16, 255), outline=MAG + (200,), width=1)
    d.rectangle([22 * S2, 216 * S2, (22 + int((W - 44) * 0.23)) * S2, 224 * S2], fill=MAG + (255,))
    d.line([(20 + (W - 40) * 0.5) * S2, 212 * S2, (20 + (W - 40) * 0.5) * S2, 228 * S2], fill=(255, 255, 255, 140), width=1) if False else None
    s = big.resize((W, H), Image.LANCZOS); sd = ImageDraw.Draw(s)
    glow_text(s, (18, 12), 'DEPOT-03', F(20), AMBER, 0.8)
    sd.text((18, 52 - 3), 'CONTAINER YARD // STOCK', font=F(11, False), fill=DIM + (255,)) if False else None
    sd.text((18, 33), 'CONTAINER YARD  ' + chr(0x2022) + '  ONLINE', font=F(11, False), fill=GREEN + (255,))
    y = 62
    rows2 = [('SCRAP', '612/800', AMBER), ('ALLOY', '148/400', CYAN), ('POLYMER', '66/400', MAG), ('RATIONS', '410/600', GREEN), ('POWER', '18/40MW', CYAN)]
    for (lab, v, col) in rows2:
        sd.text((18, y + 3), lab, font=F(13), fill=col + (255,)); sd.text((W - 18, y + 3), v, font=F(13, False), fill=(200, 215, 220, 255), anchor='ra'); y += 28
    sd.text((18, 198), 'INDEPENDENCE', font=F(12), fill=MAG + (255,)); sd.text((W - 18, 198), '23%', font=F(12), fill=MAG + (255,), anchor='ra')
    sd.text((18, 238), 'CONCORDAT LEVY  18% / CYCLE', font=F(12, False), fill=(255, 130, 195, 255))
    sd.text((18, 256), 'AUDIT FLEET ETA  04:12', font=F(12, False), fill=(255, 130, 195, 255))
    sd.text((18, 276), '[ASSIGN]  [UPGRADE]  [DEMOLISH]', font=F(11, False), fill=CYAN + (255,))
    s = scan(s)
    s.save(os.path.join(OUT, 'ui_panel.png'))

def overlay():
    W, H = 1920, 1080
    y, x = np.mgrid[0:H, 0:W].astype('float32')
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    vig = np.clip((r - 0.62) / 0.75, 0, 1) ** 1.6 * 0.62
    a = vig.copy()
    sl = (np.arange(H) % 3 == 0)[:, None] * np.ones((1, W), 'float32') * 0.05
    a = 1 - (1 - a) * (1 - sl)
    rgb = np.zeros((H, W, 3), 'float32'); rgb[..., 0] = 2; rgb[..., 1] = 3; rgb[..., 2] = 8
    # bottom magenta/teal haze
    hz = np.clip((y - 760) / 320, 0, 1) ** 2 * 0.10
    rgb = rgb * (1 - hz[..., None]) + hz[..., None] * np.array([60, 18, 70], 'float32')
    a = 1 - (1 - a) * (1 - hz)
    Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype('uint8'), 'RGBA').save(os.path.join(OUT, 'ui_overlay.png'))

if __name__ == '__main__':
    topbar(); panel(); overlay(); print('ui done')
