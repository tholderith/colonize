import random
from pxl import *

TW, TH = 64, 32
def mask_rows():
    for y in range(TH):
        w = 4 * min(y, TH - 1 - y) + 4
        yield y, TW // 2 - w // 2, TW // 2 + w // 2 - 1

def tile(base, seed, spots, tufts=None, extra=None):
    s = Spr(TW, TH); rnd = random.Random(seed)
    for y, x0, x1 in mask_rows():
        for x in range(x0, x1 + 1): s.px(x, y, base)
    def inside(x, y):
        return 0 <= y < TH and TW // 2 - (4 * min(y, TH - 1 - y) + 4) // 2 + 1 <= x <= TW // 2 + (4 * min(y, TH - 1 - y) + 4) // 2 - 2
    for col, n, size in spots:
        for _ in range(n):
            x = rnd.randrange(8, 56); y = rnd.randrange(4, 28)
            for dx in range(size):
                for dy in range(max(1, size // 2)):
                    if inside(x + dx, y + dy): s.px(x + dx, y + dy, col)
    if tufts:
        for _ in range(tufts[2]):
            x = rnd.randrange(10, 54); y = rnd.randrange(6, 26)
            if inside(x - 1, y) and inside(x + 1, y):
                s.px(x, y, tufts[0]); s.px(x - 1, y - 1, tufts[1]); s.px(x + 1, y - 1, tufts[1]) if rnd.random() < .7 else None
    if extra: extra(s, rnd, inside)
    return s

def grass(v):
    g = lambda i: C('grass', i)
    return tile(g(3), 100 + v, [(g(2), 7, 4), (g(4), 5, 3), (g(2), 4, 2)], (g(1), g(4), 5 + v)).final()

def sand(v):
    n = lambda i: C('sand', i)
    def ex(s, rnd, ins):
        for _ in range(3 + v):
            x = rnd.randrange(12, 50); y = rnd.randrange(8, 24)
            if ins(x, y) and ins(x + 3, y): s.px(x, y, n(1)); s.px(x + 1, y, n(1))
        for _ in range(2):
            x = rnd.randrange(12, 50); y = rnd.randrange(8, 24)
            if ins(x, y): s.px(x, y, n(4))
    return tile(n(3), 200 + v, [(n(2), 7, 4), (n(4), 4, 3)], None, ex).final()

def water(kind, v):
    w = lambda i: C('water', i)
    if kind == 'deep':
        base, mid, hi = w(1), w(2), w(3)
    else:
        base, mid, hi = w(3), w(4), w(5)
    def ex(s, rnd, ins):
        for _ in range(3):
            x = rnd.randrange(10, 50); y = rnd.randrange(6, 26)
            if ins(x, y) and ins(x + 4, y):
                for i in range(4): s.px(x + i, y, hi if kind == 'deep' else w(6) if i in (1, 2) else hi)
                s.px(x - 1, y + 1, mid); s.px(x + 4, y + 1, mid) if False else None
    return tile(base, 300 + v + (50 if kind == 'deep' else 0), [(mid, 6, 5), (mid, 4, 3)], None, ex).final()

def road(v):
    n = lambda i: C('sand', i); wd = lambda i: C('wood', i)
    def ex(s, rnd, ins):
        for _ in range(9):
            x = rnd.randrange(10, 54); y = rnd.randrange(6, 26)
            if ins(x, y) and ins(x + 1, y): s.px(x, y, n(1)); s.px(x + 1, y, C('stone', 2))
        for _ in range(8):
            x = rnd.randrange(10, 54); y = rnd.randrange(6, 26)
            if ins(x, y): s.px(x, y, n(4))
    return tile(n(2), 400 + v, [(n(1), 6, 4), (n(3), 5, 3)], None, ex).final()
