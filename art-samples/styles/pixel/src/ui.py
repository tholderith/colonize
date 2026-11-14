from pxl import *

G = {}
def _g(ch, rows): G[ch] = rows.split('/')
for ch, r in {
 '0':'.###./#..##/#.#.#/##..#/#...#/#...#/.###.', '1':'..#../.##../..#../..#../..#../..#../.###.', '2':'.###./#...#/....#/...#./..#../.#.../#####',
 '3':'.###./#...#/....#/..##./....#/#...#/.###.', '4':'...#./..##./.#.#./#..#./#####/...#./...#.', '5':'#####/#..../####./....#/....#/#...#/.###.',
 '6':'..##./.#.../#..../####./#...#/#...#/.###.', '7':'#####/....#/...#./..#../..#../..#../..#..', '8':'.###./#...#/#...#/.###./#...#/#...#/.###.',
 '9':'.###./#...#/#...#/.####/....#/...#./.##..',
 'A':'.###./#...#/#...#/#####/#...#/#...#/#...#','B':'####./#...#/#...#/####./#...#/#...#/####.','C':'.###./#...#/#..../#..../#..../#...#/.###.',
 'D':'####./#...#/#...#/#...#/#...#/#...#/####.','E':'#####/#..../#..../####./#..../#..../#####','F':'#####/#..../#..../####./#..../#..../#....',
 'G':'.###./#...#/#..../#.###/#...#/#...#/.###.','H':'#...#/#...#/#...#/#####/#...#/#...#/#...#','I':'.###./..#../..#../..#../..#../..#../.###.',
 'J':'..###/...#./...#./...#./...#./#..#./.##..','K':'#...#/#..#./#.#../##.../#.#../#..#./#...#','L':'#..../#..../#..../#..../#..../#..../#####',
 'M':'#...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#','N':'#...#/##..#/#.#.#/#..##/#...#/#...#/#...#','O':'.###./#...#/#...#/#...#/#...#/#...#/.###.',
 'P':'####./#...#/#...#/####./#..../#..../#....','Q':'.###./#...#/#...#/#...#/#.#.#/#..#./.##.#','R':'####./#...#/#...#/####./#.#../#..#./#...#',
 'S':'.####/#..../#..../.###./....#/....#/####.','T':'#####/..#../..#../..#../..#../..#../..#..','U':'#...#/#...#/#...#/#...#/#...#/#...#/.###.',
 'V':'#...#/#...#/#...#/#...#/#...#/.#.#./..#..','W':'#...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#','X':'#...#/#...#/.#.#./..#../.#.#./#...#/#...#',
 'Y':'#...#/#...#/.#.#./..#../..#../..#../..#..','Z':'#####/....#/...#./..#../.#.../#..../#####',
 ' ':'...../...../...../...../...../...../.....', ':':'...../..#../..#../...../..#../..#../.....', '/':'....#/....#/...#./..#../.#.../#..../#....',
 '.':'...../...../...../...../...../.##../.##..', ',':'...../...../...../...../.##../..#../.#...', '-':'...../...../...../#####/...../...../.....',
 '+':'...../..#../..#../#####/..#../..#../.....', '%':'##..#/##..#/...#./..#../.#.../#..##/#..##', '!':'..#../..#../..#../..#../..#../...../..#..',
 '(':'..#../.#.../#..../#..../#..../.#.../..#..', ')':'..#../...#./....#/....#/....#/...#./..#..', '>':'#..../.#.../..#../...#./..#../.#.../#....',
}.items(): _g(ch, r)

def text(s, x, y, t, col, sh=None):
    cx = x
    for ch in t.upper():
        g = G.get(ch, G[' '])
        for j, row in enumerate(g):
            for i, c in enumerate(row):
                if c == '#':
                    if sh: s.px(cx + i + 1, y + j + 1, sh)
        for j, row in enumerate(g):
            for i, c in enumerate(row):
                if c == '#': s.px(cx + i, y + j, col)
        cx += 6
    return cx
def twidth(t): return 6 * len(t) - 1

W = lambda i: C('wood', i)
def frame(s, x0, y0, x1, y1, fill, hi, lo, edge=INK):
    s.rect(x0, y0, x1, y1, edge); s.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
    s.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, hi); s.rect(x0 + 1, y0 + 1, x0 + 1, y1 - 1, hi)
    s.rect(x0 + 1, y1 - 1, x1 - 1, y1 - 1, lo); s.rect(x1 - 1, y0 + 1, x1 - 1, y1 - 1, lo)

# ---- 12x12 icons, drawn at (x,y) top-left
def ic_gold(s, x, y):
    s.ell(x + 1, y + 1, x + 10, y + 10, C('gold', 0)); s.ell(x + 1, y + 1, x + 9, y + 9, C('gold', 2)); s.ell(x + 3, y + 3, x + 7, y + 7, C('gold', 1))
    s.rect(x + 5, y + 3, x + 5, y + 7, C('gold', 3)); s.px(x + 3, y + 2, C('gold', 3)); s.px(x + 2, y + 3, C('gold', 3))
def ic_wood(s, x, y):
    for yy, c in ((2, 0), (6, 0)):
        s.rect(x + 0, y + yy + 1, x + 9, y + yy + 3, W(2)); s.rect(x + 0, y + yy + 1, x + 9, y + yy + 1, W(3)); s.rect(x + 0, y + yy + 3, x + 9, y + yy + 3, W(1))
        s.ell(x + 7, y + yy, x + 10, y + yy + 4, C('sand', 3)); s.px(x + 8, y + yy + 2, C('sand', 1))
    s.rect(x + 2, y + 9, x + 11, y + 11, W(2)); s.rect(x + 2, y + 9, x + 11, y + 9, W(3)); s.rect(x + 2, y + 11, x + 11, y + 11, W(1)); s.ell(x + 9, y + 8, x + 12, y + 12, C('sand', 3)); s.px(x + 10, y + 10, C('sand', 1))
def ic_brick(s, x, y):
    R = lambda i: C('roof', i)
    for r in range(3):
        for k in range(2):
            xx = x + 1 + k * 5 + (r % 2) * 3 - (3 if r % 2 and k else 0) * 0
            if r % 2: xx = x + 3 + k * 5 - (5 if k == 1 and False else 0)
            if xx + 4 > x + 11: continue
            yy = y + 2 + r * 3
            s.rect(xx, yy, xx + 4, yy + 2, R(3)); s.rect(xx, yy, xx + 4, yy, R(4)); s.rect(xx, yy + 2, xx + 4, yy + 2, R(1))
    s.rect(x + 1, y + 11, x + 10, y + 11, R(0))
def ic_tools(s, x, y):
    s.line((x + 2, y + 10), (x + 8, y + 3), W(3)); s.line((x + 3, y + 10), (x + 9, y + 3), W(2))
    s.rect(x + 5, y + 0, x + 11, y + 3, C('stone', 3)); s.rect(x + 5, y + 0, x + 11, y + 0, C('stone', 4)); s.rect(x + 5, y + 3, x + 11, y + 3, C('stone', 1))
    s.line((x + 1, y + 2), (x + 5, y + 6), C('stone', 2)) 
def ic_food(s, x, y):
    s.ell(x + 0, y + 3, x + 11, y + 10, W(1)); s.ell(x + 0, y + 3, x + 10, y + 9, W(3)); s.ell(x + 2, y + 4, x + 7, y + 7, W(4))
    for k in (3, 6, 9): s.line((k, y + 5), (k - 1, y + 8), W(1)) if False else s.px(x + k - 1, y + 6, W(1))
def ic_cloth(s, x, y):
    b = lambda i: C('slate', i)
    s.rect(x + 1, y + 3, x + 10, y + 10, b(2)); s.rect(x + 1, y + 3, x + 10, y + 3, b(3)); s.rect(x + 1, y + 10, x + 10, y + 10, b(0)); s.rect(x + 10, y + 3, x + 10, y + 10, b(1))
    s.ell(x + 0, y + 1, x + 4, y + 11, b(3)); s.ell(x + 1, y + 3, x + 3, y + 9, b(1)); s.px(x + 2, y + 5, b(2))
    for k in (4, 6, 8): s.px(x + k + 1, y + 6, b(3))
def ic_pop(s, x, y):
    s.ell(x + 3, y + 1, x + 8, y + 6, C('skin', 1)); s.rect(x + 3, y + 1, x + 8, y + 2, W(1)); s.rect(x + 3, y + 1, x + 4, y + 4, W(1))
    s.rect(x + 1, y + 7, x + 10, y + 11, C('grass', 3)); s.rect(x + 1, y + 7, x + 10, y + 7, C('grass', 4)); s.rect(x + 9, y + 7, x + 10, y + 11, C('grass', 1))
ICONS = dict(gold=ic_gold, wood=ic_wood, brick=ic_brick, tools=ic_tools, food=ic_food, cloth=ic_cloth, pop=ic_pop)

def topbar():
    w, h = 960, 36
    s = Spr(w, h)
    s.rect(0, 0, w - 1, h - 1, INK); s.rect(0, 1, w - 1, h - 3, W(1))
    s.rect(0, 1, w - 1, 1, W(3)); s.rect(0, 2, w - 1, 2, W(2))
    for x in range(0, w, 6):   # plank seams (sparse)
        if (x // 6) % 11 == 0: s.rect(x, 3, x, h - 4, W(0))
    s.rect(0, h - 3, w - 1, h - 3, W(0)); s.rect(0, h - 2, w - 1, h - 2, INK)
    res = [('gold', '1250'), ('wood', '438'), ('brick', '112'), ('tools', '36'), ('food', '284'), ('cloth', '57'), ('pop', '142')]
    x = 12
    for k, v in res:
        bw = 78
        frame(s, x, 6, x + bw, 28, C('ink', 1), C('ink', 2), C('ink', 0))
        s.rect(x + 2, 8, x + 15, 26, W(1)) if False else None
        ICONS[k](s, x + 5, 11)
        text(s, x + 21, 13, v, C('sand', 4), C('ink', 0))
        x += bw + 8
    # right: date + speed
    text(s, 800, 8, 'SPRING 1623', C('sand', 3), C('ink', 0)); text(s, 800, 20, 'PAUSED', C('gold', 3), C('ink', 0))
    # speed pips
    for i in range(3): s.rect(910 + i * 12, 18, 917 + i * 12, 25, C('ink', 1)); s.poly([(912 + i * 12, 19), (912 + i * 12, 24), (916 + i * 12, 21.5)], C('gold', 2) if i < 1 else W(2))
    return s.final()

def panel():
    w, h = 180, 150
    s = Spr(w, h)
    frame(s, 0, 0, w - 1, h - 1, W(1), W(3), W(0))
    s.rect(3, 3, w - 4, h - 4, INK)
    pc = lambda i: C('sand', i)
    s.rect(4, 4, w - 5, h - 5, pc(3)); s.rect(4, 4, w - 5, 4, pc(4)); s.rect(4, h - 5, w - 5, h - 5, pc(2))
    # title ribbon
    s.rect(4, 4, w - 5, 20, C('roof', 1)); s.rect(4, 4, w - 5, 4, C('roof', 2)); s.rect(4, 20, w - 5, 20, C('roof', 0))
    text(s, 12, 8, 'HARBOUR WAREHOUSE', C('sand', 4), C('roof', 0))
    s.rect(w - 22, 7, w - 8, 17, INK); s.rect(w - 21, 8, w - 9, 16, C('slate', 1)); s.px(w - 15, 12, C('sand', 4)); s.rect(w - 15, 10, w - 15, 14, pc(4)); s.rect(w - 17, 12, w - 13, 12, pc(4)) if False else None
    text(s, 8, 25, 'STOCK  (CAP 500)', C('stone', 0))
    rows = [('wood', 'TIMBER', 438, 500), ('brick', 'BRICKS', 112, 500), ('tools', 'TOOLS', 36, 100), ('food', 'GRAIN', 284, 500), ('cloth', 'CLOTH', 57, 200)]
    y = 36
    for k, nm, v, cap in rows:
        ICONS[k](s, 8, y)
        text(s, 24, y + 3, nm, C('ink', 1))
        bx = 76
        s.rect(bx, y + 2, bx + 62, y + 9, INK); s.rect(bx + 1, y + 3, bx + 61, y + 8, pc(2))
        fw = int(60 * v / cap)
        col = C('grass', 3) if v / cap > .3 else C('roof', 3)
        s.rect(bx + 1, y + 3, bx + fw, y + 8, col); s.rect(bx + 1, y + 3, bx + fw, y + 3, C('grass', 4) if col == C('grass', 3) else C('roof', 4))
        text(s, bx + 66, y + 3, str(v), C('ink', 1))
        y += 14
    s.rect(8, y + 1, w - 9, y + 1, pc(1)); 
    text(s, 8, y + 6, 'TRADE: 2 SHIPS DOCKED', C('slate', 0))
    text(s, 8, y + 17, 'TAX TO CROWN: 12%', C('roof', 1))
    return s.final()
