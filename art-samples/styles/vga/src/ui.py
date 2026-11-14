"""Period-document UI: bevelled wood/grey frames, parchment ledger plates, woodcut icons, own caps font."""
import numpy as np
from PIL import Image
from gfx import dith, B4, SCALE
from pal import *
import font

class Im:
    def __init__(s, w, h): s.w, s.h = w, h; s.a = np.zeros((h, w, 4), np.uint8)
    def put(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h: s.a[y, x] = (*c, 255)
    def rect(s, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): s.put(x, y, c)
    def drect(s, x0, y0, x1, y1, ramp_, tone):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = tone(x, y) if callable(tone) else tone
                s.put(x, y, dith(ramp_, t, x, y))
    def frame(s, x0, y0, x1, y1, hi, lo, inset=False):
        if inset: hi, lo = lo, hi
        for x in range(x0, x1 + 1): s.put(x, y0, hi); s.put(x, y1, lo)
        for y in range(y0, y1 + 1): s.put(x0, y, hi); s.put(x1, y, lo)
    def grid(s, x, y, rows, pal):
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch in pal: s.put(x + i, y + j, pal[ch])
    def text(s, x, y, t, col, sh=None):
        from PIL import Image as I
        im = I.fromarray(s.a, 'RGBA').copy(); font.text(im, x, y, t, col, sh); s.a = np.array(im).copy()
    def save(s, p):
        Image.fromarray(s.a, 'RGBA').resize((s.w * SCALE, s.h * SCALE), Image.NEAREST).save(p)

def parch(im, x0, y0, x1, y1, seed=0):
    im.drect(x0, y0, x1, y1, PARCH, lambda x, y: 2.7 + 0.5 * np.sin(x * .9 + seed) * np.cos(y * 1.3) + (0.5 if (x * 5 + y * 11 + seed) % 23 == 0 else 0) - (0.6 if (x + y * 2) % 29 == 0 else 0))
    im.frame(x0, y0, x1, y1, PARCH[0], PARCH[1])
def bevel_panel(im, x0, y0, x1, y1):
    im.drect(x0, y0, x1, y1, WOOD, lambda x, y: 1.6 + 0.5 * ((x + y) % 2) * .6 + (0.35 if (y % 3 == 0) else 0))
    im.frame(x0, y0, x1, y1, STONE[4], INK)
    im.frame(x0 + 1, y0 + 1, x1 - 1, y1 - 1, WOOD[4], WOOD[0])
    im.frame(x0 + 2, y0 + 2, x1 - 2, y1 - 2, WOOD[0], WOOD[3])

K = INK
IC = {
 'gold': (["..kkkkk..",".kGGGGGk.","kGyyyyyGk","kGyGGGyGk","kGyGyGyGk","kGyGGGyGk","kGyyyyyGk",".kGGGGGk.","..kkkkk.."],
          {'k': K, 'G': GOLD[1], 'y': GOLD[3]}),
 'wood': (["..........",".kkkkkkk..","kWWWWWWkk","kwWWWWWwk","kWwkwWWWk","kWkwkWWWk",".kWwWWWkk","..kkkkkk.","........."],
          {'k': K, 'W': WOOD[3], 'w': WOOD[4]}),
 'brick': (["kkkkkkkkk","kRRkRRRRk","kkkkkkkkk","kRRRRkRRk","kkkkkkkkk","kRRkRRRRk","kkkkkkkkk",".........","........."],
          {'k': K, 'R': BRICK[3]}),
 'tools': (["...kkkk..","..kSSSSk.","..kSSSSk.",".kWkkkk..","kWWk.....","kWk......","kk.......",".........","........."],
          {'k': K, 'S': STONE[4], 'W': WOOD[4]}),
 'food': (["....k....","...kyk...","..kyyyk..",".kyykyyk.","kyyk.kyyk","..kkWkk..","...kWk...","..kkWkk..",".........",],
          {'k': K, 'y': GOLD[2], 'W': WOOD[3]}),
 'cloth': (["..kkkkkkk","..kBBBBBk",".kBBBbBBk","kBBBbBBkk","kBBbBBkBk","kBBBBBkBk","kBBBBkBBk",".kkkkkkkk","........."],
          {'k': K, 'B': COATB[2], 'b': PLAST[3]}),
 'pop': (["...kkk...","..kSSSk..","..kSSSk..","...kkk...",".kkRRRkk.","kRRRRRRRk","kRRRRRRRk","kkkkkkkkk","........."],
          {'k': K, 'S': SKIN[2], 'R': COATB[2]}),
}
def icon(im, x, y, name):
    rows, pal = IC[name]; im.grid(x, y, rows, pal)

def topbar():
    W, H = 480, 18
    im = Im(W, H)
    bevel_panel(im, 0, 0, W - 1, H - 1)
    # left plate: date
    items = [('gold', '1248'), ('wood', '124'), ('brick', '37'), ('tools', '18'), ('food', '96'), ('cloth', '22'), ('pop', '212')]
    x = 4
    # emblem plate (original: ship's wheel)
    im.rect(x, 3, x + 11, 14, STONE[2]); im.frame(x, 3, x + 11, 14, STONE[5], INK)
    cxx, cyy = x + 6, 9
    for dx, dy in [(0,-4),(0,4),(-4,0),(4,0),(3,-3),(-3,3),(3,3),(-3,-3)]: im.put(cxx+dx, cyy+dy, GOLD[2])
    for dx, dy in [(0,-2),(0,2),(-2,0),(2,0),(1,-2),(-1,2),(2,1),(-2,-1),(-1,-2),(1,2),(2,-1),(-2,1)]: im.put(cxx+dx, cyy+dy, GOLD[1])
    im.put(cxx, cyy, GOLD[3])
    x += 16
    for name, val in items:
        w = 51
        parch(im, x, 2, x + w - 1, 15, seed=x)
        im.frame(x - 1, 1, x + w, 16, INK, INK)
        icon(im, x + 3, 4, name)
        im.text(x + 14, 6, val, WOOD[0])
        x += w + 4
    # right: date plate
    parch(im, x, 2, W - 5, 15, 3); im.frame(x - 1, 1, W - 4, 16, INK, INK)
    im.text(x + 4, 6, "YEAR 1612", ROOF[1])
    return im

def panel():
    W, H = 90, 75
    im = Im(W, H)
    bevel_panel(im, 0, 0, W - 1, H - 1)
    parch(im, 5, 5, W - 6, H - 6, 7)
    im.frame(5, 5, W - 6, H - 6, INK, INK)
    # title ribbon
    im.rect(7, 7, W - 8, 15, ROOF[2]); im.frame(7, 7, W - 8, 15, ROOF[3], ROOF[0])
    t = "WAREHOUSE"; im.text((W - font.width(t)) // 2, 9, t, PLAST[4], ROOF[0])
    im.rect(7, 16, W - 8, 16, INK)
    rows = [('wood', 'TIMBER', 124, 200), ('brick', 'BRICKS', 37, 200), ('tools', 'TOOLS', 18, 60), ('food', 'GRAIN', 96, 200), ('cloth', 'CLOTH', 22, 100)]
    y = 19
    for name, lab, v, m in rows:
        icon(im, 8, y, name)
        im.text(19, y, lab, WOOD[0])
        s = f"{v}"
        im.text(W - 9 - font.width(s) , y, s, ROOF[1])
        im.rect(19, y + 7, W - 10, y + 8, INK)
        n = int((W - 30) * v / m)
        im.rect(20, y + 7, 19 + n, y + 7, GRASS[3] if v / m > .25 else RED); im.rect(20, y + 8, 19 + n, y + 8, GRASS[1] if v / m > .25 else ROOF[1])
        y += 10
    return im

def build(out, A):
    topbar().save(f'{out}/ui_topbar.png'); panel().save(f'{out}/ui_panel.png')
