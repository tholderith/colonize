import math, random
import numpy as np
from lib import *
from objs import *

def wheat(seed=0):
    p = Iso(2, 2, 40, mx=6)
    c = p.canvas(201)
    q = p.Q((.02, .02), (1.98, .02), (1.98, 1.98), (.02, 1.98)) if False else [p.P(.04, .04), p.P(1.96, .04), p.P(1.96, 1.96), p.P(.04, 1.96)]
    m = c.poly(q, hexc('#8a6a3e'), shade=(1.1, .9), tex=.2)
    # furrows along a: rows at constant b
    rnd = random.Random(3)
    nrows = 10
    for i in range(nrows):
        b = .14 + i * (1.72 / (nrows - 1))
        c0, c1 = p.P(.12, b), p.P(1.88, b)
        sh = [c0, c1, (c1[0] + 1, c1[1] + 4), (c0[0] + 1, c0[1] + 4)]
        c.poly(sh, hexc('#4a321c'), alpha=.45, tex=0)
        # plants
        n = 36
        for k in range(n):
            t = (k + rnd.uniform(-.3, .3)) / n
            x = c0[0] + (c1[0] - c0[0]) * t; y = c0[1] + (c1[1] - c0[1]) * t
            h = rnd.uniform(9, 14)
            col = rnd.choice([hexc('#e2bc52'), hexc('#d3a640'), hexc('#efd070'), hexc('#c4a042')])
            c.lines([((x, y), (x + rnd.uniform(-1, 1), y - h))], hexc('#8aa044') if rnd.random() < .25 else col, width=1.6, alpha=.95)
            c.lines([((x + rnd.uniform(-1, 1), y - h), (x + rnd.uniform(-1.5, 1.5), y - h - 3.5))], hexc('#f4dc8a'), width=2.0, alpha=.9)
    # edge darker border / grass fringe
    c.lines([(q[0], q[1]), (q[1], q[2]), (q[2], q[3]), (q[3], q[0])], hexc('#4a321c'), width=2.0, alpha=.5, m=m)
    # clip all to slightly extended footprint (wheat heads poke up, fine)
    return c.to_image(), p.anchor

def pier(seed=0):
    p = Iso(1, 1, 50, mx=16)
    c = p.canvas(301)
    # deck along a-axis, b from .3..-.7 ; z=10
    z = 9
    def deck(a0, a1, b0, b1, zz): return p.Q((a0, b0, zz), (a1, b0, zz), (a1, b1, zz), (a0, b1, zz))
    c.shadow(deck(.02, 1.1, .2, .85, 0), .32, blur=3, color=(10, 40, 50))
    # posts (back first)
    def post(a, b):
        x0, y0 = p.P(a, b, -4); x1, y1 = p.P(a, b, z + 4)
        c.poly([(x0 - 2.5, y0), (x0 + 2.5, y0), (x1 + 2.5, y1), (x1 - 2.5, y1)], hexc('#5a3d24'), shade=(1.1, .75), tex=.15)
    for a in (.15, .55, .95): post(a, .3)
    # side face (b=.7) beneath deck
    side = p.Q((0, .7, z), (1.0, .7, z), (1.0, .7, z - 6), (0, .7, z - 6))
    c.poly(side, hexc('#6b4a2c'), shade=(1, .7), tex=.12)
    dk = deck(0, 1.0, .3, .7, z)
    c.poly(dk, hexc('#c49a62'), shade=(1.05, .95), tex=.12)
    # planks across (constant a lines)
    segs = [(p.P(t, .3, z), p.P(t, .7, z)) for t in np.linspace(.0, 1.0, 11)[1:-1]]
    c.lines(segs, hexc('#7a5530'), width=1.1, alpha=.7)
    c.lines([(p.P(0, .3, z), p.P(1, .3, z))], hexc('#8a6238'), width=1.3, alpha=.8)
    c.lines([(p.P(0, .7, z), p.P(1, .7, z))], hexc('#5a3a1e'), width=1.4, alpha=.9)
    m = c.mask(dk)
    c.strokes(m, [hexc('#e0b87c'), hexc('#8a6238')], 60, 8, ang=(25, 35), width=1.0, alpha=.3, seed=2)
    for a in (.15, .55, .95): post(a, .7)
    # mooring bollards and rope coil
    bx, by = p.P(.88, .62, z)
    c.poly([(bx - 2.5, by), (bx + 2.5, by), (bx + 2, by - 7), (bx - 2, by - 7)], hexc('#4a3220'))
    c.circle(bx, by - 7, 2.7, hexc('#6a4a2c'))
    c.outline(color=(50, 34, 22), alpha=.5, px=.8)
    return c.to_image(), p.anchor

def cart(seed=0):
    p = Iso(1, 1, 60, mx=18)
    c = p.canvas(401)
    cx, cy = p.P(.5, .5, 0)
    c.shadow_ellipse(cx + 8, cy + 2, 28, 8, alpha=.3, blur=2.5)
    # cart along a axis: body quad
    z0, z1 = 8, 18
    a0, a1, b0, b1 = .16, .64, .38, .6
    wallL(c, p, a0, a1, b1, z0, z1, hexc('#9a6a3a'), tex=.15)
    wallR(c, p, a1, b0, b1, z0, z1, hexc('#9a6a3a'), tex=.15, f=KR)
    # hay load
    top = p.Q((a0, b0, z1), (a1, b0, z1), (a1, b1, z1), (a0, b1, z1))
    c.poly(top, hexc('#6a4a2a'))
    hx, hy = p.P((a0 + a1) / 2, (b0 + b1) / 2, z1)
    for dx in (-9, 0, 9): c.sphere(hx + dx, hy - 4, 8, hexc('#e0bd5c'), tex=.3, ry=7)
    # wheel (left visible side at b1)
    wx, wy = p.P(.4, b1 + .02, 0)
    for wxx in (wx - 8, wx + 8):
        c.circle(wxx, wy - 7, 8, hexc('#5a3a1e'))
        c.circle(wxx, wy - 7, 5.5, hexc('#b08850'), tex=.15)
        c.lines([((wxx - 5, wy - 7), (wxx + 5, wy - 7)), ((wxx, wy - 12), (wxx, wy - 2))], hexc('#5a3a1e'), width=1.1)
    # shafts + ox
    sx, sy = p.P(.72, .5, 9)
    c.lines([(p.P(.64, .48, 10), p.P(.86, .44, 9))], hexc('#5a3a1e'), width=1.8)
    ox, oy = p.P(.82, .56, 0)
    c.poly([(ox - 8, oy - 6), (ox + 9, oy - 10), (ox + 10, oy - 18), (ox - 7, oy - 16)], hexc('#8d5e3a'), shade=(1.1, .8), tex=.15)
    for lx in (-6, 6):
        c.poly([(ox + lx - 1.5, oy - 6), (ox + lx + 1.5, oy - 6), (ox + lx + 1.5, oy + 3), (ox + lx - 1.5, oy + 3)], hexc('#4a2e1c'))
    c.circle(ox + 11, oy - 18, 4.5, hexc('#9a6a44'))
    c.lines([((ox + 10, oy - 22), (ox + 8, oy - 27)), ((ox + 14, oy - 21), (ox + 17, oy - 25))], hexc('#e8dcc0'), width=1.5)
    c.outline(color=(48, 32, 22), alpha=.55, px=.8)
    return c.to_image(), p.anchor

def colonist(variant=0, seed=0):
    p = Iso(1, 1, 50, mx=14)
    c = p.canvas(501 + variant)
    cx, cy = p.P(.5, .5, 0)
    c.shadow_ellipse(cx + 5, cy + 1, 9, 3.5, alpha=.32, blur=1.5)
    tun = [hexc('#b84a3a'), hexc('#3f6e9a'), hexc('#c8a040'), hexc('#6a8a4a')][variant % 4]
    # legs
    c.poly([(cx - 4, cy - 12), (cx - .5, cy - 12), (cx - 1, cy), (cx - 4.5, cy)], hexc('#4a3a30'))
    c.poly([(cx + .5, cy - 12), (cx + 4, cy - 12), (cx + 4.5, cy), (cx + 1, cy)], hexc('#3a2c24'))
    # body
    c.poly([(cx - 5.5, cy - 27), (cx + 5.5, cy - 27), (cx + 6.5, cy - 11), (cx - 6.5, cy - 11)], tun, shade=(1.15, .8), tex=.1)
    c.lines([((cx - 6, cy - 14), (cx + 6, cy - 14))], hexc('#3a2a1c'), width=1.5)
    # arms
    c.poly([(cx - 8, cy - 26), (cx - 5, cy - 26), (cx - 6, cy - 14), (cx - 9, cy - 14)], mul(tun, .9))
    c.poly([(cx + 5, cy - 26), (cx + 8, cy - 26), (cx + 9, cy - 14), (cx + 6, cy - 14)], mul(tun, .65))
    c.circle(cx, cy - 31, 4.6, hexc('#e8b890'), tex=.05)
    # hat
    c.poly([(cx - 7, cy - 33), (cx + 7, cy - 33), (cx + 3, cy - 40), (cx - 3, cy - 40)], hexc('#5a4030') if variant % 2 == 0 else hexc('#c8b070'), shade=(1.2, .85))
    c.outline(color=(40, 28, 22), alpha=.6, px=.7)
    return c.to_image(), p.anchor

def ship(seed=0):
    p = Iso(2, 2, 230, mx=30)
    c = p.canvas(601)
    # water disturbance beneath hull: dark shadow & foam
    hull = lambda t: (.12 + 1.76 * t)
    def w(t):
        if t < .38: return .36 * math.sqrt(max(0, 1 - ((.38 - t) / .52) ** 2))
        return .36 * math.sqrt(max(0, 1 - ((t - .38) / .62) ** 2)) ** 1.15
    def zdeck(t): return 20 + 16 * t ** 2.2 + (9 * (1 - t / .3) if t < .3 else 0)
    ts = np.linspace(0, 1, 26)
    B0 = 1.0
    # shadow on water
    shp = [p.P(hull(t) + .1, B0 + w(t) + .12, 0) for t in ts] + [p.P(hull(t) + .1, B0 - w(t) + .12, 0) for t in ts[::-1]]
    c.shadow(shp, .3, blur=5, color=(8, 40, 56))
    # hull sides
    top_l = [p.P(hull(t), B0 + w(t), zdeck(t) + 6) for t in ts]
    bot_l = [p.P(hull(t), B0 + .72 * w(t), 3) for t in ts[::-1]]
    top_r = [p.P(hull(t), B0 - w(t), zdeck(t) + 6) for t in ts]
    bot_r = [p.P(hull(t), B0 - .72 * w(t), 3) for t in ts[::-1]]
    c.poly(top_r + bot_r, hexc('#4a2e18'), shade=(1, .8), tex=.12)
    side = c.poly(top_l + bot_l, warm(hexc('#8a5a30'), 1.0), shade=(1.12, .72), tex=.16)
    # hull bands: gold sheer strip + darker lower + planks
    for f, col, wd, al in [(.78, hexc('#e0b858'), 2.6, .95), (.35, hexc('#3c2410'), 1.0, .5), (.55, hexc('#3c2410'), 1.0, .45), (.18, hexc('#3c2410'), 1.0, .4)]:
        segs = []
        for i in range(len(ts) - 1):
            def pt(t): return p.P(hull(t), B0 + w(t) * (1 - .28 * (1 - f)), 3 + (zdeck(t) + 3) * f)
            segs.append((pt(ts[i]), pt(ts[i + 1])))
        c.lines(segs, col, width=wd, alpha=al, m=side)
    # stern: transom/cabin block
    # deck
    deck = [p.P(hull(t), B0 - w(t), zdeck(t) + 6) for t in ts] + [p.P(hull(t), B0 + w(t), zdeck(t) + 6) for t in ts[::-1]]
    dm = c.poly(deck, hexc('#c89a5c'), shade=(1.05, .9), tex=.14)
    c.lines([(p.P(hull(t), B0 + k * w(t) * .85, zdeck(t) + 6), p.P(hull(ts[i + 1]), B0 + k * w(ts[i + 1]) * .85, zdeck(ts[i + 1]) + 6))
             for i, t in enumerate(ts[:-1]) for k in (-.5, 0, .5)], hexc('#8a5f34'), width=1.0, alpha=.5, m=dm)
    # inner bulwark rail on right (far) side
    rail_r = [p.P(hull(t), B0 - w(t), zdeck(t) + 6) for t in ts] + [p.P(hull(t), B0 - w(t), zdeck(t) + 13) for t in ts[::-1]]
    c.poly(rail_r, hexc('#b5834a'), shade=(1, .85), tex=.1)
    # near rail (outer face)
    rail_l = [p.P(hull(t), B0 + w(t), zdeck(t) + 6) for t in ts] + [p.P(hull(t), B0 + w(t), zdeck(t) + 12) for t in ts[::-1]]
    c.poly(rail_l, hexc('#a0703c'), shade=(1.1, .85), tex=.1)
    c.lines([(p.P(hull(ts[i]), B0 + w(ts[i]), zdeck(ts[i]) + 12), p.P(hull(ts[i + 1]), B0 + w(ts[i + 1]), zdeck(ts[i + 1]) + 12)) for i in range(len(ts) - 1)],
            hexc('#e0b858'), width=1.4, alpha=.9)
    # stern castle (cabin)
    ca0, ca1 = .24, .62
    cz0 = zdeck(.15) + 6
    cb0, cb1 = B0 - .24, B0 + .24
    wallL(c, p, ca0, ca1, cb1, cz0, cz0 + 20, hexc('#c9a066'), tex=.14)
    wallR(c, p, ca1, cb0, cb1, cz0, cz0 + 20, hexc('#c9a066'), tex=.14, f=KR)
    c.poly(p.Q((ca0 - .03, cb0 - .03, cz0 + 20), (ca1 + .03, cb0 - .03, cz0 + 20), (ca1 + .03, cb1 + .03, cz0 + 20), (ca0 - .03, cb1 + .03, cz0 + 20)), hexc('#d8b078'), tex=.12)
    for ta in (.32, .44, .54):
        window(c, p, 'L', ta - .035, ta + .035, cz0 + 7, cz0 + 16, cb1)
    # masts
    mast_ts = [.22, .52, .8]
    mast_h = [150, 178, 140]
    for mt, mh in zip(mast_ts, mast_h):
        x0, y0 = p.P(hull(mt), B0, zdeck(mt) + 6)
        c.poly([(x0 - 2.5, y0), (x0 + 2.5, y0), (x0 + 1.5, y0 - mh), (x0 - 1.5, y0 - mh)], hexc('#6a4528'), shade=(1.1, .75), tex=.1)
    # sails (draw rear to front by a -> back mast first)
    for idx, (mt, mh) in enumerate(zip(mast_ts, mast_h)):
        a = hull(mt) + .02
        zb = zdeck(mt) + 6
        sw = [.40, .46, .38][idx]
        levels = [(zb + 22, zb + mh * .55), (zb + mh * .55 + 3, zb + mh * .88)] if idx != 0 else [(zb + 24, zb + mh * .62), (zb + mh * .62 + 3, zb + mh * .88)]
        for li, (zlo, zhi) in enumerate(levels):
            wdt = sw * (1 - .25 * li)
            n = 12
            top = [p.P(a + .0, B0 + wdt * (1 - 2 * s / n), zhi) for s in range(n + 1)]
            bot = [p.P(a + .09 * math.sin(math.pi * s / n) + .02, B0 + (wdt * .94) * (1 - 2 * s / n), zlo + 3 * math.sin(math.pi * s / n)) for s in range(n + 1)]
            # billow: middle bulges toward +a (screen right-down) and down
            quad = top + bot[::-1]
            m = c.poly(quad, hexc('#f0e6c8'), shade=(1.1, .88), tex=.1, alpha=1)
            # shading: left part lit, right part shaded
            sh = [p.P(a + .09 * math.sin(math.pi * s / n), B0 + wdt * (1 - 2 * s / n), 0) for s in range(n + 1)]
            c.lines([(top[s], bot[s]) for s in range(2, n - 1, 3)], hexc('#b8a67e'), width=1.0, alpha=.5, m=m)
            c.lines([(lerp(top[s], bot[s], .45), lerp(top[s + 1], bot[s + 1], .45)) for s in range(n)], hexc('#b8a67e'), width=1.0, alpha=.4, m=m)
            # right-side shadow gradient
            rq = top[n // 2:] + bot[n // 2:][::-1]
            c.poly(rq, hexc('#8a7a8a'), alpha=.28, tex=0)
            # red stripe on main courses
            if li == 0:
                s1 = [lerp(top[s], bot[s], .38) for s in range(n + 1)]; s2 = [lerp(top[s], bot[s], .5) for s in range(n + 1)]
                c.poly(s1 + s2[::-1], hexc('#b8483a'), alpha=.85, tex=.08)
            # yard
            c.lines([(top[0], top[-1])], hexc('#5a3a1e'), width=2.0)
    # bowsprit + jib
    bx, by = p.P(hull(1), B0, zdeck(1) + 6)
    tx, ty = p.P(hull(1) + .4, B0, zdeck(1) + 18)
    c.lines([((bx, by), (tx, ty))], hexc('#5a3a1e'), width=2.4)
    mxp, myp = p.P(hull(.8), B0, zdeck(.8) + 6 + 135)
    c.poly([(mxp + 1, myp + 6), (tx - 2, ty - 1), (mxp + 4, p.P(hull(.8), B0, zdeck(.8) + 40)[1])], hexc('#ece0c0'), shade=(1.1, .85), alpha=.97)
    c.lines([((mxp + 1, myp + 6), (tx, ty))], hexc('#3c2a1a'), width=1.0, alpha=.7)
    # rigging
    rig = []
    for mt, mh in zip(mast_ts, mast_h):
        top = p.P(hull(mt), B0, zdeck(mt) + 6 + mh * .9)
        for k in (-.3, .3):
            rig.append((top, p.P(hull(mt), B0 + k, zdeck(mt) + 12)))
    c.lines(rig, hexc('#3c2a1a'), width=.8, alpha=.55)
    # flag
    fx, fy = p.P(hull(.52), B0, zdeck(.52) + 6 + 178)
    c.lines([((fx, fy), (fx, fy - 9))], hexc('#5a3a1e'), width=1.4)
    c.poly([(fx, fy - 9), (fx + 15, fy - 6), (fx + 12, fy - 3), (fx + 16, fy), (fx, fy - 2)], hexc('#c2453a'), tex=.08)
    # foam / wake at waterline
    foam = [p.P(hull(t), B0 + w(t) * .78 + .035, 1) for t in ts]
    c.lines([(foam[i], foam[i + 1]) for i in range(len(foam) - 1)], hexc('#f4fbf6'), width=2.2, alpha=.85)
    foam2 = [p.P(hull(t), B0 + w(t) * 1.08 + .08 + .02 * math.sin(t * 22), 0) for t in ts]
    c.lines([(foam2[i], foam2[i + 1]) for i in range(len(foam2) - 1) if i % 3 != 2], hexc('#d5f0ee'), width=1.4, alpha=.55)
    c.outline(color=(36, 24, 16), alpha=.55, px=.8)
    return c.to_image(), p.anchor
