"""Terrain tiles, procedural + lit in numpy, periodic in tile-space (u,v) => seamless; position-locked Bayer dither.
Half-res tile 64x32 -> palette-quantised -> 2x NEAREST -> 128x64 sprites, anchor (64,64)."""
import numpy as np, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PAL, ramp, ordered
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW, TH = 64, 32
yy, xx = np.mgrid[0:TH, 0:TW]; X = xx + 0.5 - TW / 2; Y = yy + 0.5 - TH / 2
MASK = np.abs(X) / (TW / 2) + np.abs(Y) / (TH / 2) < 1
U = (X / 32 + Y / 16) / 2 + 0.5; V = (Y / 16 - X / 32) / 2 + 0.5     # periodic tile coordinates

def pn(seed, kmax=4, decay=1.3, u=U, v=V):
    """periodic noise in ~[0,1]"""
    r = np.random.RandomState(seed); acc = np.zeros_like(u); tot = 0
    for kx in range(-kmax, kmax + 1):
        for ky in range(0, kmax + 1):
            if ky == 0 and kx <= 0: continue
            a = 1 / (kx * kx + ky * ky) ** (decay / 2); acc += a * np.cos(2 * np.pi * (kx * u + ky * v) + r.uniform(0, 6.283)); tot += a
    return acc / tot * 1.6 * 0.5 + 0.5
def lightgrad(h, k=3.0):
    gx = np.roll(h, -1, 1) - np.roll(h, 1, 1); gy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
    return np.clip(-(gx * 0.8 + gy * 0.6) * k, -1, 1)          # light from upper-left
def shade(c, l, amt=0.16): return c * (1 + l[..., None] * amt)
def sprinkle(img, seed, n, cols, rng_xy=None):
    r = np.random.RandomState(seed)
    for _ in range(n):
        u, v = r.rand(), r.rand(); px = int(32 + 32 * (u - v)); py = int(16 + 16 * (u + v - 1))
        if 0 <= px < TW and 0 <= py < TH and MASK[py, px]: img[py, px] = cols[r.randint(len(cols))]
    return img

def grass(k):
    n1 = pn(10 + k, 3); n2 = pn(40 + k, 11, 0.6); n3 = pn(70 + k, 6, 1.0)
    t = 0.42 + (n1 - .5) * .55 + (n2 - .5) * .45 + (n3 - .5) * .15
    c = ramp('grass', t); c = shade(c, lightgrad(n3 * .5 + n2 * .5), .20)
    blade = pn(90 + k, 16, 0.2) > 0.69; c[blade] = ramp('grass', 0.12 + 0.2 * n1[blade])[:]
    tuft = pn(120 + k, 16, 0.2) > 0.72; c[tuft & ~blade] = ramp('grass', 0.80 + 0.12 * n1[tuft & ~blade])
    c = sprinkle(c, 300 + k, 3 + k, [(250, 244, 230), (250, 222, 72), (240, 96, 84), (132, 72, 152)]) if k != 1 else c
    return c
def sand(k):
    n1 = pn(210 + k, 3); n2 = pn(240 + k, 10, .5)
    rip = np.sin(2 * np.pi * (2 * (U + V) + 0.6 * np.sin(2 * np.pi * (U - V) + k) + n1 * 0.8)) * .5 + .5
    t = 0.58 + (n1 - .5) * .45 + (n2 - .5) * .22 + (rip - .5) * .08
    c = ramp('sand', t); c = shade(c, lightgrad(rip * .15 + n2 * .85), .16)
    return sprinkle(c, 500 + k, 7, [ramp('earth', .7), ramp('stone', .8), ramp('plaster', .95), ramp('earth', .25)])
def road(k):
    r = np.random.RandomState(600 + k); N = 7 if k == 0 else 5
    pts = [((i + r.uniform(.2, .8)) / N, (j + r.uniform(.2, .8)) / N) for i in range(N) for j in range(N)]
    d1 = np.full(U.shape, 9.); d2 = d1.copy(); cid = np.zeros(U.shape, int)
    for ci, (pu, pv) in enumerate(pts):
        for du in (-1, 0, 1):
            for dv in (-1, 0, 1):
                d = np.hypot((U - pu - du) * 1.0 * 32 * 1.0, (V - pv - dv) * 1.0 * 32)  # isotropic in screen-ish metric
                m = d < d1; d2 = np.where(m, d1, np.minimum(d2, d)); cid = np.where(m, ci, cid); d1 = np.minimum(d, d1)
    shade_c = np.array([r.rand() for _ in pts])[cid]
    n = pn(630 + k, 10, .5); n1 = pn(650 + k, 3)
    edge = (d2 - d1)
    if k == 0:
        t = 0.45 + (shade_c - .5) * .6 + (n - .5) * .2
        c = ramp('stone', 0.35 + .35 * t) * np.array([1.0, .93, .84]) + 0
        c = shade(c, lightgrad(np.clip(edge / 6, 0, 1) * .7 + n * .3, 2.5), .25)
        c[edge < 1.1] = ramp('earth', 0.12)
    else:
        t = 0.38 + (n1 - .5) * .5 + (n - .5) * .35
        c = ramp('earth', t); c = shade(c, lightgrad(n * .5 + n1 * .5), .18)
        rut = np.abs(np.sin(2 * np.pi * (U + V) * 1.0 + 0.5)) > .93   # worn cart ruts
        c[rut] *= .82
        c[(edge < 0.8) & (shade_c > .55)] = ramp('stone', .55)
    return c
def crest(seedk, thr, amp, freq, u=U, v=V):
    ph = np.random.RandomState(seedk).uniform(0, 6.28, 3)
    p = freq * (u + v) + amp * np.sin(2 * np.pi * (u - v) + ph[0]) + 0.5 * amp * np.sin(2 * np.pi * (2 * (u - v)) + ph[1])
    ridge = np.cos(2 * np.pi * p)
    env = pn(seedk + 7, 3, 1.0)
    return (ridge > thr) & (env > 0.5), ridge, env
def deep(k):
    n1 = pn(800 + k, 3); n2 = pn(830 + k, 6, 0.9)
    ripple = np.cos(2 * np.pi * (2 * (U + V) + 0.5 * np.sin(2 * np.pi * (U - V) + k) + 1.2 * n2)) * .5 + .5
    t = 0.30 + (n1 - .5) * .35 + (ripple - .5) * .22
    c = ramp('sea', t); c = shade(c, lightgrad(ripple * .6 + n1 * .4, 1.8), .12)
    cm, ridge, env = crest(850 + k, 0.86, 0.22, 2, U, V)
    c[cm] = ramp('sea', 0.80 + .12 * ridge[cm]) 
    cm2, _, _ = crest(850 + k, 0.93, 0.22, 2, U, V); cm2 &= (env > .62)
    c[cm2] = ramp('foam', .6)
    gl = (np.roll(cm, 1, 0) | np.roll(cm, 1, 1)) & ~cm; c[gl & (n2 > .5)] = ramp('sea', .62)   # dark lee-side under crest
    return c
def shallow(k):
    n1 = pn(900 + k, 3); n2 = pn(930 + k, 5, .8)
    # caustic net: ridges of two periodic fields
    ca = 1 - np.abs(np.sin(np.pi * (3 * U + n2 * 1.4))) * np.abs(np.sin(np.pi * (3 * V + n1 * 1.4 + .3)))
    t = 0.38 + (n1 - .5) * .4 + ca ** 3 * .24
    c = ramp('lagoon', t); c = shade(c, lightgrad(n1, 1.5), .10)
    cm, ridge, env = crest(950 + k, 0.90, 0.2, 2, U, V); c[cm & (env > .55)] = ramp('foam', .3)
    sd = pn(990 + k, 4, 1.0) > .70; c[sd & ~cm] = ramp('sand', .55 + .2 * n2[sd & ~cm]) * .3 + ramp('lagoon', .75) * .7  # sandy patches
    return c

SPEC = {'grass': (grass, 4), 'sand': (sand, 3), 'road': (road, 2), 'deep': (deep, 4), 'shallow': (shallow, 4)}
def main():
    for name, (fn, n) in SPEC.items():
        for k in range(n):
            rgb = ordered(fn(k), spread=18)
            a = np.zeros((TH, TW, 4), np.uint8); a[..., :3] = rgb; a[..., 3] = MASK * 255
            Image.fromarray(a, 'RGBA').resize((TW * 2, TH * 2), Image.NEAREST).save(os.path.join(OUT, f'{name}_{k}.png'))
    print('terrain done')
if __name__ == '__main__': main()
