import math, random
import numpy as np
from PIL import Image, ImageDraw
from lib import hexc

TW, TH = 132, 68   # 128x64 diamond + 2px bleed each side; anchor (66,66)
ANCH = (66, 66)

def pnoise(u, v, n, seed):
    """periodic (period 1 in u and v) smooth value noise."""
    g = np.random.default_rng(seed).random((n, n))
    x = (u % 1) * n; y = (v % 1) * n
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = x - x0; fy = y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    x0 %= n; y0 %= n; x1 = (x0 + 1) % n; y1 = (y0 + 1) % n
    return (g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x1] * fx * (1 - fy) +
            g[y1, x0] * (1 - fx) * fy + g[y1, x1] * fx * fy) - .5

def uv_grid():
    py, px = np.mgrid[0:TH, 0:TW].astype(float)
    dx = px + .5 - 66; dy = py + .5 - 34
    u = (1 + dy / 32 + dx / 64) / 2
    v = (1 + dy / 32 - dx / 64) / 2
    return u, v

def alpha_mask(u, v):
    e = 1.5 / 32
    d = np.minimum(np.minimum(u + e, 1 + e - u), np.minimum(v + e, 1 + e - v)) * 32
    return np.clip(d + .5, 0, 1)

def base(kind, u, v):
    """shared (variant-independent) large-scale colour -> seamless."""
    n = pnoise(u, v, 3, 11) * .25 + pnoise(u, v, 6, 12) * .45 + pnoise(u, v, 12, 13) * .6 + pnoise(u, v, 20, 18) * .35
    return n

PAL = {
    'deep': ('#1f5f7a', '#17506b', '#2a7390'),
    'shallow': ('#52aeb0', '#3f9ba6', '#74c8bd'),
    'sand': ('#e4cd96', '#d4b87e', '#f0dfae'),
    'grass': ('#6e9a46', '#5a8a3c', '#8bb352'),
    'road': ('#b08a5c', '#9a774c', '#c7a574'),
}

def make(kind, variant):
    u, v = uv_grid()
    n = base(kind, u, v)
    mid, dark, light = [hexc(c) for c in PAL[kind]]
    t = np.clip(n * 1.6 + .5, 0, 1)[..., None]
    col = np.where(t < .5, dark + (mid - dark) * (t / .5), mid + (light - mid) * ((t - .5) / .5))
    # soft top-left light gradient (very gentle, periodic-safe because linear in tile coords is skipped)
    fine = pnoise(u, v, 24, 14)[..., None] * 16
    col = col + fine
    if kind in ('deep', 'shallow'):
        # horizontal-ish painted wave bands (iso-aligned), periodic
        w = np.sin((u + v) * 2 * math.pi * 3 + pnoise(u, v, 4, 15) * 6) * .5 + .5
        k = 18 if kind == 'deep' else 14
        col = col + (w[..., None] - .5) * k * .6 * np.array([.6, 1, 1])
    if kind == 'sand':
        rip = np.sin((u - v) * 2 * math.pi * 4 + pnoise(u, v, 5, 16) * 5)
        col = col + rip[..., None] * 4
    if kind == 'grass':
        col = col + (pnoise(u, v, 18, 17)[..., None] * 18) * np.array([.5, 1, .3])
    col = np.clip(col, 0, 255)
    a = alpha_mask(u, v)
    im = Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), 'RGBA')
    # detail layer at 4x, kept inside inner diamond to avoid seams
    K = 4
    det = Image.new('RGBA', (TW * K, TH * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(det)
    rnd = random.Random(hash((kind, variant)) & 0xffff)
    def pt(uu, vv): return ((66 + (uu - vv) * 64) * K, (2 + (uu + vv) * 32) * K)
    def inner(m=.1):
        return rnd.uniform(m, 1 - m), rnd.uniform(m, 1 - m)
    if kind == 'grass':
        for _ in range(130 + variant * 10):
            uu, vv = inner(.08); x, y = pt(uu, vv)
            L = rnd.uniform(3, 7)
            c = rnd.choice([(150, 196, 86, 150), (88, 138, 56, 150), (172, 206, 100, 120), (66, 112, 50, 120)])
            d.line([(x, y), (x + rnd.uniform(-2, 2) * K, y - L * K)], fill=c, width=int(1.3 * K))
        for _ in range(3 + variant):
            uu, vv = inner(.15); x, y = pt(uu, vv)
            c = rnd.choice([(250, 238, 160, 230), (240, 240, 235, 220), (240, 170, 150, 200)])
            d.ellipse([x - K, y - K, x + K, y + K], fill=c)
    elif kind == 'sand':
        for _ in range(110):
            uu, vv = inner(.06); x, y = pt(uu, vv)
            c = rnd.choice([(250, 238, 190, 120), (190, 160, 110, 110), (150, 125, 90, 90)])
            d.ellipse([x - K * .6, y - K * .4, x + K * .6, y + K * .4], fill=c)
        for _ in range(3):
            uu, vv = inner(.2); x, y = pt(uu, vv)
            d.ellipse([x - 3 * K, y - 1.5 * K, x + 3 * K, y + 1.5 * K], fill=(156, 140, 120, 200))
            d.ellipse([x - 3 * K, y - 2 * K, x + 2.5 * K, y + .5 * K], fill=(196, 182, 158, 220))
    elif kind == 'road':
        for _ in range(150):
            uu, vv = inner(.05); x, y = pt(uu, vv)
            r = rnd.uniform(.5, 1.6)
            c = rnd.choice([(220, 196, 150, 160), (120, 92, 62, 160), (150, 126, 96, 150)])
            d.ellipse([x - r * K, y - r * K * .6, x + r * K, y + r * K * .6], fill=c)
        # wheel ruts along both iso axes (centre)
        for off in (-.1, .1):
            p0 = pt(0.02, .5 + off); p1 = pt(.98, .5 + off)
            d.line([p0, p1], fill=(110, 82, 54, 90), width=int(2 * K))
    elif kind == 'shallow':
        for _ in range(26):
            uu, vv = inner(.12); x, y = pt(uu, vv)
            L = rnd.uniform(6, 14)
            d.line([(x - L * K / 2, y), (x + L * K / 2, y + L * K * .08)], fill=(220, 250, 240, 130), width=int(1.2 * K))
        for _ in range(8):
            uu, vv = inner(.15); x, y = pt(uu, vv)
            d.line([(x - 4 * K, y), (x + 4 * K, y)], fill=(236, 210, 150, 80), width=int(1.6 * K))
    elif kind == 'deep':
        for _ in range(22):
            uu, vv = inner(.14); x, y = pt(uu, vv)
            L = rnd.uniform(6, 16)
            d.line([(x - L * K / 2, y), (x + L * K / 2, y)], fill=(130, 200, 215, 90), width=int(1.2 * K))
            d.line([(x - L * K / 2, y + 2 * K), (x + L * K / 2, y + 2 * K)], fill=(10, 40, 64, 90), width=int(1.2 * K))
    det = det.resize((TW, TH), Image.LANCZOS)
    im.alpha_composite(det)
    # re-mask alpha (detail must not leak)
    arr = np.asarray(im).copy(); arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')
