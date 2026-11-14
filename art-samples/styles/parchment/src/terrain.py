from art import *
from scipy.ndimage import gaussian_filter

SEA_D = (112, 146, 134); SEA_S = (156, 188, 168); SAND = (226, 205, 152); GRASS = (178, 190, 132); ROAD = (206, 176, 128)
W, H = 128, 64
def diamond(grow=1.0):
    return [(64, 0 - grow), (128 + grow, 32), (64, 64 + grow), (0 - grow, 32)]

def tile(kind, seed):
    a = A(W, H, (64, 64), seed)
    r = a.rng
    base = {"deep": SEA_D, "shallow": SEA_S, "sand": SAND, "grass": GRASS, "road": GRASS}[kind]
    base = shade(base, r.uniform(.985, 1.015))
    a.wash(diamond(2.6), base, pool=0, grain=10)
    inner = lambda f: [(64, 32 - 30 * f), (64 + 62 * f, 32), (64, 32 + 30 * f), (64 - 62 * f, 32)]
    def pt():
        while True:
            x, y = r.uniform(12, 116), r.uniform(8, 56)
            if abs(x - 64) / 52 + abs(y - 32) / 25 < 1: return x, y
    if kind in ("deep", "shallow"):
        n = 11 if kind == "deep" else 6
        for _ in range(n):
            x, y = pt(); L = r.uniform(6, 11) if kind == "deep" else r.uniform(5, 9)
            col = INK2 if kind == "deep" else (110, 130, 110)
            # little wave: a flat 'w' stroke
            a.line([(x - L, y), (x - L / 2, y - 2.2), (x, y), (x + L / 2, y - 2.2), (x + L, y)], .8, col, .25, alpha=150 if kind == "deep" else 120)
        if kind == "deep":
            for _ in range(4):
                x, y = pt(); a.hatch([(x - 8, y - 3), (x + 8, y - 3), (x + 8, y + 3), (x - 8, y + 3)], 0, 1.7, INK2, .6, 90)
    elif kind == "sand":
        a.stipple(inner(.95), 130, INK2, .55, 150)
        for _ in range(3):
            x, y = pt(); a.line([(x - 3, y), (x + 3, y + .5)], .7, INK2, .2, alpha=110)
    elif kind == "grass":
        for _ in range(16):
            x, y = pt()
            for dx in (-1.6, 0, 1.6):
                a.line([(x + dx, y), (x + dx * 1.7, y - r.uniform(2.6, 4.2))], .75, (96, 110, 66), .15, alpha=210)
        a.stipple(inner(.95), 50, (116, 128, 80), .6, 150)
    elif kind == "road":
        # dirt ribbon fills the whole diamond (neighbours are road/grass), ragged via stipples
        a.wash(inner(1.0), ROAD, pool=0, grain=12)
        a.stipple(inner(.95), 110, INK2, .7, 170)
        for _ in range(5):
            x, y = pt(); a.ellipse((x, y), 2.6, 1.3, (176, 150, 112), True, .6)
    return a

def build(out):
    for k, n in (("deep", 2), ("shallow", 2), ("sand", 2), ("grass", 4), ("road", 2)):
        for i in range(n):
            tile(k, hash(k) % 100 + i * 31 + 5).save(f"{out}/{k}_{i}.png")
