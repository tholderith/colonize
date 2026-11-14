import random
from pxl import *
from terrain import TW

def new(wt, H): return Spr(64 * wt, H)

def finish(s, cx, cy, sh=26, dx=5):
    s.outline(INK); s.shadow(cx, cy, sh, dx); return s.final()

# ------------------------------------------------------------------ nature
def tree(v):
    s = new(1, 72); cx, by = 32, 56
    L = M('leaf'); 
    if v == 0:      # broadleaf
        s.rect(cx - 2, by - 12, cx + 1, by, M('bark')[1]); s.rect(cx - 2, by - 12, cx - 1, by, M('bark')[2])
        s.blob(cx, by - 16, 14, 10, [L[0], L[1], L[2], L[3]]); s.blob(cx - 6, by - 26, 10, 9, [L[1], L[2], L[3], L[4]])
        s.blob(cx + 6, by - 26, 9, 8, [L[1], L[2], L[3], L[3]]); s.blob(cx - 1, by - 34, 8, 7, [L[1], L[3], L[4], L[5]])
        for p in ((cx - 8, by - 30), (cx - 3, by - 37), (cx - 6, by - 22)): s.px(*p, L[5])
    elif v == 1:    # pine
        P = M('pine')
        s.rect(cx - 1, by - 8, cx + 1, by, M('bark')[1])
        for i, (w, y) in enumerate(((13, by - 6), (11, by - 15), (9, by - 24), (6, by - 32))):
            s.poly([(cx - w, y), (cx, y - 14), (cx + w, y)], P[1])
            s.poly([(cx - w, y), (cx, y - 14), (cx, y)], P[2])
            s.poly([(cx - w + 2, y - 1), (cx - 1, y - 12), (cx - 1, y - 6)], P[3]) if False else None
            s.line((cx - w + 1, y - 1), (cx, y - 13), P[4])
        s.px(cx, by - 46, P[4])
    else:           # round autumn-ish / fruit tree
        s.rect(cx - 2, by - 10, cx + 1, by, M('bark')[1]); s.rect(cx - 2, by - 10, cx - 1, by, M('bark')[2])
        A = [C('roof', 1), C('roof', 2), C('roof', 3), C('roof', 4)] if False else [C('grass', 1), C('grass', 2), C('grass', 3), C('grass', 4)]
        s.blob(cx, by - 20, 15, 14, A)
        for p in ((-6, -26), (4, -24), (-2, -16), (8, -16), (-9, -17)): s.px(cx + p[0], by + p[1], C('roof', 3)); s.px(cx + p[0] + 1, by + p[1], C('roof', 2))
    return finish(s, cx, by + 2, 18, 4)

def rock():
    s = new(1, 48); cx, by = 32, 36
    R = M('rock')
    s.poly([(cx - 12, by), (cx - 9, by - 8), (cx - 2, by - 12), (cx + 7, by - 9), (cx + 12, by - 2), (cx + 6, by + 3), (cx - 6, by + 3)], R[2])
    s.poly([(cx - 9, by - 8), (cx - 2, by - 12), (cx + 2, by - 8), (cx - 3, by - 3), (cx - 10, by - 2)], R[4])
    s.poly([(cx + 2, by - 8), (cx + 7, by - 9), (cx + 12, by - 2), (cx + 6, by + 3), (cx + 1, by + 2)], R[1])
    s.line((cx - 3, by - 3), (cx + 1, by + 2), R[1]); s.px(cx - 6, by - 8, R[5]); s.px(cx - 5, by - 9, R[5])
    s.poly([(cx + 12, by + 1), (cx + 17, by - 1), (cx + 16, by + 3), (cx + 12, by + 3)], R[2]); s.px(cx + 14, by, R[4])
    s.px(cx - 14, by + 2, C('grass', 3)); s.px(cx - 13, by + 3, C('grass', 4))
    return finish(s, cx, by + 2, 16, 3)

# ------------------------------------------------------------------ buildings
def house(v):
    s = new(1, 72); cx, cy = 32, 56
    walls = [M('plaster'), M('ochre'), M('timber'), M('plaster')][v]
    roof = [M('roof'), M('slate'), M('thatch'), M('roof')][v]
    orient = [0, 1, 0, 1][v]
    hw, h = 18, 12 + (v % 2) * 2
    T, R, B, L = iso_box(s, cx, cy, hw, h, walls, texture='brick' if v in (0,) else 'plank', lit=(3, 2) if v != 2 else (2, 1))
    if v == 2: pass
    rh = 11
    if orient == 0:
        door(s, B, R, .35, .22, 8); window(s, L, B, h, .22, 5); window(s, L, B, h, .62, 5)
        gable_roof(s, cx, cy, hw, h, rh, roof, 0, 2, walls)
        chimney(s, cx - 9, cy - h - 10, 8)
    else:
        door(s, L, B, .55, .22, 8); window(s, B, R, h, .2, 5); window(s, B, R, h, .62, 5)
        gable_roof(s, cx, cy, hw, h, rh, roof, 1, 2, walls)
        chimney(s, cx + 6, cy - h - 12, 8)
    if v == 3: s.rect(cx + 14, cy + 1, cx + 17, cy + 5, M('plank')[2]); s.rect(cx + 14, cy + 1, cx + 17, cy + 1, M('plank')[4])  # barrel
    return finish(s, cx, cy, 24)

def farmhouse():
    s = new(1, 78); cx, cy = 32, 62
    w = M('timber'); r = M('thatch'); hw, h = 21, 13
    T, R, B, L = iso_box(s, cx, cy, hw, h, w, lit=(3, 2), texture='plank')
    door(s, B, R, .3, .25, 9); window(s, L, B, h, .2, 5); window(s, L, B, h, .58, 5)
    gable_roof(s, cx, cy, hw, h, 14, r, 0, 3, w)
    s.rect(cx + 14, cy - 2, cx + 18, cy + 3, C('gold', 2)); s.rect(cx + 14, cy - 2, cx + 18, cy - 2, C('gold', 3)); s.px(cx + 16, cy, C('gold', 1))  # hay
    return finish(s, cx, cy, 26)

def windmill():
    s = new(1, 116); cx, cy = 32, 100
    st = M('plaster'); 
    # tapered body
    bw, tw, h = 17, 10, 44
    def lvl(hw, k): return corners(cx, cy, hw, k)
    Tb, Rb, Bb, Lb = lvl(bw, 0); Tt, Rt, Bt, Lt = lvl(tw, h)
    s.poly([Lb, Bb, Bt, Lt], st[3]); s.poly([Bb, Rb, Rt, Bt], st[2])
    for k in range(4, h, 5):
        t = k / h; hwk = bw + (tw - bw) * t
        Tk, Rk, Bk, Lk = corners(cx, cy, int(hwk), k)
        s.line((Lk[0] + 1, Lk[1]), (Bk[0], Bk[1]), st[2]); s.line((Bk[0], Bk[1]), (Rk[0] - 1, Rk[1]), st[1])
    s.line(Bb, Bt, st[1]); s.line(Lb, Lt, st[4])
    door(s, Bb, (Bb[0] + 8, Bb[1] - 4), 0, 1, 9)
    window(s, (cx - 6, cy + 8 - 20 // 2 + 5), (cx + 0, cy + 8 - 20 // 2 + 5), 0, 0, 14 + 8, w=1) if False else None
    # cap (hip roof)
    ap = hip_roof(s, cx, cy, tw + 1, h, 12, M('roof'), 2)
    # sails on right face: hub
    hx, hy = cx + 9, cy - h + 2 + 8 - 4
    hx, hy = cx + 6, cy - h - 2
    sail = M('sail')
    for ang in ((1, -1), (-1, -1), (-1, 1), (1, 1)):
        dx, dy = ang
        L_ = 25
        x2, y2 = hx + dx * L_ * .7, hy + dy * L_ * .85
        s.line((hx, hy), (x2, y2), M('timber')[2])
        # blade as quad
        nx, ny = -dy, dx
        q = [(hx + dx * 8 + nx * 1, hy + dy * 8 + ny * 1), (x2, y2), (x2 + nx * 5 - dx * 0, y2 + ny * 5), (hx + dx * 8 + nx * 6, hy + dy * 8 + ny * 6)]
        s.poly(q, sail[3]); s.line(q[0], q[1], M('timber')[2])
        s.line(q[3], q[2], sail[1])
    s.ell(hx - 2, hy - 2, hx + 2, hy + 2, M('timber')[1]); s.px(hx, hy, M('gold')[3])
    return finish(s, cx, cy, 24)

def lumberjack():
    s = new(1, 72); cx, cy = 32, 56
    w = M('plank'); hw, h = 14, 10
    cx2 = cx - 4
    T, R, B, L = iso_box(s, cx2, cy - 2, hw, h, w, lit=(2, 1), texture='plank')
    door(s, B, R, .3, .3, 7); window(s, L, B, h, .3, 4)
    gable_roof(s, cx2, cy - 2, hw, h, 8, M('thatch'), 0, 2, w)
    # log pile (right)
    lg = M('bark')
    for i, (x, y) in enumerate(((cx + 8, cy + 6), (cx + 13, cy + 8), (cx + 18, cy + 10), (cx + 11, cy + 2), (cx + 16, cy + 4))):
        s.rect(x, y - 3, x + 7, y, lg[2]); s.rect(x, y - 3, x + 7, y - 3, lg[3]); s.rect(x + 7, y - 3, x + 7, y, lg[1])
        s.px(x, y - 2, C('sand', 3)); s.px(x, y - 1, C('sand', 2))
    # stump + axe
    s.rect(cx - 20, cy + 5, cx - 15, cy + 9, lg[1]); s.rect(cx - 20, cy + 4, cx - 15, cy + 5, C('sand', 3))
    s.line((cx - 17, cy + 4), (cx - 13, cy - 1), lg[3]); s.rect(cx - 14, cy - 3, cx - 12, cy - 1, M('stone')[3])
    return finish(s, cx, cy, 28)

def chapel():
    s = new(2, 140); cx, cy = 64, 108
    st = M('plaster'); 
    # nave along x axis (orient 0) offset left, tower right front
    ncx, ncy = cx - 6, cy - 6
    T, R, B, L = iso_box(s, ncx, ncy, 34, 20, st, lit=(3, 2), texture='brick')
    for u in (.18, .42, .66): window(s, L, B, 20, u, 7, w=.1, hgt=8)
    door(s, B, R, .3, .3, 12)
    gable_roof(s, ncx, ncy, 34, 20, 16, M('slate'), 0, 3, st)
    # tower
    tcx, tcy = cx + 22, cy + 4
    iso_box(s, tcx, tcy, 14, 40, st, lit=(3, 2), texture='brick')
    Tt, Rt, Bt, Lt = corners(tcx, tcy, 14)
    window(s, Bt, Rt, 40, .35, 22, w=.25, hgt=9, wmat=None)
    ap = hip_roof(s, tcx, tcy, 14, 40, 22, M('slate'), 2)
    s.line(ap, (ap[0], ap[1] - 8), M('gold')[2]); s.line((ap[0] - 2, ap[1] - 6), (ap[0] + 2, ap[1] - 6), M('gold')[3]); s.px(ap[0], ap[1] - 9, M('gold')[3])
    return finish(s, cx, cy, 52)

def warehouse():
    s = new(2, 138); cx, cy = 64, 106
    w = M('timber'); hw, h = 40, 22
    T, R, B, L = iso_box(s, cx, cy - 4, hw, h, w, lit=(3, 2), texture='plank')
    door(s, L, B, .22, .22, 14); door(s, L, B, .5, .22, 14)
    window(s, B, R, h, .5, 9, w=.12)
    for u in (.8,): window(s, L, B, h, u, 9, w=.1)
    gable_roof(s, cx, cy - 4, hw, h, 18, M('roof'), 1, 3, w)
    # crates + barrels at front-left of ground
    for i, (x, y) in enumerate(((cx - 30, cy + 8), (cx - 24, cy + 11))):
        s.rect(x, y - 6, x + 6, y, M('plank')[3]); s.rect(x, y - 6, x + 6, y - 6, M('plank')[4]); s.rect(x + 6, y - 6, x + 6, y, M('plank')[1]); s.line((x, y - 3), (x + 6, y - 3), M('plank')[1])
    s.rect(cx + 22, cy + 12, cx + 27, cy + 18, M('plank')[2]); s.rect(cx + 22, cy + 14, cx + 27, cy + 14, M('stone')[1]); s.rect(cx + 22, cy + 17, cx + 27, cy + 17, M('stone')[1])
    # flag
    fx, fy = cx + 30, cy - 32
    return finish(s, cx, cy, 58)

# ------------------------------------------------------------------ flat
def wheat():
    s = new(2, 64)
    # diamond
    for y in range(64):
        w = 4 * min(y, 63 - y) + 4
        for x in range(64 - w // 2, 64 + w // 2): s.px(x, y, C('wood', 2))
    W = M('wheat'); rnd = random.Random(7)
    def inside(x, y): return 0 <= y < 64 and 64 - (4 * min(y, 63 - y) + 4) // 2 + 2 <= x <= 64 + (4 * min(y, 63 - y) + 4) // 2 - 3
    # rows along axis (dx=2, dy=1) spaced 4px vertically
    for off in range(-40, 48, 5):
        for x in range(0, 128):
            y = 32 + off // 1 + (x - 64) // 2 - 0
            yy = y + 0
            if not inside(x, yy): continue
            bright = (x // 3 + off) % 3
            col = [W[3], W[2], W[3]][bright] if True else W[2]
            s.px(x, yy, col)
            if inside(x, yy - 1): s.px(x, yy - 1, W[4] if (x + off) % 4 == 0 else W[2])
            if inside(x, yy + 1): s.px(x, yy + 1, W[1])
    # border / dirt edge
    for y in range(64):
        w = 4 * min(y, 63 - y) + 4
        for x in (64 - w // 2, 64 + w // 2 - 1, 64 - w // 2 + 1, 64 + w // 2 - 2):
            pass
    # scarecrow-free: add a few poppies
    for _ in range(8):
        x = rnd.randrange(30, 98); y = rnd.randrange(16, 48)
        if inside(x, y): s.px(x, y, C('roof', 3))
    # soft edge: darker earth rim 
    im = s.im; P = im.load()
    for y in range(64):
        for x in range(128):
            if P[x, y][3] and not inside(x, y): P[x, y] = C('wood', 1) + (255,)
    return s.final()

def pier():
    s = new(1, 56); cx, cy = 32, 40
    # deck: from mid(L,T) to mid(B,R) direction (2,1); width perpendicular
    T, R, B, L = corners(cx, cy, 32)
    a0 = lerp(L, T, .5); a1 = lerp(B, R, .5)   # centreline ends
    def off(p, k): return (p[0] + k * 2 * 0.5 * 1, p[1] + k * -0.5)  # perpendicular (+,-)
    hwid = 7
    pw = M('plank')
    # posts
    for t in (0, .5, 1):
        p = lerp(a0, a1, t)
        for sgn in (-1, 1):
            q = (p[0] + sgn * hwid * 2 * .5 * 2 // 2, p[1] - sgn * hwid // 2 + 6)
            s.rect(int(q[0]) - 1, int(q[1]) - 2, int(q[0]) + 1, int(q[1]) + 8, pw[0])
            s.rect(int(q[0]) - 1, int(q[1]) - 2, int(q[0]) - 1, int(q[1]) + 8, pw[1])
            s.px(int(q[0]) - 1, int(q[1]) + 8, C('water', 5)); s.px(int(q[0]), int(q[1]) + 9, C('water', 6)); s.px(int(q[0]) - 2, int(q[1]) + 9, C('water', 6))
    # deck slab
    A = [(a0[0] - hwid, a0[1] + hwid // 2), (a0[0] + hwid, a0[1] - hwid // 2), (a1[0] + hwid, a1[1] - hwid // 2), (a1[0] - hwid, a1[1] + hwid // 2)]
    s.poly([(x, y + 3) for x, y in A], pw[1])
    s.poly(A, pw[3])
    for k in range(1, 12):
        t = k / 12
        p = lerp(A[0], A[3], t); q = lerp(A[1], A[2], t)
        # boards run across deck: line between lines parallel to axis -> use cross lines
    for k in range(0, 10):
        t = k / 10
        p = lerp(A[0], A[1], 0); 
        c0 = lerp(A[0], A[3], t); c1 = lerp(A[1], A[2], t)
        s.line(c0, c1, pw[2] if k % 2 else pw[4])
    s.line(A[0], A[3], pw[1]); s.line(A[1], A[2], pw[4])
    # bollard + rope coil
    s.rect(int(a1[0]) - 1, int(a1[1]) - 5, int(a1[0]) + 1, int(a1[1]) - 1, pw[0]); s.px(int(a1[0]), int(a1[1]) - 5, pw[4])
    s.outline(INK)
    return s.final()

# ------------------------------------------------------------------ moving
def ship():
    s = new(2, 124); cx, cy = 64, 92
    hl = M('hull'); sail = M('sail')
    ax, ay = 2, 1  # along-axis per unit (iso x)
    def P(t, dz=0, side=0):  # t along axis in [-1,1], dz height, side +1 far/-1 near
        return (cx + 8 + t * 33 + side * 6, cy + 1 + t * 16.5 - side * 3 - dz)
    # foam/wake
    for t in range(-12, 13):
        pass
    near = []; 
    # hull sides (near side polygon): gunwale line (raised ends) and keel line
    n = 20
    top_n = [P(-1 + 2 * i / n, 8 + 4 * (abs(2 * i / n - 1) ** 2) * 1 + (4 if i / n < .15 else 0), -1) for i in range(n + 1)]
    bot_n = [P(-.85 + 1.75 * i / n, -2 + 4.0 * (1 - (abs(2 * i / n - 1) ** 2)) * -1 + 0, -1) for i in range(n + 1)]
    # keep simple: near side
    top_f = [(x + 12, y - 6) for x, y in top_n]
    # deck (between far and near gunwale)
    s.poly(top_n + top_f[::-1], hl[3])
    # near hull face
    face_pts = top_n + [(x, y + 11) for x, y in top_n[::-1]]
    # tapered at bow and stern
    bl = [(x, y + 11 - int(5 * (abs(2 * i / n - 1) ** 3))) for i, (x, y) in enumerate(top_n)]
    s.poly(top_n + bl[::-1], hl[2])
    # lower dark strake
    bl2 = [(x, y - 4) for x, y in bl]
    s.poly(bl2 + bl[::-1], hl[1])
    # white/gold stripe
    for i in range(n):
        a = (top_n[i][0], top_n[i][1] + 3); b = (top_n[i + 1][0], top_n[i + 1][1] + 3)
        s.line(a, b, M('gold')[2])
    s.line((top_n[0][0], top_n[0][1]), (top_n[-1][0], top_n[-1][1]), hl[4]) if False else None
    for i in range(n): s.line(top_n[i], top_n[i + 1], hl[4])
    # port holes
    for i in range(3, n - 2, 3):
        s.px(top_n[i][0], top_n[i][1] + 6, INK)
    # stern castle (raised block at back-left)
    sx, sy = top_n[2]
    s.poly([(sx, sy), (sx + 12, sy - 6), (sx + 12, sy - 14), (sx, sy - 8)], hl[2]); s.poly([(sx, sy - 8), (sx + 12, sy - 14), (sx + 20, sy - 10), (sx + 8, sy - 4)], hl[3])
    s.px(sx + 3, sy - 4, M('glass')[3]); s.px(sx + 7, sy - 6, M('glass')[3])
    # masts & sails
    masts = [(-.45, 52, 20), (.0, 62, 24), (.48, 44, 16)]
    for t, mh, sw in masts:
        bx, by = P(t, 10, 0)
        s.line((bx, by), (bx, by - mh), hl[0]); s.line((bx + 1, by), (bx + 1, by - mh), hl[1])
        # two sails stacked for tall masts (square rig seen from the side -> parallelograms with sheer along (-2,1))
        levels = [(mh - 4, mh // 2 + 1)] if mh < 50 else [(mh - 4, mh * 5 // 9), (mh * 5 // 9 - 1, 14)]
        for (ytop, ybot) in levels:
            hwid = sw // 2 + 3 - (3 if ytop > mh - 6 and mh >= 50 and levels[0][0] == ytop else 0)
            q = [(bx - hwid, by - ytop + hwid // 2), (bx + hwid, by - ytop - hwid // 2), (bx + hwid + 2, by - ybot - hwid // 2 + 3), (bx - hwid + 2, by - ybot + hwid // 2 + 3)]
            # belly: draw lighter centre
            s.poly(q, sail[3])
            m1 = lerp(q[0], q[1], .5); m2 = lerp(q[3], q[2], .5)
            s.poly([q[0], m1, m2, q[3]], sail[4])
            s.poly([lerp(q[1], q[0], .15), q[1], q[2], lerp(q[2], q[3], .15)], sail[2])
            s.line(q[3], q[2], sail[1]); s.line(q[0], q[1], hl[3])
            s.px(bx - 3, by - (ytop + ybot) // 2 + 2, sail[2])
    # bowsprit + jib
    bx, by = top_n[-1]
    s.line((bx - 2, by - 1), (bx + 10, by - 6), hl[2])
    fx, fy = P(.0, 10, 0)[0], P(.0, 10, 0)[1] - 62
    s.poly([(fx, fy), (fx + 9, fy - 2), (fx + 3, fy - 1)], M('paint_red')[2])
    s.line((fx, fy), (fx, fy - 2), hl[0])
    # rigging
    s.line((fx, fy + 2), (bx + 10, by - 6), hl[1])
    s.outline(INK)
    # water foam
    im = s.im
    out = Spr(s.w, s.h)
    out.im = Image.new('RGBA', (s.w, s.h), (0, 0, 0, 0)); out.d = ImageDraw.Draw(out.im)
    for t in range(-4, 5):
        x = cx + 8 + t * 6; y = cy + 1 + t * 3 + 12
        out.px(x, y + 1, C('water', 6)); out.px(x + 1, y + 1, C('water', 6)); out.px(x - 1, y + 2, C('water', 5))
    out.px(cx + 44, cy + 20, C('water', 6)); out.px(cx + 46, cy + 21, C('water', 6))
    out.im.alpha_composite(s.im)
    return out.final()

def cart():
    s = new(1, 56); cx, cy = 32, 40
    wd = M('plank')
    # wagon bed along x axis, small
    cx2 = cx - 5
    T, R, B, L = corners(cx2, cy, 14, 5)
    # bed as low box 
    iso_box(s, cx2, cy, 12, 5, wd, lit=(2, 1), texture=None, base=4)
    # sacks/load
    s.blob(cx2 - 3, cy - 13, 4, 3, [C('sand', 1), C('sand', 2), C('sand', 3), C('sand', 4)]); s.blob(cx2 + 3, cy - 11, 4, 3, [C('sand', 1), C('sand', 2), C('sand', 3), C('sand', 4)])
    # wheel (near)
    s.ell(cx2 - 5, cy - 4, cx2 + 1, cy + 5, wd[0]); s.ell(cx2 - 4, cy - 3, cx2, cy + 4, wd[3]); s.ell(cx2 - 3, cy - 2, cx2 - 1, cy + 2, wd[1]); s.px(cx2 - 2, cy, M('gold')[2])
    # ox
    ox = M('ox')
    ox_c = (cx + 14, cy + 2)
    s.poly([(ox_c[0] - 6, ox_c[1] - 9), (ox_c[0] + 5, ox_c[1] - 4), (ox_c[0] + 5, ox_c[1] + 3), (ox_c[0] - 6, ox_c[1] - 2)], C('sand', 3) if False else ox[3])
    s.poly([(ox_c[0] - 6, ox_c[1] - 9), (ox_c[0] + 5, ox_c[1] - 4), (ox_c[0] + 3, ox_c[1] - 6), (ox_c[0] - 6, ox_c[1] - 11)], ox[4])
    s.rect(ox_c[0] + 4, ox_c[1] - 8, ox_c[0] + 8, ox_c[1] - 4, ox[2])
    s.px(ox_c[0] + 8, ox_c[1] - 4, INK); s.px(ox_c[0] + 5, ox_c[1] - 9, C('sand', 4)); s.px(ox_c[0] + 8, ox_c[1] - 9, C('sand', 4))
    for dx in (-5, 3):
        s.rect(ox_c[0] + dx, ox_c[1] - 1, ox_c[0] + dx + 1, ox_c[1] + 4, ox[0])
    s.line((cx2 + 8, cy - 4), (ox_c[0] - 6, ox_c[1] - 5), ox[1])
    return finish(s, cx, cy, 18, 3)

def colonist(v):
    s = new(1, 56); cx, cy = 32, 38
    tun = [M('paint_red')[2], M('paint_blue')[2], C('grass', 3), C('gold', 2)][v]
    tund = [M('paint_red')[1], M('paint_blue')[1], C('grass', 1), C('gold', 1)][v]
    s.rect(cx - 2, cy - 9, cx + 1, cy - 2, tun); s.rect(cx + 1, cy - 9, cx + 1, cy - 2, tund)
    s.rect(cx - 2, cy - 2, cx - 2, cy, M('plank')[1]); s.rect(cx + 1, cy - 2, cx + 1, cy, M('plank')[0])
    s.rect(cx - 1, cy - 13, cx + 1, cy - 10, C('skin', 1)); s.px(cx + 1, cy - 11, C('skin', 0))
    s.rect(cx - 2, cy - 14, cx + 2, cy - 14, M('plank')[1]); s.rect(cx - 1, cy - 15, cx + 1, cy - 15, M('plank')[2])
    s.px(cx - 3, cy - 7, C('skin', 1)); s.px(cx + 2, cy - 6, C('skin', 1))
    return finish(s, cx, cy, 8, 2)
