from art import *

def new(w, h, anchor, seed): return A(w, h, anchor, seed)
WALL = (238, 224, 192); ROOFS = [(178, 100, 70), (190, 126, 80), (150, 112, 92)]
LEAF = [(142, 166, 108), (126, 154, 104), (160, 172, 110)]
WOOD = (172, 130, 88)

def shadow(a, c, rx, ry):
    pts = [(c[0] + math.cos(t / 12 * 6.283) * rx, c[1] + math.sin(t / 12 * 6.283) * ry) for t in range(12)]
    a.hatch(pts, 20, 2.2, INK2, .55, 110)

def tree(i):
    a = new(80, 110, (40, 100), 100 + i); b = (40, 68)
    shadow(a, (b[0] + 6, b[1] + 1), 13, 5)
    if i == 2:  # conifer
        a.poly([(b[0] - 2, b[1]), (b[0] + 2, b[1]), (b[0] + 2, b[1] - 12), (b[0] - 2, b[1] - 12)], (130, 96, 64), w=.9)
        for k, (w_, y0) in enumerate([(19, 6), (15, 24), (11, 40)]):
            tri = [(b[0] - w_, b[1] - y0 - 8), (b[0] + w_, b[1] - y0 - 8), (b[0], b[1] - y0 - 30)]
            a.poly(tri, shade((108, 140, 100), 1 - .0 * k)); a.hatch([(b[0], tri[0][1]), tri[1], tri[2]], 70, 2.4, alpha=130)
    else:
        a.poly([(b[0] - 2.5, b[1]), (b[0] + 2.5, b[1]), (b[0] + 2, b[1] - 20), (b[0] - 2, b[1] - 20)], (130, 96, 64), w=.9)
        col = LEAF[i]
        for dx, dy, r_ in [(-9, -34, 13), (9, -36, 13), (0, -46, 15), (-2, -30, 14)]:
            a.ellipse((b[0] + dx, b[1] + dy), r_, r_ * .88, col, True, 1.0)
        a.hatch([(b[0] - 8, b[1] - 40), (b[0] + 20, b[1] - 40), (b[0] + 20, b[1] - 18), (b[0] - 8, b[1] - 18)], 65, 2.7, alpha=70)
        a.stipple([(b[0] - 20, b[1] - 60), (b[0] + 20, b[1] - 60), (b[0] + 20, b[1] - 20), (b[0] - 20, b[1] - 20)], 40, (84, 108, 70), .7)
    return a

def rock():
    a = new(64, 56, (32, 52), 7); b = (32, 36)
    shadow(a, (b[0] + 3, b[1] + 3), 17, 6)
    a.poly([(b[0] - 18, b[1] + 2), (b[0] - 12, b[1] - 12), (b[0] + 2, b[1] - 18), (b[0] + 16, b[1] - 8), (b[0] + 20, b[1] + 2), (b[0] + 4, b[1] + 6)], (200, 190, 168))
    a.hatch([(b[0] - 2, b[1] - 16), (b[0] + 20, b[1] - 4), (b[0] + 20, b[1] + 3), (b[0] + 4, b[1] + 6), (b[0] - 2, b[1] - 4)], 55, 2.2, alpha=170)
    a.line([(b[0] - 12, b[1] - 6), (b[0] - 4, b[1] - 2)], .8)
    a.poly([(b[0] - 22, b[1] + 3), (b[0] - 17, b[1] - 3), (b[0] - 10, b[1] + 2), (b[0] - 12, b[1] + 6)], (190, 180, 158))
    return a

def house(i):
    a = new(128, 112, (64, 100), 20 + i)
    sx, sy = [(.2, .22), (.18, .24), (.22, .2)][i]
    x0, x1, y0, y1 = sx, .8 - (.05 if i == 1 else 0), sy, 1 - sy
    shadow(a, a.P(.6, .7, 0), 34, 11)
    box(a, x0, y0, x1, y1, 0, 26, WALL)
    door(a, x0 + .14 + .1 * i, y1, 0, .13, 16)
    window(a, x0 + .5, y1, 10, .12, 9)
    window(a, x1, y1 - .2, 9, .12, 9, right=True)
    gable(a, x0, y0, x1, y1, 26, 54, ROOFS[i])
    ch = a.P(x1 - .12, y0 + .3, 44)
    a.poly([(ch[0] - 3, ch[1]), (ch[0] + 3, ch[1]), (ch[0] + 3, ch[1] - 11), (ch[0] - 3, ch[1] - 11)], (190, 170, 150), w=.9)
    # smoke curl
    a.line([(ch[0], ch[1] - 12), (ch[0] + 3, ch[1] - 18), (ch[0] - 2, ch[1] - 24), (ch[0] + 3, ch[1] - 30)], .8, INK2, .4, alpha=150)
    return a

def farmhouse():
    a = new(128, 120, (64, 108), 40)
    shadow(a, a.P(.55, .7, 0), 42, 13)
    box(a, .1, .2, .9, .85, 0, 24, (232, 214, 176))
    door(a, .4, .85, 0, .2, 17, col=(130, 92, 60))
    window(a, .18, .85, 10, .12, 9); window(a, .9, .6, 9, .12, 9, right=True)
    gable(a, .1, .2, .9, .85, 24, 52, (206, 170, 98), over=.06)
    a.hatch(a.P(.5, .5, 0) and [a.P(.1, .85, 22), a.P(.9, .85, 22), a.P(.9, .52, 48), a.P(.1, .52, 48)], 80, 2.0, alpha=80)
    return a

def windmill():
    a = new(160, 190, (80, 150), 41)
    shadow(a, a.P(.5, .5, 0), 30, 10)
    c = (0.5, 0.5)
    P = lambda x, y, h: a.P(x, y, h)
    bot = lambda t: [(c[0] - .3 * t, c[1] - .3 * t), (c[0] + .3 * t, c[1] - .3 * t), (c[0] + .3 * t, c[1] + .3 * t), (c[0] - .3 * t, c[1] + .3 * t)]
    # tapered tower approximated with 2 faces
    l = [P(.2, .8, 0), P(.8, .8, 0), P(.7, .7, 92), P(.3, .7, 92)]
    r = [P(.8, .8, 0), P(.8, .2, 0), P(.7, .3, 92), P(.7, .7, 92)]
    a.poly(l, (240, 228, 200)); a.poly(r, (214, 196, 164)); a.hatch(r, 64, 2.4, alpha=130)
    for k in range(1, 6):
        h_ = k * 15; a.line([P(.8 - .02 * k, .8 - .02 * k, h_), P(.8 - .02 * k, .2 + .02 * k, h_)], .5, INK2, alpha=90)
    door(a, .44, .8, 0, .12, 18)
    cap = [P(.28, .72, 92), P(.72, .72, 92), P(.5, .5, 112)]
    a.poly(cap, (150, 100, 76)); a.hatch(cap, 20, 2.4, alpha=110)
    hub = P(.5, .75, 84)
    a.line([(hub[0] - 52, hub[1] - 10), (hub[0] + 54, hub[1] + 10)], 1.4)
    for sgn in (1, -1):
        e = (hub[0] + 33 * sgn * math.cos(.55), hub[1] - 52 * sgn * math.sin(.4) * 1)
    ang0 = 0.7
    for k in range(4):
        t = ang0 + k * math.pi / 2
        ex, ey = hub[0] + math.cos(t) * 50, hub[1] + math.sin(t) * 50 * .95
        nx, ny = -math.sin(t) * 9, math.cos(t) * 9
        sail = [(hub[0] + math.cos(t) * 12, hub[1] + math.sin(t) * 12), (ex, ey), (ex + nx, ey + ny), (hub[0] + math.cos(t) * 12 + nx, hub[1] + math.sin(t) * 12 + ny)]
        a.poly(sail, (236, 226, 196), w=.9, pool=.1); a.hatch(sail, math.degrees(t) + 90, 2.6, alpha=90)
        a.line([hub, (ex, ey)], 1.3)
    a.ellipse(hub, 3.2, 3.2, (140, 100, 70), True, .9)
    return a

def lumberjack():
    a = new(128, 100, (64, 90), 42)
    shadow(a, a.P(.5, .6, 0), 36, 12)
    box(a, .12, .2, .6, .72, 0, 18, (186, 144, 98))
    a.hatch(a.P(0, 0, 0) and [a.P(.12, .72, 0), a.P(.6, .72, 0), a.P(.6, .72, 18), a.P(.12, .72, 18)], 90, 3, alpha=110)
    door(a, .26, .72, 0, .15, 13)
    gable(a, .12, .2, .6, .72, 18, 38, (140, 108, 76))
    # log pile
    for k, (gx, gy, h) in enumerate([(.7, .75, 3), (.7, .6, 3), (.7, .45, 3), (.7, .68, 9), (.7, .52, 9), (.7, .6, 15)]):
        p = a.P(gx + .1, gy, h)
        a.ellipse(p, 5, 3.2, (196, 156, 104), True, .8)
        a.ellipse((p[0] + 5, p[1]), 2.4, 2.8, (222, 190, 140), True, .6)
    return a

def chapel():
    fw = fh = 2
    a = new(256, 230, (128, 215), 43)
    P = lambda x, y, h: a.P(x, y, h, 2, 2)
    shadow(a, P(1.2, 1.2, 0), 70, 22)
    box(a, .4, .7, 1.3, 1.5, 0, 38, (244, 234, 208), 2, 2)
    for k in range(3):
        window(a, .55 + .26 * k, 1.5, 14, .1, 16, 2, 2)
    door(a, .78, 1.5, 0, .2, 22, 2, 2, (130, 92, 60))
    gable(a, .4, .7, 1.3, 1.5, 38, 72, (170, 98, 74), 2, 2)
    # tower
    box(a, 1.3, .9, 1.78, 1.38, 0, 78, (236, 224, 196), 2, 2)
    window(a, 1.46, 1.38, 52, .1, 16, 2, 2)
    top = [P(1.26, 1.42, 78), P(1.82, 1.42, 78), P(1.82, .86, 78), P(1.26, .86, 78)]
    sp = [P(1.26, 1.42, 78), P(1.82, 1.42, 78), P(1.54, 1.14, 142)]
    sp2 = [P(1.82, 1.42, 78), P(1.82, .86, 78), P(1.54, 1.14, 142)]
    a.poly(sp, (170, 98, 74)); a.poly(sp2, (140, 80, 62)); a.hatch(sp2, 60, 2.2, alpha=140); a.hatch(sp, 20, 2.4, alpha=100)
    t = P(1.54, 1.14, 142)
    a.line([t, (t[0], t[1] - 14)], 1.3); a.line([(t[0] - 4, t[1] - 9), (t[0] + 4, t[1] - 9)], 1.3)
    return a

def warehouse():
    a = new(256, 190, (128, 178), 44)
    P = lambda x, y, h: a.P(x, y, h, 2, 2)
    shadow(a, P(1.1, 1.1, 0), 76, 24)
    box(a, .25, .35, 1.65, 1.55, 0, 40, (214, 184, 140), 2, 2)
    a.hatch([P(.25, 1.55, 0), P(1.65, 1.55, 0), P(1.65, 1.55, 40), P(.25, 1.55, 40)], 90, 3.2, INK2, .6, 100)
    door(a, .8, 1.55, 0, .45, 30, 2, 2, (120, 84, 56))
    a.line([P(1.025, 1.55, 0), P(1.025, 1.55, 30)], .8)
    window(a, 1.35, 1.55, 18, .1, 11, 2, 2); window(a, .45, 1.55, 18, .1, 11, 2, 2)
    gable(a, .25, .35, 1.65, 1.55, 40, 70, (160, 104, 76), 2, 2, over=.06)
    # crates and barrels at front-right
    for gx, gy in [(1.78, 1.5), (1.78, 1.2)]:
        p = P(gx, gy, 0)
        a.poly([(p[0] - 6, p[1]), (p[0] + 6, p[1]), (p[0] + 6, p[1] - 12), (p[0] - 6, p[1] - 12)], (170, 128, 84), w=.9)
        a.ellipse((p[0], p[1] - 12), 6, 2.6, (190, 150, 100), True, .8)
        a.line([(p[0] - 6, p[1] - 5), (p[0] + 6, p[1] - 5)], .7)
    return a

def wheat():
    a = new(256, 128, (128, 128), 45)
    P = lambda x, y: a.P(x, y, 0, 2, 2)
    out = [P(.08, .08), P(1.92, .08), P(1.92, 1.92), P(.08, 1.92)]
    a.wash(out, (214, 188, 112), pool=.15, grain=12)
    # furrows along y
    n = 12
    for k in range(n + 1):
        x = .16 + (1.68) * k / n
        a.line([P(x, .14), P(x, 1.86)], .8, (150, 116, 60), .35, alpha=190)
        for j in range(8):
            y = .22 + j * .2 + (.05 if k % 2 else 0)
            p = P(x, y); a.line([(p[0], p[1]), (p[0], p[1] - 4.5)], .8, (122, 92, 44), .1)
            a.line([(p[0] - 1.6, p[1] - 3), (p[0], p[1] - 5.5), (p[0] + 1.6, p[1] - 3)], .6, (122, 92, 44), .1, alpha=200)
    a.line(out + [out[0]], 1.2, INK, 1.0)
    # dotted hedge border
    for k in range(40):
        t = k / 40
        for e0, e1 in [(out[0], out[1]), (out[1], out[2]), (out[2], out[3]), (out[3], out[0])]:
            x, y = e0[0] + (e1[0] - e0[0]) * t, e0[1] + (e1[1] - e0[1]) * t
            a.ellipse((x, y), 1.4, 1.0, (128, 150, 96), False)
    return a

def pier():
    a = new(128, 64, (64, 64), 46)
    P = lambda x, y, h=0: a.P(x, y, h)
    # deck along x axis (down-right), from x=-0.3 beyond edge is clipped by canvas; draw a bit extended
    y0, y1 = .34, .66
    deck = [P(-.1, y0, 6), P(1.15, y0, 6), P(1.15, y1, 6), P(-.1, y1, 6)]
    side = [P(-.1, y1, 6), P(1.15, y1, 6), P(1.15, y1, 0), P(-.1, y1, 0)]
    a.poly(side, (130, 96, 64)); a.poly(deck, (190, 150, 104))
    for k in range(14):
        x = -.05 + k * .09
        a.line([P(x, y0, 6), P(x, y1, 6)], .7, INK2, .2, alpha=190)
    a.line([P(-.1, .5, 6), P(1.15, .5, 6)], .5, INK2, alpha=90)
    for x in (.0, .35, .7, 1.05):
        for yy in (y0 - .04, y1 + .04):
            p = P(x, yy, 6); a.poly([(p[0] - 1.8, p[1]), (p[0] + 1.8, p[1]), (p[0] + 1.8, p[1] + 14), (p[0] - 1.8, p[1] + 14)], (112, 80, 54), w=.8)
    return a

def ship():
    a = new(256, 230, (128, 200), 47)
    P = lambda x, y, h=0: a.P(x, y, h, 2, 2)
    # water ripple
    for k in range(5):
        p = P(.3 + k * .3, 1.35, 0)
        a.line([(p[0] - 14, p[1] + 4), (p[0] - 7, p[1] + 1), (p[0], p[1] + 4), (p[0] + 7, p[1] + 1), (p[0] + 14, p[1] + 4)], .8, INK2, .3, alpha=120)
    xs = [.15 + k * .1 for k in range(17)]  # stern .15 -> bow 1.75
    def sheer(x): return 26 + 9 * ((x - .15) / 1.6) ** 2 * 1.0 + (6 if x < .5 else 0)
    def half(x): t = (x - .15) / 1.6; return .27 * math.sin(math.pi * min(1, t * 0.92 + .04)) ** .7
    def keel(x): t = (x - .15) / 1.6; return 3 + 10 * (1 - math.sin(math.pi * t)) 
    gy = 1.0
    near = [P(x, gy + half(x), sheer(x)) for x in xs]
    nearb = [P(x, gy + half(x) * .55, keel(x)) for x in reversed(xs)]
    hull = near + nearb
    far = [P(x, gy - half(x), sheer(x)) for x in xs]
    a.poly(far + [P(1.78, gy, sheer(1.75))] + list(reversed(near)), (120, 88, 62))  # deck/inner area
    a.poly(hull, (150, 108, 72)); a.hatch(hull, 4, 2.0, alpha=110)
    a.line(near, 1.4)
    # white stripe / gunports
    for x in xs[2:-2:2]:
        p = P(x, gy + half(x) * .95, sheer(x) - 8); a.poly([(p[0] - 2, p[1] - 2), (p[0] + 2, p[1] - 2), (p[0] + 2, p[1] + 2), (p[0] - 2, p[1] + 2)], (60, 44, 34), False)
    # bowsprit
    a.line([P(1.75, gy, sheer(1.75) - 2), P(2.05, gy, sheer(1.75) + 14)], 1.5)
    # masts and sails
    masts = [(.55, 92, .34), (1.0, 112, .38), (1.4, 94, .33)]
    for mx, mh, mw in masts:
        base = P(mx, gy, sheer(mx) - 4)
        a.line([base, (base[0], base[1] - mh)], 2.0, INK, .2)
        for lvl, (h0, h1) in enumerate([(.0, .58), (.62, .96)]):
            hb = sheer(mx) + mh * h0 * .85 + 8; ht = sheer(mx) + mh * h1 * .85
            w_ = mw * (1 - .25 * lvl)
            bill = .06
            sail = [P(mx + bill * .5, gy - w_, ht), P(mx + bill, gy, ht - 3), P(mx + bill * .5, gy + w_, ht),
                    P(mx + bill * .5, gy + w_, hb), P(mx + bill, gy, hb + 2), P(mx + bill * .5, gy - w_, hb)]
            a.poly(sail, (240, 230, 200), w=1.0, pool=.12, grain=8)
            a.hatch(sail, 75, 3.2, alpha=75)
            a.line([P(mx, gy - w_ - .04, ht + 1), P(mx, gy + w_ + .04, ht + 1)], 1.1)
        pen = [P(mx, gy, sheer(mx) + mh * .85 + 6)]
        tp = (base[0], base[1] - mh)
        a.poly([tp, (tp[0] + 13, tp[1] + 3), (tp[0], tp[1] + 6)], (170, 70, 56), w=.8)  # plain red pennant
    # rigging
    b1 = P(.55, gy, sheer(.55)); b2 = P(1.4, gy, sheer(1.4))
    a.line([(b1[0], b1[1] - 92), P(1.75, gy, sheer(1.75) + 10)], .5, INK2, alpha=160)
    a.line([(b1[0], b1[1] - 92), P(.2, gy, sheer(.2))], .5, INK2, alpha=160)
    return a

def cart():
    a = new(96, 72, (48, 64), 48)
    b = (48, 40)
    shadow(a, (b[0], b[1] + 5), 22, 7)
    # ox (left-lower side), cart behind
    bed = [(b[0] - 4, b[1] - 4), (b[0] + 20, b[1] + 8), (b[0] + 20, b[1] - 2), (b[0] - 4, b[1] - 14)]
    a.poly([(b[0] - 14, b[1] - 6), (b[0] + 10, b[1] - 18), (b[0] + 22, b[1] - 12), (b[0] - 2, b[1] + 0)], (190, 150, 100))
    a.poly([(b[0] - 14, b[1] - 6), (b[0] - 2, b[1] + 0), (b[0] - 2, b[1] - 8), (b[0] - 14, b[1] - 14)], (160, 120, 80))
    a.poly([(b[0] - 2, b[1] + 0), (b[0] + 22, b[1] - 12), (b[0] + 22, b[1] - 20), (b[0] - 2, b[1] - 8)], (140, 102, 70)); 
    for k in range(5):  # hay
        x = b[0] - 8 + k * 5; a.line([(x, b[1] - 12 + k), (x + 2, b[1] - 20 + k * .5)], 1.3, (206, 176, 96), .3)
    a.ellipse((b[0] + 6, b[1] + 0), 7, 7, (160, 120, 80), True, 1.0); a.ellipse((b[0] + 6, b[1]), 1.5, 1.5, INK, False)
    a.line([(b[0] + 6, b[1] - 6), (b[0] + 6, b[1] + 6)], .6); a.line([(b[0], b[1]), (b[0] + 12, b[1])], .6)
    # ox
    ox = (b[0] - 26, b[1] + 3)
    a.poly([(ox[0] - 8, ox[1] - 6), (ox[0] + 8, ox[1] - 8), (ox[0] + 9, ox[1] + 0), (ox[0] - 7, ox[1] + 2)], (170, 130, 96))
    a.ellipse((ox[0] - 10, ox[1] - 8), 4, 3.4, (160, 120, 88), True, .9)
    a.line([(ox[0] - 12, ox[1] - 11), (ox[0] - 15, ox[1] - 14)], 1.0); a.line([(ox[0] - 9, ox[1] - 11), (ox[0] - 7, ox[1] - 15)], 1.0)
    for dx in (-5, 5): a.line([(ox[0] + dx, ox[1]), (ox[0] + dx, ox[1] + 7)], 1.3)
    a.line([(ox[0] + 8, ox[1] - 4), (b[0] - 12, b[1] - 6)], .8)
    return a

def colonist(i=0):
    a = new(32, 48, (16, 40), 50)
    b = (16, 30)
    coat = (150, 78, 64)
    a.hatch([(b[0] - 5, b[1] + 2), (b[0] + 9, b[1] + 3), (b[0] + 8, b[1] + 5), (b[0] - 5, b[1] + 5)], 20, 1.6, INK2, .5, 100)
    for dx in (-2, 2): a.line([(b[0] + dx, b[1] - 4), (b[0] + dx, b[1] + 3)], 1.6)
    a.poly([(b[0] - 5, b[1] - 3), (b[0] + 5, b[1] - 3), (b[0] + 3, b[1] - 16), (b[0] - 3, b[1] - 16)], coat, w=.9, grain=6)
    a.line([(b[0] - 4, b[1] - 14), (b[0] - 7, b[1] - 6)], 1.3); a.line([(b[0] + 4, b[1] - 14), (b[0] + 7, b[1] - 7)], 1.3)
    a.ellipse((b[0], b[1] - 20), 3.2, 3.4, (232, 200, 160), True, .8)
    a.poly([(b[0] - 6, b[1] - 22), (b[0] + 6, b[1] - 22), (b[0] + 3, b[1] - 28), (b[0] - 3, b[1] - 28)], (96, 72, 54), w=.8, grain=0)
    return a

def build(out):
    for i in range(3): tree(i).save(f"{out}/tree_{i}.png")
    rock().save(f"{out}/rock.png")
    for i in range(3): house(i).save(f"{out}/house_{i}.png")
    farmhouse().save(f"{out}/farmhouse.png"); windmill().save(f"{out}/windmill.png"); lumberjack().save(f"{out}/lumberjack.png")
    chapel().save(f"{out}/chapel.png"); warehouse().save(f"{out}/warehouse.png"); wheat().save(f"{out}/wheat.png")
    pier().save(f"{out}/pier.png"); ship().save(f"{out}/ship.png"); cart().save(f"{out}/cart.png"); colonist().save(f"{out}/colonist.png")
