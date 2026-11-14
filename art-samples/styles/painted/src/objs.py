import math, random
import numpy as np
from lib import *

# ---------- palette ----------
TERRA = hexc('#c4623e'); TERRA2 = hexc('#a84e32'); THATCH = hexc('#d1a95a'); THATCH2 = hexc('#b8903e')
PLASTER = hexc('#efe0bc'); PLASTER2 = hexc('#e9c9a0'); PLASTER3 = hexc('#d8dcc0')
TIMBER = hexc('#6e4a2c'); TIMBER_L = hexc('#8c6238'); STONE = hexc('#b3a994'); WOODD = hexc('#7a5230')
SLATE = hexc('#5f6a76'); GLASS = hexc('#35566a')
KL, KR, KT = 1.0, .66, 1.12     # left-face / right-face / top light factors

def wallL(c, p, a0, a1, B, z0, z1, color, f=KL, tex=.07, grad=(1.05, .9)):
    q = p.Q((a0, B, z0), (a1, B, z0), (a1, B, z1), (a0, B, z1))
    return c.poly(q, warm(color, f), shade=grad, tex=tex), q
def wallR(c, p, A, b0, b1, z0, z1, color, f=KR, tex=.07, grad=(1.05, .9)):
    q = p.Q((A, b0, z0), (A, b1, z0), (A, b1, z1), (A, b0, z1))
    return c.poly(q, warm(color, f), shade=grad, tex=tex), q

def plaster_strokes(c, m, color, seed):
    c.strokes(m, [mul(color, 1.07), mul(color, .92), mul(color, 1.0)], 90, 7, ang=(-12, 12), width=1.4, alpha=.28, seed=seed)

def lerp(p, q, t): return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

def roof_quad(c, quad, color, kind, seed, f):
    """quad = [eave0, eave1, ridge1, ridge0] screen pts. rows run eave->ridge."""
    col = warm(color, f)
    m = c.poly(quad, col, shade=(1.08, .86), tex=.1)
    e0, e1, r1, r0 = quad
    rows = 7 if kind == 'tile' else 6
    segs = []
    for i in range(1, rows):
        t = i / rows
        segs.append((lerp(e0, r0, t), lerp(e1, r1, t)))
    dark = mul(col, .72 if kind == 'tile' else .8)
    c.lines(segs, dark, width=1.1, alpha=.55, m=m)
    # tile columns / thatch strands along slope direction
    rnd = random.Random(seed)
    segs = []
    n = 16 if kind == 'tile' else 34
    for i in range(n):
        s = rnd.uniform(0, 1)
        a = lerp(e0, e1, s); b = lerp(r0, r1, s)
        t0 = rnd.uniform(0, .8); t1 = min(1, t0 + rnd.uniform(.12, .35))
        segs.append((lerp(a, b, t0), lerp(a, b, t1)))
    if kind == 'tile':
        c.lines(segs, mul(col, .78), width=1.0, alpha=.35, m=m)
        c.lines([(lerp(e0, e1, k / 8 + .03), lerp(e0, e1, k / 8 + .03)) for k in range(0)], col)
    else:
        c.strokes(m, [mul(col, 1.18), mul(col, .78), mul(col, 1.05)], 120, 6, ang=(55, 125), width=1.3, alpha=.4, seed=seed)
        c.lines(segs, mul(col, 1.25), width=1.0, alpha=.4, m=m)
    # eave shadow line + ridge highlight
    c.lines([(e0, e1)], mul(col, .55), width=1.6, alpha=.65)
    c.lines([(r0, r1)], mul(col, 1.3) if kind == 'tile' else mul(col, .7), width=2.0, alpha=.8)
    return m

def gable_roof(c, p, a0, b0, a1, b1, z1, rise, axis, color, kind, over=.07, seed=1, wallcol=PLASTER, trim=TIMBER):
    zr = z1 + rise
    if axis == 'a':
        bm = (b0 + b1) / 2
        tri = p.Q((a1, b0, z1), (a1, b1, z1), (a1, bm, zr))
        m = c.poly(tri, warm(wallcol, KR), shade=(1.05, .9), tex=.07)
        c.strokes(m, [mul(wallcol, .9)], 25, 6, ang=(-10, 10), width=1.3, alpha=.25, seed=seed)
        c.lines([(tri[0], tri[2]), (tri[1], tri[2]), (tri[0], tri[1])], mul(trim, .8), width=1.6, alpha=.9)
        q = p.Q((a0 - over, b1 + over, z1 - 3), (a1 + over, b1 + over, z1 - 3), (a1 + over, bm, zr), (a0 - over, bm, zr))
        roof_quad(c, q, color, kind, seed, 1.08)
        # underside lip
        c.lines([(q[0], q[1])], mul(color, .45), width=2.0, alpha=.7)
        return {'tri': tri, 'quad': q}
    else:
        am = (a0 + a1) / 2
        tri = p.Q((a0, b1, z1), (a1, b1, z1), (am, b1, zr))
        m = c.poly(tri, warm(wallcol, KL), shade=(1.05, .9), tex=.07)
        c.strokes(m, [mul(wallcol, .92)], 25, 6, ang=(-10, 10), width=1.3, alpha=.25, seed=seed)
        c.lines([(tri[0], tri[2]), (tri[1], tri[2]), (tri[0], tri[1])], mul(trim, .8), width=1.6, alpha=.9)
        # right slope (faces a+): eave runs along b at a1+over, ridge at am
        q = p.Q((a1 + over, b1 + over, z1 - 3), (a1 + over, b0 - over, z1 - 3), (am, b0 - over, zr), (am, b1 + over, zr))
        roof_quad(c, q, color, kind, seed, .78)
        c.lines([(q[0], q[1])], mul(color, .4), width=2.0, alpha=.6)
        return {'tri': tri, 'quad': q}

def window(c, p, face, t0, t1, z0, z1, fixed, shutters=None, arch=False):
    if face == 'L': pts = p.Q((t0, fixed, z0), (t1, fixed, z0), (t1, fixed, z1), (t0, fixed, z1))
    else: pts = p.Q((fixed, t0, z0), (fixed, t1, z0), (fixed, t1, z1), (fixed, t0, z1))
    m = c.poly(pts, mix(GLASS, hexc('#f2d58a'), .25), shade=(.9, 1.1), tex=.05)
    # glint
    c.lines([(lerp(pts[0], pts[3], .25), lerp(pts[1], pts[2], .25))], hexc('#d9f0f0'), width=1.0, alpha=.45)
    c.lines([(pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[3]), (pts[3], pts[0])], mul(TIMBER, .8), width=1.3, alpha=.95)
    c.lines([(lerp(pts[0], pts[1], .5), lerp(pts[3], pts[2], .5))], mul(TIMBER, .8), width=1.0, alpha=.9)
    if shutters is not None:
        w = t1 - t0
        for s in (-1, 1):
            if face == 'L':
                tt0, tt1 = (t0 - w * .45, t0 - .005) if s < 0 else (t1 + .005, t1 + w * .45)
                sp = p.Q((tt0, fixed, z0), (tt1, fixed, z0), (tt1, fixed, z1), (tt0, fixed, z1))
            else:
                tt0, tt1 = (t0 - w * .45, t0 - .005) if s < 0 else (t1 + .005, t1 + w * .45)
                sp = p.Q((fixed, tt0, z0), (fixed, tt1, z0), (fixed, tt1, z1), (fixed, tt0, z1))
            c.poly(sp, warm(shutters, KL if face == 'L' else KR), tex=.05)
    return m

def door(c, p, face, t0, t1, z1, fixed, color=WOODD, f=None):
    f = f or (KL if face == 'L' else KR)
    if face == 'L': pts = p.Q((t0, fixed, 0), (t1, fixed, 0), (t1, fixed, z1), (t0, fixed, z1))
    else: pts = p.Q((fixed, t0, 0), (fixed, t1, 0), (fixed, t1, z1), (fixed, t0, z1))
    c.poly(pts, warm(color, f), shade=(1.1, .8), tex=.08)
    c.lines([(pts[0], pts[3]), (pts[3], pts[2]), (pts[2], pts[1])], mul(TIMBER, .6), width=1.5, alpha=.9)
    c.lines([(lerp(pts[0], pts[1], .5), lerp(pts[3], pts[2], .5))], mul(color, .6), width=1.0, alpha=.6)

def timber_frame(c, p, face, t0, t1, z0, z1, fixed, n=3, diag=True, color=TIMBER):
    f = KL if face == 'L' else KR
    def P(t, z): return p.P(t, fixed, z) if face == 'L' else p.P(fixed, t, z)
    segs = []
    segs += [(P(t0, z0), P(t1, z0)), (P(t0, z1), P(t1, z1)), (P(t0, z0), P(t0, z1)), (P(t1, z0), P(t1, z1))]
    for i in range(1, n):
        t = t0 + (t1 - t0) * i / n
        segs.append((P(t, z0), P(t, z1)))
    if diag:
        for i in range(n):
            ta = t0 + (t1 - t0) * i / n; tb = t0 + (t1 - t0) * (i + 1) / n
            segs.append((P(ta, z0), P(tb, z1)) if i % 2 == 0 else (P(ta, z1), P(tb, z0)))
    c.lines(segs, warm(color, f), width=2.0, alpha=.95)

def ao_base(c, p, a0, b0, a1, b1, alpha=.38, grow=.18, grass=True, seed=0):
    """ambient-occlusion ground contact + grass tufts around base; shadow cast to lower-right."""
    q = p.Q((a0 - grow, b0 - grow, 0), (a1 + grow, b0 - grow, 0), (a1 + grow, b1 + grow, 0), (a0 - grow, b1 + grow, 0))
    c.shadow(q, alpha, blur=5, color=(30, 34, 20))

def cast_shadow(c, p, a0, b0, a1, b1, h, alpha=.26):
    """parallelogram shadow thrown toward +x(screen)/+a,+b? light upper-left -> shadow toward lower-right (screen +x,+y)."""
    dx, dy = h * .55, h * .28
    q = p.Q((a0, b0, 0), (a1, b0, 0), (a1, b1, 0), (a0, b1, 0))
    top = [(x + dx, y + dy) for x, y in q]
    pts = [q[0], q[1], top[1], top[2], top[3], q[3]]
    # convex hull of base + offset base
    allp = q + top
    hull = convex_hull(allp)
    c.shadow(hull, alpha, blur=3, color=(25, 32, 50))

def convex_hull(pts):
    pts = sorted(set(pts))
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for q in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    up = []
    for q in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0: up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]

def tufts(c, pts_list, seed=0, n=1):
    rnd = random.Random(seed)
    segs = []; cols = []
    for (x, y) in pts_list:
        for _ in range(5):
            dx = rnd.uniform(-6, 6); L = rnd.uniform(4, 9)
            segs.append(((x + dx * .3, y), (x + dx, y - L)))
    c.lines(segs, hexc('#6f9a40'), width=1.4, alpha=.9)
    segs2 = [((a[0] + 1, a[1]), (b[0] + 1.5, b[1] + 1)) for a, b in segs[::2]]
    c.lines(segs2, hexc('#9cc15a'), width=1.2, alpha=.8)

def edge_tufts(c, p, a0, b0, a1, b1, seed=0, k=7):
    rnd = random.Random(seed); pts = []
    for i in range(k):
        t = rnd.uniform(0, 1)
        pts.append(p.P(a0 + (a1 - a0) * t, b1 + .04, 0))
        pts.append(p.P(a1 + .04, b0 + (b1 - b0) * rnd.uniform(0, 1), 0))
    tufts(c, pts, seed)

def chimney(c, p, a, b, z0, z1, w=.09):
    # small stone chimney (box)
    pl = wallL(c, p, a - w, a + w, b + w, z0, z1, STONE)[0]
    wallR(c, p, a + w, b - w, b + w, z0, z1, STONE, f=KR)
    top = p.Q((a - w, b - w, z1), (a + w, b - w, z1), (a + w, b + w, z1), (a - w, b + w, z1))
    c.poly(top, mul(STONE, .85), tex=.05)
    # smoke puffs
    x, y = p.P(a, b, z1)
    for i, (dx, dy, r, al) in enumerate([(2, -8, 5, .55), (6, -18, 7, .4), (12, -30, 9, .28)]):
        c.shadow_ellipse(x + dx, y + dy, r, r * .85, alpha=al, blur=2.5, color=(235, 232, 226))

# ---------- trees / rocks ----------
def tree(variant, seed):
    p = Iso(1, 1, 150, mx=20)
    c = p.canvas(seed + variant * 17)
    cx, cy = p.P(.5, .5, 0)
    rnd = random.Random(seed * 31 + variant)
    c.shadow_ellipse(cx + 12, cy + 4, 30, 11, alpha=.3, blur=4, color=(24, 36, 30))
    if variant == 3:  # pine / cypress
        c.poly([(cx - 3, cy + 2), (cx + 3, cy + 2), (cx + 2, cy - 20), (cx - 2, cy - 20)], hexc('#6a4a2e'), tex=.1)
        cols = [hexc('#3f6e46'), hexc('#4a7e4c'), hexc('#58904f')]
        for i, (zy, r) in enumerate([(-18, 22), (-40, 19), (-62, 15), (-82, 11)]):
            for j in range(3):
                c.sphere(cx + (j - 1) * r * .45, cy + zy + abs(j - 1) * 6, r * .62, cols[i % 3], tex=.18)
            c.sphere(cx - 2, cy + zy - 5, r * .75, mix(cols[i % 3], hexc('#9cc060'), .1), tex=.18)
    else:
        # trunk
        tw = 4 + (variant == 1) * 1
        c.poly([(cx - tw, cy + 3), (cx + tw, cy + 3), (cx + tw * .6, cy - 30), (cx - tw * .6, cy - 30)], hexc('#6e4b2d'), shade=(1.1, .8), tex=.12)
        c.poly([(cx + tw * .2, cy + 3), (cx + tw, cy + 3), (cx + tw * .6, cy - 30), (cx + tw * .1, cy - 30)], hexc('#4a321f'), alpha=.5)
        greens = [hexc('#3f7a3e'), hexc('#4d8c3f'), hexc('#5c9a43'), hexc('#76ad4a')]
        if variant == 1: greens = [hexc('#4a7f3a'), hexc('#5d9340'), hexc('#7aa944'), hexc('#a4b84a')]
        if variant == 2: greens = [hexc('#356f44'), hexc('#42824a'), hexc('#559a50'), hexc('#6cae58')]
        blobs = []
        spread = {0: 26, 1: 22, 2: 30}[variant]
        topy = {0: -62, 1: -72, 2: -56}[variant]
        for i in range(9):
            ang = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(0, 1) ** .6 * spread
            bx = cx + math.cos(ang) * rr * 1.0; by = cy + topy + math.sin(ang) * rr * .62 + 12
            blobs.append((by, bx, rnd.uniform(15, 21)))
        blobs.sort()
        # draw lower/back first by y then bottom
        for by, bx, r in blobs:
            g = greens[0] if by > cy + topy + 14 else greens[1]
            c.sphere(bx, by, r, g, tex=.2, ry=r * .92)
        for i in range(5):
            bx = cx + rnd.uniform(-spread * .7, spread * .45); by = cy + topy + rnd.uniform(-8, 10)
            c.sphere(bx, by, rnd.uniform(11, 15), greens[2 + (i % 2)], tex=.22)
        # leaf dabs
        m = c.mask(convex_hull([(bx + dx, by + dy) for by, bx, r in blobs for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r))])) * (c.a > .5)
        c.strokes(m, [greens[3], mix(greens[3], hexc('#f0e07a'), .4), greens[0]], 160, 4, ang=(200, 340), width=1.5, alpha=.5, seed=seed)
    c.outline(color=(32, 50, 28), alpha=.5)
    return c.to_image(), p.anchor

def rock(variant, seed):
    p = Iso(1, 1, 60, mx=16)
    c = p.canvas(seed + variant)
    cx, cy = p.P(.5, .5, 0)
    c.shadow_ellipse(cx + 10, cy + 4, 24, 9, alpha=.32, blur=3, color=(24, 30, 40))
    rnd = random.Random(variant * 5 + 2)
    if variant == 0: parts = [(-8, -6, 17, 1.0), (10, -1, 12, .9), (-1, -14, 11, .9)]
    else: parts = [(0, -5, 18, .85), (-13, 0, 10, .8), (12, -2, 9, .8)]
    base = hexc('#9c9484')
    for dx, dy, r, k in parts:
        c.sphere(cx + dx, cy + dy, r, mix(base, hexc('#a89c88'), rnd.random()), tex=.28, ry=r * .8)
    m = (c.a > .5).astype(np.float32)
    c.strokes(m, [hexc('#c9c2b0'), hexc('#6d6a62')], 40, 6, ang=(-40, 40), width=1.3, alpha=.35, seed=variant)
    tufts(c, [(cx - 18, cy + 4), (cx + 17, cy + 5)], seed)
    c.outline(color=(40, 36, 32), alpha=.5)
    return c.to_image(), p.anchor

# ---------- houses ----------
def house(variant, seed=0):
    p = Iso(1, 1, 130, mx=24)
    c = p.canvas(41 + variant)
    ao_base(c, p, .14, .14, .86, .86)
    if variant == 0:      # plaster cottage, terracotta, ridge along a
        a0, b0, a1, b1, h = .16, .22, .84, .78, 34
        cast_shadow(c, p, a0, b0, a1, b1, h + 12)
        wallL(c, p, a0, a1, b1, 0, h, PLASTER); wallR(c, p, a1, b0, b1, 0, h, PLASTER)
        timber_frame(c, p, 'L', a0, a1, 0, h, b1, n=4, diag=False)
        timber_frame(c, p, 'R', b0, b1, 0, h, a1, n=3, diag=False)
        door(c, p, 'L', .24, .4, 22, b1)
        window(c, p, 'L', .55, .7, 14, 27, b1, shutters=hexc('#4f8a74'))
        window(c, p, 'R', .4, .58, 14, 27, a1, shutters=hexc('#4f8a74'))
        gable_roof(c, p, a0, b0, a1, b1, h, 30, 'a', TERRA, 'tile', seed=3, wallcol=PLASTER)
        chimney(c, p, .32, .42, h + 14, h + 38)
    elif variant == 1:    # thatch cottage, darker timber-clad, ridge along b
        a0, b0, a1, b1, h = .2, .16, .8, .84, 30
        cast_shadow(c, p, a0, b0, a1, b1, h + 14)
        wallL(c, p, a0, a1, b1, 0, h, PLASTER2); wallR(c, p, a1, b0, b1, 0, h, PLASTER2)
        timber_frame(c, p, 'L', a0, a1, 0, h, b1, n=3, diag=True)
        timber_frame(c, p, 'R', b0, b1, 0, h, a1, n=4, diag=True)
        door(c, p, 'R', .55, .72, 22, a1)
        window(c, p, 'L', .36, .52, 13, 25, b1)
        window(c, p, 'R', .24, .38, 13, 25, a1)
        gable_roof(c, p, a0, b0, a1, b1, h, 34, 'b', THATCH, 'thatch', over=.1, seed=5, wallcol=PLASTER2)
    else:                 # narrow two-storey, ochre plaster, slate-ish/terra roof, gable front on b
        a0, b0, a1, b1, h = .26, .14, .74, .86, 50
        cast_shadow(c, p, a0, b0, a1, b1, h + 12)
        wallL(c, p, a0, a1, b1, 0, h, hexc('#e7c98f')); wallR(c, p, a1, b0, b1, 0, h, hexc('#e7c98f'))
        # jettied band
        for (z0, z1) in ((24, 27),):
            c.lines([(p.P(a0, b1, z0), p.P(a1, b1, z0))], mul(TIMBER, .9), width=2.2)
            c.lines([(p.P(a1, b1, z0), p.P(a1, b0, z0))], mul(TIMBER, .7), width=2.2)
        timber_frame(c, p, 'L', a0, a1, 27, h, b1, n=2, diag=False)
        timber_frame(c, p, 'R', b0, b1, 27, h, a1, n=4, diag=False)
        door(c, p, 'L', .38, .55, 22, b1)
        window(c, p, 'L', .3, .42, 32, 45, b1, shutters=hexc('#b5513a'))
        window(c, p, 'L', .6, .72, 32, 45, b1, shutters=hexc('#b5513a'))
        window(c, p, 'R', .3, .48, 28, 43, a1, shutters=hexc('#b5513a'))
        window(c, p, 'R', .3, .48, 8, 20, a1)
        gable_roof(c, p, a0, b0, a1, b1, h, 32, 'b', hexc('#b4503a'), 'tile', over=.06, seed=9, wallcol=hexc('#e7c98f'))
        chimney(c, p, .5, .3, h + 14, h + 42, w=.08)
    edge_tufts(c, p, .1, .1, .9, .9, seed=variant + 1)
    c.outline()
    return c.to_image(), p.anchor

def farmhouse(seed=0):
    p = Iso(1, 1, 120, mx=26)
    c = p.canvas(77)
    ao_base(c, p, .1, .1, .9, .9)
    a0, b0, a1, b1, h = .14, .2, .84, .8, 32
    cast_shadow(c, p, a0, b0, a1, b1, h + 12)
    wallL(c, p, a0, a1, b1, 0, h, hexc('#a9522f'), tex=.1); wallR(c, p, a1, b0, b1, 0, h, hexc('#a9522f'), tex=.1)
    # plank lines
    for i in range(1, 8):
        z = i * 4
        c.lines([(p.P(a0, b1, z), p.P(a1, b1, z))], hexc('#6d2f1c'), width=1.0, alpha=.35)
        c.lines([(p.P(a1, b0, z), p.P(a1, b1, z))], hexc('#4a1e12'), width=1.0, alpha=.35)
    timber_frame(c, p, 'L', a0, a1, 0, h, b1, n=1, diag=False, color=PLASTER)
    # big barn door with X
    d = [p.P(.3, b1, 0), p.P(.55, b1, 0), p.P(.55, b1, 24), p.P(.3, b1, 24)]
    c.poly(d, warm(hexc('#8a5a34'), KL), shade=(1.1, .8))
    c.lines([(d[0], d[2]), (d[1], d[3]), (d[0], d[1]), (d[3], d[2]), (d[0], d[3]), (d[1], d[2])], PLASTER, width=1.5, alpha=.85)
    window(c, p, 'R', .35, .5, 13, 25, a1)
    gable_roof(c, p, a0, b0, a1, b1, h, 26, 'a', hexc('#7a6a56'), 'tile', over=.08, seed=7, wallcol=hexc('#a9522f'), trim=PLASTER)
    # hay stack
    hx, hy = p.P(.22, .78 + .12, 0)
    c.shadow_ellipse(hx + 8, hy + 2, 14, 5, alpha=.3, blur=2)
    c.sphere(hx, hy - 7, 10, hexc('#e0bd5c'), tex=.25, ry=11)
    c.poly([(hx - 10, hy - 6), (hx + 10, hy - 6), (hx + 8, hy + 1), (hx - 8, hy + 1)], hexc('#d0aa4c'), tex=.2)
    c.sphere(hx, hy - 12, 7, hexc('#ecca6c'), tex=.25)
    edge_tufts(c, p, .1, .1, .9, .9, seed=11)
    c.outline()
    return c.to_image(), p.anchor

def windmill(seed=0):
    p = Iso(1, 1, 210, mx=40)
    c = p.canvas(88)
    cx, cy = p.P(.5, .5, 0)
    ao_base(c, p, .12, .12, .88, .88)
    c.shadow([(cx - 18, cy), (cx + 18, cy), (cx + 64, cy + 30), (cx + 22, cy + 18)], .22, blur=3, color=(25, 32, 50))
    # tapered round tower: sides from base ellipse to top ellipse
    rb, rt, hh = 28, 17, 96
    def tower_shape(c, z0, z1, r0, r1, col, tex=.1):
        n = 40
        yy0, yy1 = cy - z0, cy - z1
        m_side = c.mask([(cx - r0, yy0), (cx + r0, yy0), (cx + r1, yy1), (cx - r1, yy1)])
        m_b = c.ellipse_mask(cx, yy0, r0, r0 * .5)
        m = np.clip(m_side + m_b, 0, 1)
        yy, xx = np.mgrid[0:c.H, 0:c.W].astype(np.float32)
        # horizontal shading across cylinder: lit left
        t = np.clip((xx / S - (cx - r0)) / (2 * r0), 0, 1)
        f = 1.18 - .72 * t ** 1.2
        field = (np.asarray(col, np.float32)[None, None, :] * (f[..., None] * (1 + tex * c.nz[..., None])))
        field = field + (1 - f[..., None]).clip(0, 1) * np.array([-5, -2, 12], np.float32) * 2
        c.comp(m, np.clip(field, 0, 255))
        return m
    m = tower_shape(c, 0, hh, rb, rt, STONE)
    # stone courses
    segs = []
    for i in range(1, 12):
        z = i * hh / 12; r = rb + (rt - rb) * z / hh
        segs.append(((cx - r, cy - z), (cx + r, cy - z + 0)))
    c.lines(segs, hexc('#6f6656'), width=1.0, alpha=.35, m=m)
    c.strokes(m, [hexc('#cfc7b2'), hexc('#8b8272')], 160, 7, ang=(-5, 5), width=1.5, alpha=.35, seed=9)
    # door + window
    door(c, p, 'L', .45, .6, 20, .62) if False else None
    c.poly([(cx - 8, cy + 1), (cx + 8, cy + 1), (cx + 8, cy - 18), (cx, cy - 25), (cx - 8, cy - 18)], hexc('#6b4528'), shade=(1.1, .75))
    c.poly([(cx - 4, cy - 52), (cx + 4, cy - 52), (cx + 4, cy - 64), (cx - 4, cy - 64)], GLASS)
    # cap (conical wooden/terracotta roof)
    zc = hh
    c.poly([(cx - rt - 5, cy - zc), (cx + rt + 5, cy - zc), (cx + 2, cy - zc - 34)], hexc('#9b5a34'), shade=(1.15, .85), tex=.12)
    c.poly([(cx - rt - 5, cy - zc), (cx - 2, cy - zc - 33), (cx, cy - zc - 34), (cx - 2, cy - zc)], hexc('#c07a48'), alpha=.6)
    c.shadow_ellipse(cx, cy - zc, rt + 5, 6, alpha=.0)
    c.lines([((cx - rt - 5, cy - zc), (cx + rt + 5, cy - zc))], hexc('#4c2c1a'), width=2.0, alpha=.7)
    # sails: hub toward front-left(+a/+b screen: down). hub on tower front
    hx, hy = cx, cy - zc + 6
    c.sphere(hx, hy, 6, hexc('#7a5230'), tex=.1)
    ang0 = math.radians(20)
    for k in range(4):
        ang = ang0 + k * math.pi / 2
        dx, dy = math.cos(ang), math.sin(ang) * .86
        L = 72
        # spar
        ex, ey = hx + dx * L, hy + dy * L
        px_, py_ = -dy, dx
        w = 9
        sail = [(hx + dx * 14 + px_ * 2, hy + dy * 14 + py_ * 2), (ex + px_ * 2, ey + py_ * 2),
                (ex + px_ * (w + 2), ey + py_ * (w + 2) ), (hx + dx * 14 + px_ * w, hy + dy * 14 + py_ * w)]
        lit = 1.1 if dx < 0 else .88
        c.poly(sail, warm(hexc('#efe4c8'), lit), tex=.08, alpha=.96)
        segs = [((hx + dx * (14 + i * 8) + px_ * 2, hy + dy * (14 + i * 8) + py_ * 2), (hx + dx * (14 + i * 8) + px_ * w, hy + dy * (14 + i * 8) + py_ * w)) for i in range(1, 8)]
        c.lines(segs, hexc('#8c7a58'), width=1.0, alpha=.7)
        c.lines([((hx, hy), (ex, ey))], hexc('#5b3d22'), width=2.6)
        c.lines([((hx + dx * 14 + px_ * w, hy + dy * 14 + py_ * w), (ex + px_ * (w + 2), ey + py_ * (w + 2)))], hexc('#5b3d22'), width=1.2, alpha=.8)
    c.sphere(hx - 1, hy - 1, 4.5, hexc('#a07040'), tex=.1)
    # base tufts + wheat sacks
    tufts(c, [(cx - 30, cy + 8), (cx + 32, cy + 9), (cx - 10, cy + 15), (cx + 12, cy + 16)], 4)
    c.outline()
    return c.to_image(), p.anchor

def lumberjack(seed=0):
    p = Iso(1, 1, 100, mx=30)
    c = p.canvas(99)
    ao_base(c, p, .1, .1, .9, .9)
    a0, b0, a1, b1, h = .14, .08, .62, .56, 24
    cast_shadow(c, p, a0, b0, a1, b1, h + 10)
    wallL(c, p, a0, a1, b1, 0, h, hexc('#a47a4a'), tex=.14); wallR(c, p, a1, b0, b1, 0, h, hexc('#a47a4a'), tex=.14)
    for i in range(1, 6):
        z = i * 4.5
        c.lines([(p.P(a0, b1, z), p.P(a1, b1, z))], hexc('#5e3d22'), width=1.0, alpha=.4)
        c.lines([(p.P(a1, b0, z), p.P(a1, b1, z))], hexc('#3f2814'), width=1.0, alpha=.4)
    door(c, p, 'L', .26, .42, 17, b1, color=hexc('#4f331c'))
    window(c, p, 'R', .2, .36, 11, 20, a1)
    gable_roof(c, p, a0, b0, a1, b1, h, 22, 'a', THATCH2, 'thatch', over=.1, seed=2, wallcol=hexc('#a47a4a'), trim=hexc('#5e3d22'))
    # log pile (stacked logs; ends face left-lower) at front right
    lx, ly = p.P(.58, .88, 0)
    c.shadow_ellipse(lx + 12, ly + 3, 24, 7, alpha=.3, blur=2.5)
    rows = [(0, 3), (1, 2), (2, 1)]
    for rrow in range(3):
        for k in range(3 - rrow):
            x = lx - 10 + k * 11 + rrow * 5.5; y = ly - 4 - rrow * 8
            # log body going toward upper-right (along -b)
            c.poly([(x, y - 5), (x + 14, y - 12), (x + 14, y - 2), (x, y + 5)], hexc('#8a5d34'), shade=(1.1, .85), tex=.2)
            c.circle(x, y, 5.2, hexc('#d9b27a'), tex=.2)
            c.circle(x, y, 3.0, hexc('#c49860'), tex=.1)
            c.circle(x, y, 1.0, hexc('#8a6238'))
    # chopping block + axe
    bx, by = p.P(.88, .5, 0)
    c.poly([(bx - 5, by - 7), (bx + 5, by - 7), (bx + 5, by), (bx - 5, by)], hexc('#8a5d34'), tex=.2)
    c.shadow_ellipse(bx, by - 7, 5, 2.5, alpha=1, blur=0.2, color=(214, 178, 118))
    c.lines([((bx + 1, by - 9), (bx + 8, by - 20))], hexc('#5e3d22'), width=1.6)
    c.poly([(bx + 6, by - 20), (bx + 12, by - 18), (bx + 9, by - 14)], hexc('#aeb4b8'))
    edge_tufts(c, p, .1, .05, .9, .9, seed=3, k=4)
    c.outline()
    return c.to_image(), p.anchor

def chapel(seed=0):
    p = Iso(2, 2, 250, mx=30)
    c = p.canvas(123)
    ao_base(c, p, .2, .2, 1.8, 1.8, alpha=.34)
    stone = hexc('#ecdfc6'); stone2 = hexc('#cfc4ac')
    # nave: ridge along a (axis a)
    a0, b0, a1, b1, h = .35, .5, 1.75, 1.35, 46
    cast_shadow(c, p, a0, b0, a1, 1.9, 100, alpha=.22)
    wallL(c, p, a0, a1, b1, 0, h, stone); wallR(c, p, a1, b0, b1, 0, h, stone)
    # buttresses + arched windows on left wall
    for ta in (.62, .98, 1.34):
        q = p.Q((ta - .04, b1 + .02, 0), (ta + .04, b1 + .02, 0), (ta + .04, b1 + .02, h - 4), (ta - .04, b1 + .02, h - 4))
        c.poly(q, warm(stone2, KL), tex=.1)
    for ta in (.8, 1.16, 1.52):
        w = .07
        pts = p.Q((ta - w, b1, 14), (ta + w, b1, 14), (ta + w, b1, 30), (ta, b1, 36), (ta - w, b1, 30))
        c.poly(pts, mix(hexc('#3d6a86'), hexc('#f2d58a'), .3), shade=(.9, 1.1))
        c.lines([(pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[3]), (pts[3], pts[4]), (pts[4], pts[0])], mul(stone2, .55), width=1.3)
        c.lines([(p.P(ta, b1, 14), p.P(ta, b1, 34))], mul(stone2, .55), width=1.0)
    # base course
    c.lines([(p.P(a0, b1, 4), p.P(a1, b1, 4))], mul(stone2, .7), width=1.5, alpha=.7)
    # right gable end window
    pts = p.Q((a1, .78, 18), (a1, .98, 18), (a1, .98, 34), (a1, .88, 42), (a1, .78, 34))
    c.poly(pts, mix(hexc('#3d6a86'), hexc('#f2d58a'), .3))
    gable_roof(c, p, a0, b0, a1, b1, h, 36, 'a', TERRA, 'tile', over=.07, seed=21, wallcol=stone)
    # bell tower at front (a ~0.35..0.8, b 1.15..1.6)? put tower at left/south corner of nave front
    ta0, tb0, ta1, tb1, th = .22, 1.2, .78, 1.76, 96
    wallL(c, p, ta0, ta1, tb1, 0, th, stone); wallR(c, p, ta1, tb0, tb1, 0, th, stone, f=KR)
    # quoins/bands
    for z in (30, 64):
        c.lines([(p.P(ta0, tb1, z), p.P(ta1, tb1, z))], mul(stone2, .7), width=1.4, alpha=.7)
        c.lines([(p.P(ta1, tb1, z), p.P(ta1, tb0, z))], mul(stone2, .5), width=1.4, alpha=.7)
    door_pts = p.Q((.4, tb1, 0), (.6, tb1, 0), (.6, tb1, 26), (.5, tb1, 33), (.4, tb1, 26))
    c.poly(door_pts, warm(hexc('#5e3d22'), KL), shade=(1.1, .8))
    c.lines([(door_pts[0], door_pts[4]), (door_pts[4], door_pts[3]), (door_pts[3], door_pts[2]), (door_pts[2], door_pts[1])], mul(stone2, .5), width=1.5)
    # belfry opening
    bp = p.Q((.42, tb1, 70), (.58, tb1, 70), (.58, tb1, 88), (.5, tb1, 94), (.42, tb1, 88))
    c.poly(bp, hexc('#2a3a46'))
    bx, by = p.P(.5, tb1, 76)
    c.circle(bx, by, 3, hexc('#d8b04a'))
    bp2 = p.Q((ta1, 1.38, 70), (ta1, 1.58, 70), (ta1, 1.58, 88), (ta1, 1.48, 94), (ta1, 1.38, 88))
    c.poly(bp2, hexc('#1f2d38'))
    # pointed spire (pyramid)
    sa, sb = (ta0 + ta1) / 2, (tb0 + tb1) / 2
    ap = p.P(sa, sb, th + 62)
    cor = p.Q((ta0 - .05, tb1 + .05, th - 2), (ta1 + .05, tb1 + .05, th - 2), (ta1 + .05, tb0 - .05, th - 2))
    c.poly([cor[0], cor[1], ap], warm(hexc('#b7573a'), 1.1), shade=(1.1, .85), tex=.1)
    c.poly([cor[1], cor[2], ap], warm(hexc('#b7573a'), .72), shade=(1.1, .85), tex=.1)
    c.lines([(cor[0], ap), (cor[1], ap)], hexc('#e6a070'), width=1.0, alpha=.4)
    c.lines([(cor[0], cor[1])], hexc('#5c2a1a'), width=2.0, alpha=.7)
    # cross
    c.lines([((ap[0], ap[1]), (ap[0], ap[1] - 18)), ((ap[0] - 5, ap[1] - 12), (ap[0] + 5, ap[1] - 12))], hexc('#e8c25a'), width=2.2)
    # steps + small garden fence
    st = p.Q((.34, tb1 + .12, 0), (.66, tb1 + .12, 0), (.66, tb1 + .12, 3), (.34, tb1 + .12, 3))
    c.poly(st, warm(stone2, 1.0), tex=.1)
    edge_tufts(c, p, .2, .5, 1.8, 1.85, seed=5, k=14)
    c.outline()
    return c.to_image(), p.anchor

def crate(c, x, y, s, col=hexc('#b08850')):
    c.poly([(x - s, y - s * .5), (x, y), (x, y - s * 1.2), (x - s, y - s * 1.7)], warm(col, 1.0), shade=(1.1, .9), tex=.15)
    c.poly([(x, y), (x + s, y - s * .5), (x + s, y - s * 1.7), (x, y - s * 1.2)], warm(col, .68), tex=.15)
    c.poly([(x - s, y - s * 1.7), (x, y - s * 1.2), (x + s, y - s * 1.7), (x, y - s * 2.2)], warm(col, 1.15), tex=.15)
    c.lines([((x - s, y - s * 1.1), (x, y - s * .65)), ((x, y - s * .65), (x + s, y - s * 1.1))], mul(col, .55), width=1.1, alpha=.8)

def barrel(c, x, y, r=6, h=11):
    c.shadow_ellipse(x + 5, y + 1, r + 3, r * .5, alpha=.28, blur=1.5)
    c.poly([(x - r, y - h), (x + r, y - h), (x + r + 1, y - h / 2), (x + r, y), (x - r, y), (x - r - 1, y - h / 2)], hexc('#9a6a3a'), shade=(1.1, .8), tex=.15)
    c.poly([(x - r * .3, y - h), (x + r, y - h), (x + r + 1, y - h / 2), (x + r, y), (x + r * .3, y)], hexc('#6a4424'), alpha=.45)
    c.shadow_ellipse(x, y - h, r, r * .45, alpha=1, blur=0.2, color=(188, 142, 86))
    c.lines([((x - r, y - h * .72), (x + r, y - h * .72)), ((x - r - 1, y - h * .3), (x + r + 1, y - h * .3))], hexc('#3a3a40'), width=1.3, alpha=.8)

def warehouse(seed=0):
    p = Iso(2, 2, 200, mx=34)
    c = p.canvas(131)
    ao_base(c, p, .2, .25, 1.85, 1.9, alpha=.34)
    a0, b0, a1, b1, h = .3, .3, 1.7, 1.6, 52
    cast_shadow(c, p, a0, b0, a1, b1, 76, alpha=.24)
    wc = hexc('#b98a56')
    wallL(c, p, a0, a1, b1, 0, h, wc, tex=.12); wallR(c, p, a1, b0, b1, 0, h, hexc('#a5784a'), tex=.12, f=KR)
    # plank lines
    for i in range(1, 12):
        z = i * 4.4
        c.lines([(p.P(a0, b1, z), p.P(a1, b1, z))], hexc('#5a3a20'), width=1.0, alpha=.3)
        c.lines([(p.P(a1, b0, z), p.P(a1, b1, z))], hexc('#3a2410'), width=1.0, alpha=.3)
    for i in range(0, 8):
        t = a0 + (a1 - a0) * i / 7
        c.lines([(p.P(t, b1, 0), p.P(t, b1, h))], hexc('#5a3a20'), width=1.0, alpha=.22)
    # stone plinth
    q = p.Q((a0, b1, 0), (a1, b1, 0), (a1, b1, 8), (a0, b1, 8)); c.poly(q, warm(STONE, KL), tex=.1)
    q = p.Q((a1, b0, 0), (a1, b1, 0), (a1, b1, 8), (a1, b0, 8)); c.poly(q, warm(STONE, KR), tex=.1)
    # timber posts
    posts = []
    for t in np.linspace(a0, a1, 5): posts.append((p.P(t, b1, 0), p.P(t, b1, h)))
    c.lines(posts, hexc('#4c3220'), width=2.6, alpha=.95)
    posts = [(p.P(a1, t, 0), p.P(a1, t, h)) for t in np.linspace(b0, b1, 4)]
    c.lines(posts, hexc('#34210f'), width=2.6, alpha=.9)
    # big double doors with arch on left wall, shuttered loading hatch up top
    d = p.Q((.78, b1, 0), (1.22, b1, 0), (1.22, b1, 34), (1.0, b1, 40), (.78, b1, 34))
    c.poly(d, warm(hexc('#6a4424'), KL), shade=(1.1, .8))
    c.lines([(d[0], d[4]), (d[4], d[3]), (d[3], d[2]), (d[2], d[1]), (p.P(1.0, b1, 0), p.P(1.0, b1, 40))], hexc('#3a2410'), width=1.6)
    c.lines([(p.P(.78, b1, 17), p.P(1.22, b1, 17))], hexc('#3a2410'), width=1.2, alpha=.6)
    hat = p.Q((1.4, b1, 30), (1.55, b1, 30), (1.55, b1, 44), (1.4, b1, 44))
    c.poly(hat, hexc('#4f331c'), shade=(1.1, .8))
    window(c, p, 'R', .62, .78, 22, 38, a1)
    window(c, p, 'R', 1.2, 1.36, 22, 38, a1)
    # roof ridge along a, big hip-ish gable, with dormer? + tile
    gable_roof(c, p, a0, b0, a1, b1, h, 40, 'a', hexc('#b9553a'), 'tile', over=.1, seed=33, wallcol=hexc('#a5784a'), trim=hexc('#4c3220'))
    # hoist beam on gable end & hanging rope
    # crates & barrels at the front/left (dockside)
    for (qa, qb, s) in [(.35, 1.78, 11), (.55, 1.9, 9)]:
        crate(c, *p.P(qa, qb, 0), s)
    crate(c, *p.P(.42, 1.86, 20) if False else p.P(.42, 1.86, 0), 8)
    for (qa, qb) in [(1.55, 1.78), (1.72, 1.82), (1.64, 1.9)]:
        barrel(c, *p.P(qa, qb, 0))
    # sacks
    for (qa, qb) in [(1.9, .9), (1.9, 1.05), (1.9, 1.2)]:
        sx, sy = p.P(qa, qb, 0)
        c.sphere(sx, sy - 5, 6, hexc('#dccaa0'), tex=.2, ry=6)
        c.poly([(sx - 2, sy - 11), (sx + 2, sy - 11), (sx + 1, sy - 8), (sx - 1, sy - 8)], hexc('#b8a47a'))
    edge_tufts(c, p, .2, .2, 1.8, 1.85, seed=12, k=10)
    c.outline()
    return c.to_image(), p.anchor
