import math, random
from gfx import *

# ---------- iso building helpers (u->SE, v->SW; light from upper-left) ----------
def wallL(c, u0, u1, v1, z0, z1, ramp_, tone):
    """left-facing wall at v=v1. tone(a,z) -> level|colour  (a = u)"""
    pts = [c.P(u0, v1, z0), c.P(u1, v1, z0), c.P(u1, v1, z1), c.P(u0, v1, z1)]
    if not callable(tone): tone = (lambda k: (lambda a, z: k))(tone)
    c.fill(pts, ramp_, lambda x, y: tone(x + v1, (x + v1 + v1) / 2 - (c.U + c.V) / 2 - y))
def wallR(c, u1, v0, v1, z0, z1, ramp_, tone):
    """right-facing wall at u=u1. (a = v)"""
    pts = [c.P(u1, v0, z0), c.P(u1, v1, z0), c.P(u1, v1, z1), c.P(u1, v0, z1)]
    if not callable(tone): tone = (lambda k: (lambda a, z: k))(tone)
    c.fill(pts, ramp_, lambda x, y: tone(u1 - x, (u1 + (u1 - x)) / 2 - (c.U + c.V) / 2 - y))
def rectL(c, a0, a1, z0, z1, v1, col):
    c.fill([c.P(a0, v1, z0), c.P(a1, v1, z0), c.P(a1, v1, z1), c.P(a0, v1, z1)], col=col)
def rectR(c, a0, a1, z0, z1, u1, col):
    c.fill([c.P(u1, a0, z0), c.P(u1, a1, z0), c.P(u1, a1, z1), c.P(u1, a0, z1)], col=col)
def top(c, u0, u1, v0, v1, z, ramp_, tone):
    c.poly3([(u0, v0, z), (u1, v0, z), (u1, v1, z), (u0, v1, z)], ramp_, tone)

def plaster(base=2.0, frame=True, brick=False, ramp_=PLAST, fcol=WOOD[1], dark=-1.1, step=6):
    def mk(side):
        d = dark if side == 'R' else 0
        def f(a, z):
            if brick:
                row = int(z // 2); off = (row % 2) * 2
                if int(z) % 2 == 0: return base - 0.7 + d
                if int(a + off) % 4 == 0: return base - .7 + d
                return base + 0.3 + d + (0.5 if (int(a) * 7 + row * 3) % 5 == 0 else 0)
            if frame and (int(a) % step == 0 or int(z) in (0,) ): return fcol
            return base + d + (0.4 if (int(a) + int(z) * 3) % 7 == 0 else 0)
        return f
    return mk

def gable(c, u0, u1, v0, v1, z1, rh, ramp_, ov=2, lo=1.0, ridge_col=None, step=3, wallramp=None, wall=None):
    """gable roof ridge along u. draws back plane, gable wall (u1), front plane."""
    vm = (v0 + v1) / 2; zr = z1 + rh
    uu0, uu1 = u0 - ov, u1 + ov; vv0, vv1 = v0 - ov, v1 + ov
    def tl(shade):
        def f(x, y):
            if y % 3 == 0: return lo - .6 + shade
            return lo + shade + (.7 if (x + y // 3) % 3 == 0 else 0)
        return f
    c.poly3([(uu0, vv0, z1 - 1), (uu1, vv0, z1 - 1), (uu1, vm, zr), (uu0, vm, zr)], ramp_, tl(-0.2))
    if wall:
        c.poly3([(u1, v0, z1), (u1, v1, z1), (u1, vm, zr)], wallramp, lambda x, y: wall(x, y))
    c.poly3([(uu0, vv1, z1 - 1), (uu1, vv1, z1 - 1), (uu1, vm, zr), (uu0, vm, zr)], ramp_, tl(1.2))
    c.line3((uu0, vm, zr), (uu1, vm, zr), ramp_[min(4, len(ramp_)-1)])
    # dark eaves
    c.line3((uu0, vv1, z1 - 1), (uu1, vv1, z1 - 1), ramp_[0]); c.line3((uu1, vv1, z1 - 1), (uu1, vm, zr), ramp_[0])
    c.line3((uu1, vv0, z1 - 1), (uu1, vm, zr), ramp_[0])

def hip(c, u0, u1, v0, v1, z1, rh, ramp_, ov=2, lo=1.0):
    um, vm = (u0 + u1) / 2, (v0 + v1) / 2; zr = z1 + rh
    def tl(shade):
        def f(x, y):
            if y % 3 == 0: return lo - .6 + shade
            return lo + shade + (.7 if (x + y // 3) % 3 == 0 else 0)
        return f
    c.poly3([(u0-ov, v1+ov, z1-1), (u1+ov, v1+ov, z1-1), (um, vm, zr)], ramp_, tl(1.2))
    c.poly3([(u1+ov, v0-ov, z1-1), (u1+ov, v1+ov, z1-1), (um, vm, zr)], ramp_, tl(-.2))
    c.line3((u0-ov, v1+ov, z1-1), (u1+ov, v1+ov, z1-1), ramp_[0]); c.line3((u1+ov, v1+ov, z1-1), (u1+ov, v0-ov, z1-1), ramp_[0])

def roofz(v, v0, v1, z1, rh, ov=2):
    vm = (v0 + v1) / 2; a = v0 - ov
    return z1 - 1 + (rh + 1) * min(1, (v - a) / (vm - a))
def chimney(c, u, v, z0, h, col=STONE):
    wallL(c, u, u + 3, v + 3, z0, z0 + h, col, lambda a, z: 3.0 + (0.6 if int(z) % 3 == 0 else 0))
    wallR(c, u + 3, v, v + 3, z0, z0 + h, col, lambda a, z: 1.8 + (0.6 if int(z) % 3 == 0 else 0))
    top(c, u, u + 3, v, v + 3, z0 + h, col, 4.2)
    c.line3((u, v, z0 + h), (u + 3, v, z0 + h), col[1])

def door_win(c, face, a, z0, z1, w, col=WOOD[0]):
    pass

def shadow(c, cx, cy, rx, ry, col=GRASS[0]):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if ((x - cx) / (rx*.8)) ** 2 + ((y - cy) / (ry*.8)) ** 2 <= 1 and (x + y) % 2 == 0 and y % 2 == 0: c.put(x, y, col)

# ---------- sprites ----------
def tree(k):
    c = new(1, 1, up=34, down=4)
    rng = random.Random(100 + k)
    cx, cy = 0, -8
    shadow(c, cx + 2, cy + 1, 8, 3)
    # trunk
    c.rect(cx - 1, cy - 7, cx, cy + 1, WOOD[2]); c.rect(cx + 1, cy - 7, cx + 1, cy + 1, WOOD[1]); c.put(cx - 2, cy + 1, WOOD[2]); c.put(cx + 2, cy + 1, WOOD[1])
    if k == 1:   # conifer: stacked tiers
        for i, (w, y0, h) in enumerate([(9, -6, 8), (7, -13, 8), (5, -20, 7), (3, -26, 6)]):
            pts = [(cx - w, cy + y0 + h), (cx + w, cy + y0 + h), (cx, cy + y0 - 1)]
            c.fill(pts, FOL, lambda x, y, cx=cx, y0=cy + y0, h=h: 1.0 + 2.8 * max(0, min(1, (cx - x + (y - y0) * .6) / 9 + .35)) + (0.6 if (x + y) % 3 == 0 else 0))
            c.line((cx - w, cy + y0 + h), (cx + w, cy + y0 + h), FOL[0])
    else:
        blobs = [(-6, -15, 7, 6), (5, -14, 7, 6), (0, -21, 8, 7), (-2, -27, 6, 5)] if k == 0 else [(-5, -13, 6, 5), (5, -13, 6, 5), (0, -19, 7, 6), (1, -24, 5, 4), (-4, -21, 5, 5)]
        for (bx, by, rx, ry) in blobs:
            c.disc(cx + bx, cy + by, rx, ry, FOL, lambda x, y, bx=bx, by=by, rx=rx, ry=ry: (1.1 if k == 0 else .5) + 2.9 * max(0, min(1, .5 + (-(x - cx - bx) / rx * .6 - (y - cy - by) / ry * .75) * .5)) + (0.5 if (x * 3 + y * 5) % 7 == 0 else 0))
            c.disc(cx + bx, cy + by, rx, ry, col=None, ramp_=FOL, tone=0) if False else None
    c.outline(); return c.crop()

def rock(k=0):
    c = new(1, 1, up=14, down=3); cx, cy = 0, -8
    shadow(c, cx + 2, cy + 3, 8, 3, EARTH[0])
    pts = [(cx - 8, cy + 3), (cx - 7, cy - 2), (cx - 3, cy - 7), (cx + 3, cy - 6), (cx + 8, cy - 1), (cx + 8, cy + 3), (cx + 2, cy + 5)]
    c.fill(pts, STONE, lambda x, y: 1.5 + 3.2 * max(0, min(1, .45 - (x - cx) / 18 - (y - cy + 2) / 12)) + (.7 if (x + y * 2) % 5 == 0 else 0))
    c.line((cx - 3, cy - 6), (cx - 1, cy), STONE[1]); c.line((cx - 1, cy), (cx + 3, cy + 3), STONE[1]); c.line((cx + 3, cy - 5), (cx + 6, cy - 1), STONE[2])
    c.outline(); return c.crop()

def house(k):
    c = new(1, 1, up=40, down=4)
    u0, u1, v0, v1 = 3, 12, 3, 12
    z1 = 10 if k != 2 else 13
    if k == 0:  # timber frame, red tile roof
        wl = plaster(2.2, True); wr = plaster(2.2, True, dark=-1.2)
    elif k == 1:  # plaster + thatch
        wl = plaster(3.0, False); wr = plaster(3.0, False, dark=-1.3)
    else:       # brick, slate/ red hip
        wl = plaster(2.0, brick=True, ramp_=BRICK); wr = plaster(2.0, brick=True, dark=-.9)
    ramp_w = [PLAST, PLAST, BRICK][k]
    shadow(c, 4, -3, 12, 4)
    wallL(c, u0, u1, v1, 0, z1, ramp_w, wl('L')); wallR(c, u1, v0, v1, 0, z1, ramp_w, wr('R'))
    # door + windows
    rectL(c, 5, 8, 0, 6, v1, WOOD[1]); rectL(c, 5, 8, 6, 7, v1, WOOD[0]); c.put(*c.P(7.5, v1, 3), GOLD[2])
    rectL(c, 9.5, 11.5, 4, 7, v1, SLATE[0]); rectL(c, 9.5, 11.5, 7, 8, v1, WOOD[2])
    rectR(c, 5, 7.5, 4, 7, u1, SLATE[0]); rectR(c, 5, 7.5, 7, 8, u1, WOOD[2]); rectR(c, 4.5, 5, 4, 7, u1, WOOD[3]); rectR(c, 7.5, 8, 4, 7, u1, WOOD[3])
    if k == 0:
        gable(c, u0, u1, v0, v1, z1, 7, ROOF, ov=2, lo=2.0, wallramp=PLAST, wall=lambda x, y: 1.6 + (0.4 if (x + y) % 4 == 0 else 0))
        chimney(c, 4, 4, roofz(5, v0, v1, z1, 7) - 1, 7)
    elif k == 1:
        gable(c, u0, u1, v0, v1, z1, 8, THATCH, ov=2, lo=2.2, wallramp=PLAST, wall=lambda x, y: 1.5)
        chimney(c, 4, 4, roofz(5, v0, v1, z1, 8) - 1, 7)
    else:
        hip(c, u0, u1, v0, v1, z1, 9, SLATE, ov=2, lo=1.3) if False else hip(c, u0, u1, v0, v1, z1, 9, ROOF, ov=2, lo=1.6)
    c.outline(); return c.crop()

def farmhouse():
    c = new(1, 1, up=40, down=4)
    u0, u1, v0, v1 = 1, 14, 4, 11; z1 = 8
    shadow(c, 4, -2, 12, 4)
    wallL(c, u0, u1, v1, 0, z1, PLAST, plaster(2.6, True, step=7)('L')); wallR(c, u1, v0, v1, 0, z1, PLAST, plaster(2.6, True, dark=-1.2, step=7)('R'))
    rectL(c, 3, 5.5, 0, 5.5, v1, WOOD[1]); rectL(c, 7.5, 9.5, 3.5, 6, v1, SLATE[0]); rectL(c, 11, 13, 3.5, 6, v1, SLATE[0])
    rectR(c, 6, 9, 0, 5, u1, WOOD[1])
    gable(c, u0, u1, v0, v1, z1, 8, THATCH, ov=2, lo=2.4, wallramp=PLAST, wall=lambda x, y: 1.5)
    chimney(c, 10, 5, roofz(6, v0, v1, z1, 8) - 1, 6)
    # hay stack
    c.disc(10, -4, 3, 4, THATCH, lambda x, y: 2 + max(0, (x - 8) * -.2) ); c.disc(11, -5, 3, 4, THATCH, 2.5)
    c.outline(); return c.crop()

def windmill():
    c = new(1, 1, up=70, down=3); cx, cy = 0, -8
    shadow(c, 4, 0, 9, 3, EARTH[1])
    zt = 30; hw0, hw1 = 8, 5
    def body(sgn):
        pts = [(cx, cy + 4), (cx + sgn * hw0, cy + 1)] if False else None
    # tower: left half lit, right half dark (octagon-ish)
    L = [(cx - hw0, cy + 0), (cx, cy + 4), (cx, cy + 4 - zt), (cx - hw1, cy + 2 - zt)]
    R = [(cx, cy + 4), (cx + hw0, cy), (cx + hw1, cy + 2 - zt), (cx, cy + 4 - zt)]
    c.fill(L, PLAST, lambda x, y: 3.0 - (x - cx + 8) * 0.05 + (-0.9 if (y + 100) % 4 == 0 else 0) + (0.5 if ((x + y // 4)) % 5 == 0 else 0))
    c.fill(R, PLAST, lambda x, y: 1.4 + (-0.8 if (y + 100) % 4 == 0 else 0) + (0.4 if ((x + y // 4)) % 5 == 0 else 0))
    c.line((cx - hw0, cy), (cx, cy + 4), STONE[2]); c.line((cx, cy + 4), (cx + hw0, cy), STONE[1])
    # stone plinth band
    c.fill([(cx - hw0, cy), (cx, cy + 4), (cx, cy + 4 - 5), (cx - hw0 + 1, cy - 4)], STONE, lambda x, y: 2.6 + (.8 if (x + y) % 4 == 0 else 0))
    c.fill([(cx, cy + 4), (cx + hw0, cy), (cx + hw0 - 1, cy - 4), (cx, cy - 1)], STONE, lambda x, y: 1.2 + (.8 if (x + y) % 4 == 0 else 0))
    # door + window
    c.fill([(cx - 5, cy + 2), (cx - 2, cy + 3), (cx - 2, cy - 3), (cx - 5, cy - 4)], col=WOOD[1])
    c.fill([(cx + 2, cy - 12), (cx + 4, cy - 12), (cx + 4, cy - 15), (cx + 2, cy - 15)], col=SLATE[0])
    # cap
    ct = cy - zt + 3
    c.fill([(cx - hw1 - 1, ct), (cx, ct + 3), (cx + hw1 + 1, ct), (cx + 2, ct - 7), (cx - 3, ct - 7)], WOOD, lambda x, y: 1.0 + (x - cx + 6) * .22)
    c.fill([(cx - 3, ct - 6), (cx + 2, ct - 6), (cx + 1, ct - 9), (cx - 2, ct - 9)], WOOD, 2.5)
    # hub + sails (plane faces SE: arm (v,z) -> screen (-v, v/2 - z))
    hx, hy = cx + 4, ct - 3
    for ang in (30, 120, 210, 300):
        a = math.radians(ang); dx, dy = math.cos(a), -math.sin(a)
        dx, dy = dx * 1.0, dy * 1.0
        ex, ey = hx + dx * 20, hy + dy * 20 - dx * 0
        nx, ny = -dy, dx
        c.line((hx, hy), (ex, ey), WOOD[0])
        for t in range(5, 20):
            if t % 2 == 1 or True:
                pass
        p0 = (hx + dx * 5 + nx * 1, hy + dy * 5 + ny * 1); p1 = (hx + dx * 19 + nx * 1, hy + dy * 19 + ny * 1)
        p2 = (hx + dx * 19 + nx * 5, hy + dy * 19 + ny * 5); p3 = (hx + dx * 5 + nx * 5, hy + dy * 5 + ny * 5)
        c.fill([p0, p1, p2, p3], PLAST, lambda x, y: 2.6 + (.8 if (x + y) % 2 == 0 else -.6))
        c.line(p0, p1, WOOD[1]); c.line(p0, p3, WOOD[1]) if False else None
        c.line(p3, p2, WOOD[2])
        c.line((hx, hy), (ex, ey), WOOD[1])
    c.disc(hx, hy, 2, 2, WOOD, 3)
    c.outline(); return c.crop()

def lumberjack():
    c = new(1, 1, up=32, down=4)
    u0, u1, v0, v1 = 1, 9, 2, 12; z1 = 7
    shadow(c, 2, -3, 12, 4, EARTH[0])
    wl = lambda a, z: 2.0 + (-1.0 if int(a) % 2 == 0 else 0) + (.5 if int(z) % 3 == 0 else 0)
    wr = lambda a, z: 1.0 + (-.8 if int(a) % 2 == 0 else 0)
    wallL(c, u0, u1, v1, 0, z1, WOOD, wl); wallR(c, u1, v0, v1, 0, z1, WOOD, wr)
    rectL(c, 3, 5.5, 0, 5, v1, WOOD[0]); rectL(c, 6.5, 8, 3.5, 5.5, v1, SLATE[0]); rectR(c, 5, 8, 3, 5.5, u1, SLATE[0])
    gable(c, u0, u1, v0, v1, z1, 6, WOOD, ov=2, lo=3.0, wallramp=WOOD, wall=lambda x, y: 1.0)
    # log pile (right front) u 10..15, v 3..14 -> end grain on left face
    pu0, pu1, pv0, pv1, ph = 10, 15, 6, 14, 5
    wallL(c, pu0, pu1, pv1, 0, ph, WOOD, lambda a, z: (WOOD[4] if ((int(a) + int(z) * 1) % 2 == 0 and int(z) % 2 == 0) else (WOOD[2] if int(z) % 2 == 0 else WOOD[1])) if False else (WOOD[4] if int(a) % 2 == 1 and int(z) % 2 == 0 else (WOOD[2] if int(z)%2==0 else WOOD[1])))
    wallR(c, pu1, pv0, pv1, 0, ph, WOOD, lambda a, z: 1.0 + (.8 if int(z) % 2 == 0 else -.2))
    top(c, pu0, pu1, pv0, pv1, ph, WOOD, lambda x, y: 2.5 + (.8 if x % 2 == 0 else 0))
    # axe stump
    c.disc(-3, -2, 3, 2, WOOD, 3.2); c.rect(-6, -2, 0, 1, WOOD[2]); c.line((-2, -6), (-2, -2), WOOD[1]); c.line((-3, -7), (-1, -7), STONE[4])
    c.outline(); return c.crop()

def chapel():
    c = new(2, 2, up=66, down=4)
    n0, n1, nv0, nv1, z1 = 3, 24, 11, 21, 15
    shadow(c, 6, -4, 24, 7, GRASS[0])
    stone = lambda base, d: (lambda a, z: (STONE[1] if int(z) % 4 == 0 else (STONE[1] if (int(a) + (int(z) // 4) * 2) % 5 == 0 else base + d)))
    wallL(c, n0, n1, nv1, 0, z1, STONE, lambda a, z: (1.2 if int(z) % 4 == 0 or (int(a) + (int(z) // 4) * 3) % 6 == 0 else 3.2 + (.4 if int(a) % 3 == 0 else 0)))
    wallR(c, n1, nv0, nv1, 0, z1, STONE, lambda a, z: 1.3)
    for a in (6, 11, 16, 21):   # pointed windows
        rectL(c, a, a + 2, 5, 11, nv1, SLATE[1]); rectL(c, a + .5, a + 1.5, 11, 12.5, nv1, SLATE[1])
        c.line3((a + 1, nv1, 5), (a + 1, nv1, 12), SLATE[3])
    gable(c, n0, n1, nv0, nv1, z1, 7, ROOF, ov=2, lo=1.8, wallramp=STONE, wall=lambda x, y: 1.5)
    # tower at front (u 22..30)
    tu0, tu1, tv0, tv1, tz = 21, 29, 11, 21, 30
    wallL(c, tu0, tu1, tv1, 0, tz, STONE, lambda a, z: (1.2 if int(z) % 4 == 0 or (int(a) + (int(z) // 4) * 3) % 6 == 0 else 3.4))
    wallR(c, tu1, tv0, tv1, 0, tz, STONE, lambda a, z: (0.6 if int(z) % 4 == 0 or (int(a) + (int(z) // 4) * 3) % 6 == 0 else 1.5))
    rectR(c, 14, 18, 0, 8, tu1, WOOD[1]); rectR(c, 15, 17, 8, 10, tu1, WOOD[1]); rectR(c, 14, 18, 8, 8.5, tu1, STONE[0])
    rectR(c, 14.5, 17.5, 21, 27, tu1, INK); rectL(c, 24, 26, 21, 27, tv1, INK)
    hip(c, tu0, tu1, tv0, tv1, tz, 15, WOOD, ov=1, lo=1.6)
    # cross
    zt = tz + 15; p = c.P(25, 16, zt)
    c.line((p[0], p[1]), (p[0], p[1] - 6), GOLD[2]); c.line((p[0] - 2, p[1] - 4), (p[0] + 2, p[1] - 4), GOLD[2])
    c.outline(); return c.crop()

def warehouse():
    c = new(2, 2, up=50, down=4)
    u0, u1, v0, v1, z1 = 3, 28, 9, 24, 12
    shadow(c, 6, -4, 26, 8, GRASS[0])
    def wl(a, z):
        if z < 4: return STONE[2] if int(z) != 3 and (int(a) + int(z // 2) * 2) % 5 != 0 else STONE[1]
        if int(a) % 5 == 0: return WOOD[1]
        return 2.6 + (.5 if (int(a) + int(z)) % 6 == 0 else 0)
    def wr(a, z):
        if z < 4: return STONE[1] if (int(a) + int(z // 2) * 2) % 5 != 0 else STONE[0]
        if int(a) % 5 == 0: return WOOD[0]
        return 1.2
    wallL(c, u0, u1, v1, 0, z1, PLAST, wl); wallR(c, u1, v0, v1, 0, z1, PLAST, wr)
    # big arched doors on end (right) wall and small on left
    rectR(c, 13, 20, 0, 8, u1, WOOD[0]); rectR(c, 14, 19, 8, 9, u1, WOOD[0])
    for a in (14, 16.5, 19):
        c.line3((u1, a, 0), (u1, a, 8), WOOD[1])
    rectL(c, 8, 12, 4.5, 9, v1, WOOD[0]); rectL(c, 17, 21, 4.5, 9, v1, WOOD[0]); rectL(c, 8, 12, 4.5, 4.9, v1, STONE[4]); rectL(c, 17, 21, 4.5, 4.9, v1, STONE[4])
    c.line3((10, v1, 4.5), (10, v1, 9), WOOD[2]); c.line3((19, v1, 4.5), (19, v1, 9), WOOD[2])
    gable(c, u0, u1, v0, v1, z1, 9, ROOF, ov=2, lo=1.8, wallramp=PLAST, wall=lambda x, y: 1.4)
    # hoist beam
    c.line3((u1 + 2, 17, 11), (u1 + 6, 17, 11), WOOD[2]); c.line3((u1 + 6, 17, 11), (u1 + 6, 17, 7), WOOD[1])
    # barrels and crates in front-left
    for (bu, bv) in [(8, 27), (11, 28)]:
        cx, cy = c.P(bu, bv, 0)
        c.rect(int(cx) - 2, int(cy) - 5, int(cx) + 2, int(cy), WOOD[3]); c.disc(cx, cy - 5, 2.5, 1.2, WOOD, 4.0)
        c.line((cx - 2, cy - 3), (cx + 2, cy - 3), STONE[1]); c.line((cx - 2, cy - 1), (cx + 2, cy - 1), STONE[1])
    for (bu, bv) in [(15, 27), (19, 28)]:
        cx, cy = c.P(bu, bv, 0)
        c.rect(int(cx) - 3, int(cy) - 5, int(cx) + 3, int(cy), WOOD[3]); c.rect(int(cx) - 3, int(cy) - 5, int(cx) + 3, int(cy) - 4, WOOD[4])
        c.line((cx, cy - 5), (cx, cy), WOOD[1]); c.line((cx - 3, cy - 2), (cx + 3, cy - 2), WOOD[2])
    c.outline(); return c.crop()

def pier():
    c = new(1, 1, up=10, down=10, side=4)
    zt = 3
    pu0, pu1, pv0, pv1 = 0, 16, 3, 13
    for (pu, pv) in [(1, 3), (1, 13), (8, 3), (8, 13), (15, 3), (15, 13)]:
        for z in range(-6, zt): 
            c.put(*[int(round(q)) for q in c.P(pu, pv, z)], WOOD[0] if pu >= 8 else WOOD[1])
        x, y = c.P(pu, pv, zt); c.put(int(x), int(y), WOOD[3])
    wallL(c, pu0, pu1, pv1, zt - 1, zt, WOOD, 1.0)
    wallR(c, pu1, pv0, pv1, zt - 1, zt, WOOD, 0.6)
    top(c, pu0, pu1, pv0, pv1, zt, WOOD, lambda x, y: 3.6 + (0.4 if x % 2 == 0 else -.8))
    for a in range(1, 16, 2): c.line3((a, pv0, zt), (a, pv1, zt), WOOD[2])
    c.line3((pu0, pv0, zt), (pu1, pv0, zt), WOOD[0]); c.line3((pu0, pv1, zt), (pu1, pv1, zt), WOOD[2])
    c.outline(); return c.crop()

def ship():
    c = new(2, 2, up=70, down=8, side=10)
    # water ripples
    def rip(u, v, z=0, col=OCEAN[6]): c.put(*[int(round(q)) for q in c.P(u, v, z)], col)
    hull_u0, hull_u1 = 2, 30
    def half(t):  # half-width at station t in [0,1], stern=0 bow=1
        return 6.5 * min(1, (t / .12) ** .6) * (1 - t ** 3.2) if t > 0 else 0
    def zt(t): return 9 + 5 * max(0, t - .72) * 3.2 + (4 if t < .26 else 0)
    stations = [hull_u0 + (hull_u1 - hull_u0) * i / 56 for i in range(57)]
    vc = 16
    wake = [(u, v) for u in range(0, 34, 3) for v in (6, 27)]
    # deck + far bulwark
    pts_top_far = []; pts_top_near = []; pts_bot = []
    for u in stations:
        t = (u - hull_u0) / (hull_u1 - hull_u0)
        w = half(t); z = zt(t)
        pts_top_far.append(c.P(u, vc - w, z)); pts_top_near.append(c.P(u, vc + w, z)); pts_bot.append(c.P(u, vc + w * .55, 1 + 2.5 * (1 - t) ** 2))
    c.fill(pts_top_far + pts_top_near[::-1], WOOD, lambda x, y: 3.0 + (0.7 if (x + y) % 3 == 0 else 0))
    # near hull side: top edge .. bottom edge
    side = pts_top_near + pts_bot[::-1]
    def htone(x, y):
        # planking by y rows + wale band
        return (x, y)
    cols_top = {}
    # compute local top edge y for each x to place bands relative to rail
    topy = {}
    for (px, py) in pts_top_near: topy[int(round(px))] = min(topy.get(int(round(px)), 99), py)
    def ht(x, y):
        ty = topy.get(x, y); d = y - ty
        if d < 1.2: return WOOD[4]
        if 3 <= d < 5: return (GOLD[1] if (x % 2 == 0 or True) else GOLD[2])
        base = 1.4 + (.8 if (x // 2) % 5 == 0 else 0) - d * .03
        return base + (-.9 if int(d) % 3 == 0 else 0)
    c.fill(side, WOOD, ht)
    # bow end cap (visible, faces SE)
    t = 1.0
    # sterncastle block
    s0, s1 = hull_u0 + 1, hull_u0 + 8
    sw = half((s0 + 4 - hull_u0) / (hull_u1 - hull_u0)) - 1
    zb = zt(0.2)
    wallR(c, s1, vc - sw, vc + sw, zb, zb + 5, WOOD, lambda a, z: 1.2 + (.8 if int(a) % 3 == 0 else 0))
    wallL(c, s0, s1, vc + sw, zb, zb + 5, WOOD, lambda a, z: 2.6 + (.7 if int(a) % 3 == 0 else 0))
    top(c, s0, s1, vc - sw, vc + sw, zb + 5, WOOD, lambda x, y: 4 - (.7 if (x + y) % 2 else 0))
    for a in (s0 + 2, s0 + 5): rectL(c, a, a + 1.5, zb + 1.5, zb + 3.5, vc + sw, INK)
    # bowsprit
    c.line3((hull_u1 - 1, vc, zt(1) - 1), (hull_u1 + 7, vc, zt(1) + 4), WOOD[1])
    # masts and sails
    def sail(u, z0, z1, hw, col=PLAST):
        bulge = 1.6
        pts = []
        for i in range(9):
            v = vc - hw + 2 * hw * i / 8; b = bulge * (1 - ((i - 4) / 4) ** 2)
            pts.append(c.P(u + b, v, z1 - (0.6 if i in (0, 8) else 0)))
        for i in range(8, -1, -1):
            v = vc - hw + 2 * hw * i / 8; b = bulge * (1 - ((i - 4) / 4) ** 2)
            pts.append(c.P(u + b, v, z0 + (0.0)))
        c.fill(pts, col, lambda x, y: 3.0 + (.5 if (x + y) % 2 else 0) - 0.14 * (x + 8) + (-1.2 if (x - y) % 11 == 0 else 0))
        c.line3((u, vc - hw - .5, z1), (u, vc + hw + .5, z1), WOOD[1]); c.line3((u + bulge*.2, vc - hw, z0), (u + bulge*.2, vc + hw, z0), STONE[2]); c.line3((u, vc - hw, z0), (u+bulge*.3, vc - hw*.8, (z0+z1)/2), STONE[2]) if False else None
        c.line3((u + bulge, vc - hw * .2, z0 + (z1 - z0) / 2), (u + bulge, vc + hw * .2, z0 + (z1 - z0) / 2), PLAST[1]) if False else None
    deck = zt(.5)
    masts = [(8, 24, 4.2, ()), (16, 34, 5.6, ()), (24.5, 27, 4.6, ())]
    for (mu, mh, hw, _) in masts:
        t = (mu - hull_u0) / (hull_u1 - hull_u0)
        base = zt(t) 
        c.line3((mu, vc, base), (mu, vc, base + mh), WOOD[0]); c.line3((mu + .01, vc, base), (mu + .01, vc, base + mh), WOOD[1])
        # sails stacked
        if mh > 30:
            sail(mu, base + 5, base + 16, hw); sail(mu, base + 18, base + 27, hw * .72); sail(mu, base + 29, base + mh - 1, hw * .45)
        else:
            sail(mu, base + 4, base + mh * .58, hw); sail(mu, base + mh * .64, base + mh - 1, hw * .66)
    # rigging
    mt = lambda mu, mh: (mu, vc, zt((mu - hull_u0) / (hull_u1 - hull_u0)) + mh)
    c.line3(mt(16.5, 33), (hull_u1 + 7, vc, zt(1) + 4), STONE[3]); c.line3(mt(16.5, 33), (hull_u0 + 1, vc, zb + 5), STONE[3])
    c.line3(mt(24, 27), (hull_u1 + 7, vc, zt(1) + 4), STONE[3]); c.line3(mt(9.5, 25), mt(16.5, 33), STONE[3])
    # pennant
    px, py = c.P(16.5, vc, zt(.5) + 33)
    c.line((px, py), (px, py - 3), WOOD[0]); c.fill([(px, py - 3), (px - 5, py - 2), (px, py - 1)], col=RED)
    c.outline()
    # waterline foam: light dither dashes along the hull base
    for i, u in enumerate(stations):
        t = (u - hull_u0) / (hull_u1 - hull_u0); w = half(t)
        x, y = c.P(u, vc + w * .55 + 1, 1 + 2.5 * (1 - t) ** 2 - 1)
        if i % 2 == 0: c.put(int(x), int(y), OCEAN[6])
    return c.crop()

def cart():
    c = new(1, 1, up=22, down=4); 
    u0, u1, v0, v1 = 4, 11, 4, 10
    shadow(c, 2, -3, 9, 3, EARTH[0])
    # ox ahead (u 11..15)
    ox, oy = c.P(14, 7, 0)
    c.rect(int(ox) - 3, int(oy) - 6, int(ox) + 3, int(oy) - 2, WOOD[2]); c.rect(int(ox) - 3, int(oy) - 6, int(ox) + 3, int(oy) - 5, WOOD[3])
    for dx in (-3, 2): c.rect(int(ox) + dx, int(oy) - 2, int(ox) + dx, int(oy) , WOOD[1])
    c.rect(int(ox) + 3, int(oy) - 8, int(ox) + 5, int(oy) - 5, WOOD[2]); c.put(int(ox) + 5, int(oy) - 9, PLAST[3]); c.put(int(ox) + 3, int(oy) - 9, PLAST[3])
    wallL(c, u0, u1, v1, 3, 7, WOOD, lambda a, z: 2.6 + (.8 if int(a) % 2 == 0 else 0)); wallR(c, u1, v0, v1, 3, 7, WOOD, 1.2)
    top(c, u0, u1, v0, v1, 7, THATCH, lambda x, y: 2.8 + (.8 if (x + y) % 2 else 0))
    wx, wy = c.P(7, v1, 3)
    c.disc(wx, wy, 3, 3, WOOD, 1.5); c.disc(wx, wy, 2, 2, WOOD, 3.4); c.put(int(wx), int(wy), WOOD[0]); c.line((wx - 2, wy), (wx + 2, wy), WOOD[1])
    c.line3((u1, 7, 4), (u1 + 3, 7, 3), WOOD[1])
    c.outline(); return c.crop()

def colonist(k):
    c = new(1, 1, up=14, down=2); cx, cy = 0, -6
    coats = [(COATB, WOOD[0]), (ROOF, WOOD[1]), (COATG, STONE[1]), (PLAST, WOOD[2])][k]
    coat, hat = coats
    c.put(cx - 1, cy + 1, EARTH[0]); c.put(cx + 1, cy + 1, EARTH[0])
    c.put(cx - 1, cy, WOOD[1]); c.put(cx + 1, cy, WOOD[1])       # feet
    c.rect(cx - 2, cy - 6, cx + 2, cy - 1, coat[1]); c.rect(cx + 1, cy - 6, cx + 2, cy - 1, coat[0]); c.rect(cx - 2, cy - 6, cx - 2, cy - 2, coat[2])
    c.rect(cx - 1, cy - 8, cx + 1, cy - 7, SKIN[1]); c.put(cx - 1, cy - 8, SKIN[2])
    c.rect(cx - 2, cy - 10 + (1 if k == 2 else 0), cx + 2, cy - 9, hat)
    if k in (0, 1): c.rect(cx - 1, cy - 11, cx + 1, cy - 11, hat)
    c.line((cx - 3, cy - 5), (cx - 3, cy - 2), SKIN[0]); 
    c.outline(); return c.crop()

def wheat():
    c = new(2, 2, up=0, down=0, side=0)
    c.a[:] = 0
    U = V = 32
    from terrain import DM
    # footprint 64x32 diamond, anchor at south corner (32,32)
    c = Cv(64, 32, 32, 32, 32, 32)
    pts = [(0, -32), (32, -16), (0, 0), (-32, -16)]
    def tone(x, y):
        u = (x + 2 * y + 64) / 2; v = (2 * y + 64 - x) / 2
        edge = min(u, v, 32 - u, 32 - v)
        row = int(v // 2.0) % 2
        if edge < 2.0: return (EARTH[1] if (x + y) % 2 == 0 else EARTH[2]) if edge > 1 else EARTH[0]
        # wheat rows parallel to u axis; stalks tick marks
        base = 2.6 if row == 0 else 1.7
        if int(u) % 3 == 0 and row == 0: base += 1.0
        if int(u + v) % 5 == 0: base -= .6
        if (int(u * 3) * 7 + int(v) * 13) % 31 == 0: return RED
        return THATCH[0] if int(v) % 2 == 1 and int(u) % 4 == 1 else base
    def t2(x, y):
        r = tone(x, y)
        return r if isinstance(r, tuple) else (THATCH[int(r)] if False else r)
    c.fill(pts, THATCH, lambda x, y: (lambda r: r)(tone(x, y)))
    return c

def build(out):
    anchors = {}
    def sv(name, cv): anchors[name] = cv.save(f'{out}/{name}.png')
    for k in range(3): sv(f'tree_{k}', tree(k))
    sv('rock_0', rock())
    for k in range(3): sv(f'house_{k}', house(k))
    sv('farmhouse_0', farmhouse()); sv('windmill_0', windmill()); sv('lumberjack_0', lumberjack())
    sv('chapel_0', chapel()); sv('warehouse_0', warehouse()); sv('pier_0', pier()); sv('ship_0', ship())
    sv('cart_0', cart())
    for k in range(4): sv(f'colonist_{k}', colonist(k))
    sv('wheat_field_0', wheat())
    return anchors
