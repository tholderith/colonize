"""Native-res pixel canvas with iso projection, Bayer-dithered ramp fills, outline, crop, 4x save."""
import math
import numpy as np
from PIL import Image, ImageDraw
from pal import *
SCALE = 4
B4 = np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]) / 16.0 + 1/32.0

def dith(ramp_, tone, x, y):
    """tone = float ramp level; Bayer choose between neighbouring entries."""
    tone = min(max(tone, 0), len(ramp_) - 1)
    i = int(math.floor(tone)); f = tone - i
    if i >= len(ramp_) - 1: return ramp_[-1]
    return ramp_[i + 1] if f > B4[y % 4, x % 4] else ramp_[i]

class Cv:
    """Canvas; coords are relative to anchor (ax,ay) inside an array of size w,h."""
    def __init__(s, w, h, ax, ay, U=16, V=16):
        s.w, s.h, s.ax, s.ay, s.U, s.V = w, h, ax, ay, U, V
        s.a = np.zeros((h, w, 4), np.uint8)
    # iso projection: u->SE, v->SW, origin = top corner of footprint
    def P(s, u, v, z=0): return (u - v, (u + v) / 2 - (s.U + s.V) / 2 - z)
    def put(s, x, y, c):
        X, Y = int(x + s.ax), int(y + s.ay)
        if 0 <= X < s.w and 0 <= Y < s.h: s.a[Y, X] = (*c, 255)
    def get(s, x, y):
        X, Y = int(x + s.ax), int(y + s.ay)
        return s.a[Y, X] if 0 <= X < s.w and 0 <= Y < s.h else np.zeros(4, np.uint8)
    def mask(s, pts):
        m = Image.new('L', (s.w, s.h), 0)
        ImageDraw.Draw(m).polygon([(int(round(x + s.ax)), int(round(y + s.ay))) for x, y in pts], fill=255)
        return np.array(m) > 0
    def fill(s, pts, ramp_=None, tone=0, col=None):
        """tone: float or fn(x,y)->float | colour tuple (override)."""
        m = s.mask(pts); ys, xs = np.nonzero(m)
        for Y, X in zip(ys, xs):
            x, y = X - s.ax, Y - s.ay
            if col is not None: c = col
            else:
                t = tone(x, y) if callable(tone) else tone
                c = t if isinstance(t, tuple) else dith(ramp_, t, x, y)
            s.a[Y, X] = (*c, 255)
    def poly3(s, pts3, ramp_=None, tone=0, col=None):
        s.fill([s.P(*p) for p in pts3], ramp_, tone, col)
    def line(s, p, q, c):
        im = Image.new('L', (s.w, s.h), 0)
        ImageDraw.Draw(im).line([(int(round(p[0]+s.ax)), int(round(p[1]+s.ay))), (int(round(q[0]+s.ax)), int(round(q[1]+s.ay)))], fill=255)
        m = np.array(im) > 0; s.a[m] = (*c, 255)
    def line3(s, p, q, c): s.line(s.P(*p), s.P(*q), c)
    def rect(s, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): s.put(x, y, c)
    def disc(s, cx, cy, rx, ry, ramp_=None, tone=0, col=None):
        pts = [(cx + rx * math.cos(t / 20 * math.pi), cy + ry * math.sin(t / 20 * math.pi)) for t in range(40)]
        s.fill(pts, ramp_, tone, col)
    def outline(s, col=INK):
        op = s.a[:, :, 3] > 0
        p = np.pad(op, 1)
        nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        new = nb & ~op
        s.a[new] = (*col, 255)
    def crop(s):
        ys, xs = np.nonzero(s.a[:, :, 3])
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        c = Cv(x1 - x0, y1 - y0, s.ax - x0, s.ay - y0, s.U, s.V); c.a = s.a[y0:y1, x0:x1].copy(); return c
    def save(s, path):
        im = Image.fromarray(s.a, 'RGBA').resize((s.w * SCALE, s.h * SCALE), Image.NEAREST)
        im.save(path); return [int(s.ax * SCALE), int(s.ay * SCALE)]

def new(fw=1, fh=1, up=48, down=6, side=8):
    U, V = 16 * fw, 16 * fh
    w = U + V + 2 * side
    return Cv(w, up + (U + V) // 2 + down, w // 2 + (U - V) // 2 * 0, up + (U + V) // 2, U, V)

# ---- hashing noise periodic over a tile lattice
def pnoise(u, v, seed, n=5):
    rng = np.random.RandomState(seed); t = 0; tot = 0
    for k in range(n):
        a, b = rng.randint(-3, 4), rng.randint(-3, 4)
        if a == 0 and b == 0: a = 1
        amp = 1.0 / (1 + 0.5 * (abs(a) + abs(b)))
        t = t + amp * np.cos(2 * np.pi * (a * u + b * v) + rng.uniform(0, 6.28)); tot += amp
    return t / tot
