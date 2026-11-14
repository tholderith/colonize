import numpy as np
from PIL import Image
from gfx import *

def diamond_mask(w=32, h=16):
    m = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            m[y, x] = abs(x + .5 - w / 2) / (w / 2) + abs(y + .5 - h / 2) / (h / 2) < 1
    return m
DM = diamond_mask()
def uv(w=32, h=16):
    X, Y = np.meshgrid(np.arange(w) + .5, np.arange(h) + .5)
    return ((X - w / 2) / (w / 2) + Y / (h / 2)) / 2 * 1.0 * (w / 32), (Y / (h / 2) - (X - w / 2) / (w / 2)) / 2

def tile(ramp_, seed, base, amp, extra=None, speck=None):
    """seamless tile: tone from periodic noise (u,v period 1) + Bayer dither; extra(u,v,X,Y,tone)->tone."""
    U_, V_ = uv()
    n = pnoise(U_, V_, seed) + 0.5 * pnoise(U_, V_, seed + 77, 7)
    t = base + amp * n
    X, Y = np.meshgrid(np.arange(32), np.arange(16))
    if extra: t = extra(U_, V_, X, Y, t)
    a = np.zeros((16, 32, 4), np.uint8)
    for y in range(16):
        for x in range(32):
            if DM[y, x]:
                a[y, x] = (*dith(ramp_, t[y, x], x, y), 255)
    return a

def save_tile(a, path):
    Image.fromarray(a, 'RGBA').resize((128, 64), Image.NEAREST).save(path)

def deep(seed):
    def ex(u, v, X, Y, t):
        # wave crests: horizontal bands broken up, tile-periodic
        band = np.cos(2 * np.pi * ((u + v) * 1 + 0.35 * np.cos(2 * np.pi * (u - v) * 1 + seed) + 0.2 * np.cos(2*np.pi*(2*u+v)+seed*3)))
        brk = np.cos(2 * np.pi * (1 * (u - v) + 0.33 * (u + v) + seed * .7)) + 0.6*np.cos(2*np.pi*(2*(u-v)+seed))
        t = t.copy()
        t[(band > .72) & (brk > .0)] += 2.6
        t[(band < -.8) & (brk > .3)] -= 1.0
        return t
    return tile(OCEAN, 11 + seed, 2.2, 1.9, ex)
def shallow(seed):
    def ex(u, v, X, Y, t):
        band = np.cos(2 * np.pi * ((u + v) * 1 + 0.3 * np.cos(2 * np.pi * (u - v) + seed)))
        brk = np.cos(2 * np.pi * ((u - v) + 0.5 * (u + v) + seed * .4))
        t = t.copy(); t[(band > .8) & (brk > -.2)] += 1.6
        return t
    return tile(SHAL, 31 + seed, 2.0, 1.6, ex)
def sand(seed):
    def ex(u, v, X, Y, t):
        sp = pnoise(u * 3, v * 3, seed + 5, 6); t = t.copy()
        t[sp > .75] -= 1.3; t[sp < -.78] += 1.0
        return t
    return tile(SAND, 51 + seed, 2.0, 1.5, ex)
def grass(seed):
    def ex(u, v, X, Y, t):
        sp = pnoise(u * 2, v * 2, seed + 9, 6); t = t.copy()
        # blade ticks: short vertical dark/light marks
        t[(sp > .6) & (Y % 2 == 0)] -= 1.5; t[(sp < -.62) & (Y % 2 == 1)] += 1.3
        return t
    return tile(GRASS, 71 + seed, 2.3, 1.7, ex)
def road(seed):
    def ex(u, v, X, Y, t):
        sp = pnoise(u * 3, v * 3, seed + 21, 6); t = t.copy()
        t[sp > .7] -= 1.2; t[sp < -.7] += 1.2   # pebbles
        return t
    return tile(EARTH, 91 + seed, 2.0, 1.2, ex)

def build(out):
    f = {}
    for i in range(3): save_tile(deep(i), f'{out}/deep_water_{i}.png')
    for i in range(3): save_tile(shallow(i), f'{out}/shallow_water_{i}.png')
    for i in range(3): save_tile(sand(i), f'{out}/sand_{i}.png')
    for i in range(4): save_tile(grass(i), f'{out}/grass_{i}.png')
    for i in range(2): save_tile(road(i), f'{out}/road_{i}.png')
