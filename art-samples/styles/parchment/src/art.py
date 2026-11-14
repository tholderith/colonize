"""Shared drawing helpers: supersampled PIL canvas, wobbly ink, watercolour fills, hatching."""
import random, math
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
import numpy as np

S = 4  # supersample
INK = (58, 40, 28)
INK2 = (96, 70, 48)
PAPER = (236, 222, 188)
FD = "/usr/share/fonts/truetype/dejavu/"
def font(sz, bold=True, serif=True, italic=False):
    n = "DejaVuSerif" if serif else "DejaVuSans"
    n += "-BoldItalic" if bold and italic else "-Bold" if bold else "-Italic" if italic else ""
    return ImageFont.truetype(FD + (n if (bold or italic) else n) + ".ttf", sz)

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])
def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))

class A:
    def __init__(s, w, h, anchor=None, seed=1):
        s.w, s.h = w, h
        s.anchor = anchor or (w // 2, h)
        s.im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        s.rng = random.Random(seed)
    def xy(s, p): return (p[0] * S, p[1] * S)
    def P(s, gx, gy, h=0, fw=1, fh=1):
        """footprint-local iso coords -> sprite pixel coords"""
        ax, ay = s.anchor
        return (ax + (gx - gy) * 64 + (fh - fw) * 0, ay - (fw + fh) * 32 + (gx + gy) * 32 - h)
    def wob(s, pts, amp=0.9, step=7, closed=False):
        out = []
        seq = list(pts) + ([pts[0]] if closed else [])
        for i in range(len(seq) - 1):
            (x0, y0), (x1, y1) = seq[i], seq[i + 1]
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
            for k in range(n):
                t = k / n
                out.append((x0 + (x1 - x0) * t + s.rng.uniform(-amp, amp), y0 + (y1 - y0) * t + s.rng.uniform(-amp, amp)))
        out.append(seq[-1])
        return out
    def _mask(s, pts):
        m = Image.new("L", s.im.size, 0)
        ImageDraw.Draw(m).polygon([s.xy(p) for p in pts], fill=255)
        return m
    def wash(s, pts, col, pool=0.22, grain=14):
        """watercolour fill with darker pigment pooling at the edge + paper grain"""
        m = s._mask(pts)
        r = 3 * S // 2 + 1
        er = m.filter(ImageFilter.MinFilter(2 * r + 1)).filter(ImageFilter.GaussianBlur(S))
        edge = ImageChops.subtract(m, er)
        base = Image.new("RGBA", s.im.size, col + (255,))
        if grain:
            n = (np.random.RandomState(s.rng.randint(0, 9999)).rand(s.im.size[1] // 2 + 1, s.im.size[0] // 2 + 1) - .5) * grain
            n = np.kron(n, np.ones((2, 2)))[:s.im.size[1], :s.im.size[0]]
            a = np.array(base).astype(float); a[..., :3] += n[..., None]
            base = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
        dark = Image.new("RGBA", s.im.size, shade(col, .72) + (255,))
        pooled = Image.composite(dark, base, edge.point(lambda v: int(v * pool)))
        pooled.putalpha(m)
        s.im.alpha_composite(pooled)
    def line(s, pts, w=1.1, col=INK, amp=0.5, wobble=True, alpha=255):
        if wobble: pts = s.wob(pts, amp)
        d = ImageDraw.Draw(s.im)
        pp = [s.xy(p) for p in pts]
        c = col + (alpha,)
        d.line(pp, fill=c, width=max(1, int(w * S)), joint="curve")
    def poly(s, pts, col, ink=True, w=1.1, pool=0.22, grain=14):
        pts = s.wob(pts, .5, closed=True)[:-1] if ink else pts
        s.wash(pts, col, pool, grain)
        if ink: s.line(pts + [pts[0]], w, wobble=False)
    def hatch(s, pts, ang=60, gap=3.2, col=INK, w=.7, alpha=190, jitter=.25):
        m = s._mask(pts)
        L = Image.new("RGBA", s.im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        R = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 2
        a = math.radians(ang); dx, dy = math.cos(a), math.sin(a); nx, ny = -dy, dx
        t = -R
        while t < R:
            o = t + s.rng.uniform(-jitter, jitter)
            x0, y0 = cx + nx * o - dx * R, cy + ny * o - dy * R
            x1, y1 = cx + nx * o + dx * R, cy + ny * o + dy * R
            d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=col + (alpha,), width=max(1, int(w * S)))
            t += gap
        A_ = ImageChops.multiply(L.getchannel("A"), m)
        L.putalpha(A_)
        s.im.alpha_composite(L)
    def stipple(s, pts, n, col=INK, r=.6, alpha=170):
        m = s._mask(pts)
        L = Image.new("RGBA", s.im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        for _ in range(n):
            x = s.rng.uniform(min(xs), max(xs)); y = s.rng.uniform(min(ys), max(ys))
            d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=col + (alpha,))
        L.putalpha(ImageChops.multiply(L.getchannel("A"), m))
        s.im.alpha_composite(L)
    def ellipse(s, c, rx, ry, col, ink=True, w=1.0):
        pts = [(c[0] + math.cos(t / 14 * 2 * math.pi) * rx, c[1] + math.sin(t / 14 * 2 * math.pi) * ry) for t in range(14)]
        s.poly(pts, col, ink, w)
        return pts
    def text(s, xy, t, f, col=INK, anchor="la"):
        d = ImageDraw.Draw(s.im)
        d.text((xy[0] * S, xy[1] * S), t, font=font_s(f), fill=col + (255,), anchor=anchor)
    def save(s, path):
        im = s.im.resize((s.w, s.h), Image.LANCZOS)
        im.save(path)

_fc = {}
def font_s(spec):
    # spec: (size, bold, italic) scaled by S
    k = spec
    if k not in _fc: _fc[k] = font(int(spec[0] * S), spec[1], True, spec[2] if len(spec) > 2 else False)
    return _fc[k]

# ---- iso building blocks (footprint-local coords, tile units) ----
def box(a, x0, y0, x1, y1, h0, h1, wall, fw=1, fh=1, seed_hatch=True):
    P = lambda x, y, h: a.P(x, y, h, fw, fh)
    left = [P(x0, y1, h0), P(x1, y1, h0), P(x1, y1, h1), P(x0, y1, h1)]    # faces +y (screen lower-left)
    right = [P(x1, y1, h0), P(x1, y0, h0), P(x1, y0, h1), P(x1, y1, h1)]   # faces +x (lower-right)
    a.poly(left, shade(wall, .98)); a.poly(right, shade(wall, .8))
    a.hatch(right, 62, 2.6, alpha=120)
    return left, right

def gable(a, x0, y0, x1, y1, h0, hr, roof, fw=1, fh=1, over=.04, ridge_along_x=True):
    """gable roof; ridge along x at mid y. returns slope poly"""
    P = lambda x, y, h: a.P(x, y, h, fw, fh)
    xa, xb, ya, yb = x0 - over, x1 + over, y0 - over, y1 + over
    ym = (y0 + y1) / 2
    gab = [P(x1, y1, h0), P(x1, y0, h0), P(x1, ym, hr)]
    a.poly(gab, shade((236, 222, 190), .78)); a.hatch(gab, 62, 2.6, alpha=110)
    slope = [P(xa, yb, h0 - 2), P(xb, yb, h0 - 2), P(xb, ym, hr), P(xa, ym, hr)]
    a.poly(slope, roof)
    a.hatch(slope, 20, 2.4, alpha=120)
    # tile lines
    for k in range(1, 5):
        t = k / 5
        a.line([P(xa, yb + (ym - yb) * t, h0 - 2 + (hr - h0 + 2) * t), P(xb, yb + (ym - yb) * t, h0 - 2 + (hr - h0 + 2) * t)], .6, INK2, alpha=170)
    return slope

def door(a, x, y, h0, w, hh, fw=1, fh=1, col=(120, 84, 56)):
    P = lambda xx, yy, h: a.P(xx, yy, h, fw, fh)
    a.poly([P(x, y, h0), P(x + w, y, h0), P(x + w, y, h0 + hh), P(x, y, h0 + hh)], col, w=.8)
def window(a, x, y, h0, w, hh, fw=1, fh=1, right=False):
    P = lambda xx, yy, h: a.P(xx, yy, h, fw, fh)
    if right: q = [P(x, y, h0), P(x, y - w, h0), P(x, y - w, h0 + hh), P(x, y, h0 + hh)]
    else: q = [P(x, y, h0), P(x + w, y, h0), P(x + w, y, h0 + hh), P(x, y, h0 + hh)]
    a.poly(q, (92, 110, 100), w=.7, grain=0)
