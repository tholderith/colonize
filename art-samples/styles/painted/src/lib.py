"""Painted Isometric - shared painting helpers (numpy+Pillow, 2x supersampled)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 2  # supersample

def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)
def mul(c, f): return np.clip(np.asarray(c, float) * f, 0, 255)
def mix(a, b, t): return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t
def warm(c, f):  # shade toward cool-warm: lit -> warm, shadow -> cool purple-ish
    c = np.asarray(c, float)
    if f >= 1: return np.clip(c * np.array([f, f * .99, f * .93]), 0, 255)
    k = 1 - f
    return np.clip(c * f + np.array([40, 36, 70]) * k * 0.35, 0, 255)

def smooth_noise(w, h, scale, rng):
    gw, gh = max(2, int(w / scale) + 2), max(2, int(h / scale) + 2)
    g = rng.random((gh, gw)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255 - 0.5

class Canvas:
    """RGBA float canvas at S x resolution. Coordinates passed in are 1x pixels."""
    def __init__(self, w, h, seed=1):
        self.w, self.h = w, h
        self.W, self.H = w * S, h * S
        self.rgb = np.zeros((self.H, self.W, 3), np.float32)
        self.a = np.zeros((self.H, self.W), np.float32)
        rng = np.random.default_rng(seed)
        self.rng = rng
        self.nz = (smooth_noise(self.W, self.H, 24, rng) * .9 + smooth_noise(self.W, self.H, 7, rng) * .8 +
                   smooth_noise(self.W, self.H, 2.2, rng) * .6)
        self.py = random.Random(seed)

    def mask(self, pts, blur=0):
        im = Image.new('L', (self.W, self.H), 0)
        ImageDraw.Draw(im).polygon([(x * S, y * S) for x, y in pts], fill=255)
        if blur: im = im.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(im, np.float32) / 255

    def ellipse_mask(self, cx, cy, rx, ry, blur=0):
        im = Image.new('L', (self.W, self.H), 0)
        ImageDraw.Draw(im).ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
        if blur: im = im.filter(ImageFilter.GaussianBlur(blur * S))
        return np.asarray(im, np.float32) / 255

    def comp(self, m, rgb):
        """alpha-over of colour field rgb (HxWx3 or 3,) with coverage m."""
        m = np.clip(m, 0, 1)
        oa = m + self.a * (1 - m)
        den = np.maximum(oa, 1e-6)[..., None]
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), self.rgb.shape)
        self.rgb = (rgb * m[..., None] + self.rgb * (self.a * (1 - m))[..., None]) / den
        self.a = oa

    def fill_mask(self, m, color, shade=(1, 1), tex=.08, alpha=1, bbox=None):
        ys = np.where(m.max(1) > .01)[0]
        if len(ys) == 0: return
        y0, y1 = ys[0], ys[-1]
        g = np.ones(self.H, np.float32)
        g[y0:y1 + 1] = np.linspace(shade[0], shade[1], y1 - y0 + 1)
        f = (g[:, None] * (1 + tex * self.nz))[..., None]
        self.comp(m * alpha, np.asarray(color, np.float32) * f)

    def poly(self, pts, color, **kw):
        m = self.mask(pts); self.fill_mask(m, color, **kw); return m

    def circle(self, cx, cy, r, color, **kw):
        m = self.ellipse_mask(cx, cy, r, r); self.fill_mask(m, color, **kw); return m

    def strokes(self, m, colors, n, length, ang=(0, 360), width=1.0, alpha=.5, box=None, seed=0):
        """painterly dabs clipped to mask m. box=(x0,y0,x1,y1) 1x area to scatter in."""
        rnd = random.Random(seed + n)
        lay = Image.new('RGBA', (self.W, self.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        if box is None:
            ys, xs = np.where(m > .5)
            if len(ys) == 0: return
            box = (xs.min() / S, ys.min() / S, xs.max() / S, ys.max() / S)
        for _ in range(n):
            x = rnd.uniform(box[0], box[2]); y = rnd.uniform(box[1], box[3])
            a = math.radians(rnd.uniform(*ang)); L = length * rnd.uniform(.5, 1.2)
            c = colors[rnd.randrange(len(colors))]
            d.line([(x * S, y * S), ((x + math.cos(a) * L) * S, (y + math.sin(a) * L) * S)],
                   fill=(int(c[0]), int(c[1]), int(c[2]), int(255 * alpha)), width=max(1, int(width * S)))
        arr = np.asarray(lay, np.float32)
        self.comp(m * arr[..., 3] / 255, arr[..., :3])

    def lines(self, segs, color, width=1.0, alpha=1, m=None):
        lay = Image.new('L', (self.W, self.H), 0)
        d = ImageDraw.Draw(lay)
        for (x0, y0), (x1, y1) in segs:
            d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=255, width=max(1, int(round(width * S))))
        k = np.asarray(lay, np.float32) / 255 * alpha
        if m is not None: k = k * m
        self.comp(k, np.asarray(color, np.float32))

    def shadow(self, pts, alpha=.3, blur=3, color=(25, 30, 50)):
        m = self.mask(pts, blur); self.comp(m * alpha, np.asarray(color, np.float32))

    def shadow_ellipse(self, cx, cy, rx, ry, alpha=.3, blur=3, color=(25, 30, 50)):
        m = self.ellipse_mask(cx, cy, rx, ry, blur); self.comp(m * alpha, np.asarray(color, np.float32))

    def sphere(self, cx, cy, r, color, light=(-.4, -.5), tex=.1, ry=None):
        ry = ry or r
        x0, x1 = int((cx - r - 1) * S), int((cx + r + 1) * S)
        y0, y1 = int((cy - ry - 1) * S), int((cy + ry + 1) * S)
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(self.W, x1), min(self.H, y1)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        nx = (xx / S - cx) / r; ny = (yy / S - cy) / ry
        d2 = nx * nx + ny * ny
        cov = np.clip((1 - np.sqrt(d2)) * r * S * .9 + .5, 0, 1)
        nzv = np.sqrt(np.clip(1 - d2, 0, 1))
        lam = np.clip(-(nx * light[0] + ny * light[1]) * .8 + nzv * .55, 0, 1.2)
        f = (.52 + .75 * lam) * (1 + tex * self.nz[y0:y1, x0:x1])
        col = np.asarray(color, np.float32)
        shaded = np.clip(col * f[..., None], 0, 255)
        # cool shadows
        sh = np.clip(1 - lam, 0, 1)[..., None] * np.array([-6, -2, 14], np.float32) * .6
        shaded = np.clip(shaded + sh, 0, 255)
        m = np.zeros((self.H, self.W), np.float32); m[y0:y1, x0:x1] = cov
        full = np.zeros_like(self.rgb); full[y0:y1, x0:x1] = shaded
        self.comp(m, full)

    def outline(self, color=(52, 34, 26), alpha=.55, px=1.0):
        ao = np.clip((self.a - .5) * 2, 0, 1)
        a = Image.fromarray((ao * 255).astype(np.uint8))
        k = int(px * S) * 2 + 1
        dil = np.asarray(a.filter(ImageFilter.MaxFilter(k)), np.float32) / 255
        ring = np.clip(dil - ao, 0, 1) * alpha
        # draw outline underneath existing content
        oa = self.a + ring * (1 - self.a)
        den = np.maximum(oa, 1e-6)[..., None]
        self.rgb = (self.rgb * self.a[..., None] + np.asarray(color, np.float32) * (ring * (1 - self.a))[..., None]) / den
        self.a = oa

    def to_image(self):
        rgba = np.dstack([np.clip(self.rgb, 0, 255), self.a * 255]).astype(np.uint8)
        # premultiply-safe downscale
        im = Image.fromarray(rgba, 'RGBA')
        pm = np.asarray(im, np.float32)
        pm[..., :3] *= pm[..., 3:4] / 255
        out = []
        for i in range(4):
            out.append(np.asarray(Image.fromarray(pm[..., i]).resize((self.w, self.h), Image.BOX if False else Image.LANCZOS)))
        o = np.stack(out, -1)
        a = np.clip(o[..., 3:4], 0, 255)
        rgb = np.where(a > 0.5, o[..., :3] * 255 / np.maximum(a, 1), 0)
        res = np.concatenate([np.clip(rgb, 0, 255), a], -1).astype(np.uint8)
        return Image.fromarray(res, 'RGBA')

class Iso:
    """maps footprint-local tile coords (a,b,z) -> canvas px. origin = top corner of footprint."""
    def __init__(self, fw, fh, H, mx=28):
        self.fw, self.fh = fw, fh
        self.mx = mx
        self.W = (fw + fh) * 64 + 2 * mx
        self.Hh = H + (fw + fh) * 32 + 12
        self.ox = fh * 64 + mx
        self.oy = H
        self.anchor = (self.ox + (fw - fh) * 64, self.oy + (fw + fh) * 32)
    def P(self, a, b, z=0): return (self.ox + (a - b) * 64, self.oy + (a + b) * 32 - z)
    def Q(self, *pp): return [self.P(*p) for p in pp]
    def canvas(self, seed=1): return Canvas(self.W, self.Hh, seed)
