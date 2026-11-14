"""Buildings: houses, farmhouse, lumberjack, chapel, warehouse, windmill."""
from wb import *
import mats as MT
import random

def frame_x(w, face, wall, tangent_half, z0, z1, posts, mat, wpost=0.022, d=0.010, braces=True, rails=(), rail_w=0.02):
    """timber framing on a wall face"""
    for a in posts: fb(w, mat, face, wall, a, z0, wpost, z1 - z0, d)
    for zr in rails:
        fb(w, mat, face, wall, 0.0, zr, 2 * tangent_half, rail_w, d)
    if braces and len(posts) > 1:
        ps = sorted(posts)
        for a, b in zip(ps[:-1], ps[1:]):
            n, t = FACES[face]
            zlo = z0 + (0.0 if not rails else 0.0); zhi = z1
            for (p, q, zl, zh) in (((a + wpost / 2 if False else a), b, zlo, zhi),):
                pass

def brace(w, face, wall, a, b, za, zb, mat, d=0.010, wd=0.014):
    n, t = FACES[face]
    def pt(al, z, off):
        x = (wall + n[0] * off) if n[0] else al
        y = (wall + n[1] * off) if n[1] else al
        return (x, y, z)
    w.beam(mat, pt(a, za, d / 2), pt(b, zb, d / 2), wd, d)

def house(ctr, v, seed=0):
    rng = random.Random(100 + v)
    w = W(ctr, f'house{v}')
    P = {
        0: dict(wx=0.74, wy=0.54, wh=0.36, rh=0.30, ridge='x', plaster=(0.80, 0.75, 0.64), roof='clay', door='y-', chim='x-', frame=True),
        1: dict(wx=0.60, wy=0.60, wh=0.30, rh=0.34, ridge='y', plaster=None, roof='thatch', door='y-', chim='y+', frame=False),
        2: dict(wx=0.76, wy=0.58, wh=0.44, rh=0.30, ridge='x', plaster=(0.74, 0.70, 0.60), roof='clay', door='y-', chim='x+', frame=True, stone=0.15),
        3: dict(wx=0.66, wy=0.56, wh=0.40, rh=0.34, ridge='y', plaster=(0.76, 0.73, 0.66), roof='shingle', door='y-', chim='y+', frame=True),
    }[v]
    wx, wy, wh, rh = P['wx'], P['wy'], P['wh'], P['rh']
    hx, hy = wx / 2, wy / 2
    tim = MT.timber((0.27, 0.20, 0.14) if v != 3 else (0.22, 0.17, 0.13))
    stone = MT.masonry('stone', False)
    pl = MT.plaster(P['plaster']) if P['plaster'] else MT.planks((0.36, 0.30, 0.23), True, 0.05, 'siding', 0.03)
    roof = {'clay': MT.clay_tile(), 'thatch': MT.thatch(), 'shingle': MT.slate_shingle()}[P['roof']]
    fh = 0.055 + P.get('stone', 0)
    yard(w, 0.78, 0.72, name='yard')
    # foundation
    w.box(stone, 0, 0, (wx + 0.02, wy + 0.02, fh), 0)
    zs = fh
    if P.get('stone'):
        pass
    # walls
    w.box(pl, 0, 0, (wx, wy, wh - fh), zs) if False else None
    w.box(pl, 0, 0, (wx - 0.001, wy - 0.001, wh - fh), fh)
    ztop = wh
    # corner posts and plates
    if P['frame'] or v == 1:
        for sx in (-1, 1):
            for sy in (-1, 1):
                w.box(tim, sx * (hx - 0.006), sy * (hy - 0.006), (0.026, 0.026, wh - fh), fh)
        for face, wall, L in (('y-', -hy, hx), ('y+', hy, hx), ('x+', hx, hy), ('x-', -hx, hy)):
            fb(w, tim, face, wall, 0, fh + 0.0, 2 * L, 0.02, 0.011)
            fb(w, tim, face, wall, 0, ztop - 0.03, 2 * L, 0.03, 0.011)
    if P['frame'] and v != 1:
        for face, wall, L in (('y-', -hy, hx), ('y+', hy, hx), ('x+', hx, hy), ('x-', -hx, hy)):
            n = int(L * 2 / 0.19)
            for k in range(1, n):
                a = -L + 2 * L * k / n
                fb(w, tim, face, wall, a, fh, 0.02, wh - fh - 0.03, 0.009)
            for k in range(n):
                a0 = -L + 2 * L * k / n; a1 = -L + 2 * L * (k + 1) / n
                if (k + (1 if face[0] == 'x' else 0)) % 2 == 0 and (face != 'y-' or abs((a0 + a1) / 2) > 0.1):
                    brace(w, face, wall, a0 + 0.01, a1 - 0.01, ztop - 0.03, fh + 0.01, tim) if k % 2 == 0 else brace(w, face, wall, a0 + 0.01, a1 - 0.01, fh + 0.01, ztop - 0.03, tim)
    # roof
    ridge_x = P['ridge'] == 'x'
    thick = 0.03 if P['roof'] == 'thatch' else 0.016
    ov = (0.05, 0.075) if P['roof'] == 'thatch' else (0.045, 0.06)
    edge = tim if P['roof'] != 'thatch' else MT.thatch()
    if ridge_x: w.gable(roof, pl, 0, 0, (wx, wy), ztop, rh, 0.0, overhang=ov, thick=thick, mat_edge=edge, mat_gable=pl)
    else: w.gable(roof, pl, 0, 0, (wy, wx), ztop, rh, math.pi / 2, overhang=ov, thick=thick, mat_edge=edge, mat_gable=pl)
    # gable timber (king post / collar) on gable faces
    gfaces = [('x+', hx, hy), ('x-', -hx, hy)] if ridge_x else [('y+', hy, hx), ('y-', -hy, hx)]
    gh = rh
    for face, wall, L in gfaces:
        if P['frame'] or P['roof'] == 'thatch':
            n, t = FACES[face]
            def gp(al, z, off=0.006):
                return ((wall + n[0] * off) if n[0] else al, (wall + n[1] * off) if n[1] else al, z)
            w.beam(tim, gp(0, ztop), gp(0, ztop + gh * 0.85), 0.018, 0.012)
            w.beam(tim, gp(-L * 0.5, ztop + gh * 0.5), gp(L * 0.5, ztop + gh * 0.5), 0.016, 0.012)
            w.beam(tim, gp(-L, ztop), gp(0, ztop + gh), 0.016, 0.012)
            w.beam(tim, gp(L, ztop), gp(0, ztop + gh), 0.016, 0.012)
        # attic window
        window(w, face, wall, 0.0, ztop + gh * 0.28, 0.06, 0.075, shutters=False, sill=False)
    # ridge cap
    rc = MT.clay_tile() if P['roof'] != 'thatch' else MT.thatch()
    if ridge_x: w.box(rc, 0, 0, (wx + 2 * ov[0], 0.035, 0.022), ztop + rh - 0.008)
    else: w.box(rc, 0, 0, (0.035, wx + 2 * ov[0], 0.022), ztop + rh - 0.008)
    # openings on the two visible faces + others
    zw = fh + (wh - fh) * 0.58
    def eave_face_details(face, wall, L, with_door):
        if with_door:
            door(w, face, wall, -L * 0.28 if v != 3 else 0.0, z0=fh - 0.002)
            window(w, face, wall, L * 0.46, zw, shut=MT.painted('shutter', [(0.30, 0.40, 0.32), (0.45, 0.30, 0.22), (0.28, 0.34, 0.44), (0.40, 0.36, 0.24)][v]))
            if v in (0, 2): window(w, face, wall, -L * 0.72 if False else L * 0.12, zw + (0.0), 0.0 + 0.085, 0.10) if False else None
        else:
            window(w, face, wall, -L * 0.40, zw)
            window(w, face, wall, L * 0.40, zw)
    if ridge_x:
        eave_face_details('y-', -hy, hx, True); eave_face_details('y+', hy, hx, False)
        window(w, 'x+', hx, 0.0, zw); window(w, 'x-', -hx, 0.0, zw)
    else:
        # gable on y- faces: door on gable face at left
        door(w, 'y-', -hy, -hx * 0.30, z0=fh - 0.002)
        window(w, 'y-', -hy, hx * 0.45, zw)
        window(w, 'x+', hx, -hy * 0.45, zw); window(w, 'x+', hx, hy * 0.45, zw)
        window(w, 'x-', -hx, -hy * 0.45, zw); window(w, 'x-', -hx, hy * 0.45, zw)
        window(w, 'y+', hy, 0, zw)
    # chimney
    brick = MT.brickwork()
    cs = P['chim']
    if cs[0] == 'x': cx0, cy0 = (hx - 0.07) * (1 if cs[1] == '+' else -1), 0.0
    else: cy0, cx0 = (hy - 0.07) * (1 if cs[1] == '+' else -1), 0.0
    if (cs[0] == 'x') == ridge_x:
        w.box(brick, cx0, cy0, (0.06, 0.07, rh + 0.12), ztop - 0.04)
        w.box(MT.masonry('cap', True), cx0, cy0, (0.075, 0.085, 0.014), ztop + rh + 0.075)
        w.box(MT.solid('flue', (0.02, 0.02, 0.02), 1.0), cx0, cy0, (0.04, 0.05, 0.004), ztop + rh + 0.088)
    else:
        w.box(brick, cx0, cy0, (0.07, 0.06, rh + 0.12), ztop - 0.04)
        w.box(MT.masonry('cap', True), cx0, cy0, (0.085, 0.075, 0.014), ztop + rh + 0.075)
    # props
    if v == 0:
        barrel(w, -hx * 0.55, -hy - 0.07); barrel(w, -hx * 0.55 + 0.05, -hy - 0.05, r=0.024, h=0.05)
        w.box(tim, hx * 0.55, -hy - 0.07, (0.14, 0.035, 0.012), 0.032); w.box(tim, hx * 0.55 - 0.05, -hy - 0.07, (0.012, 0.03, 0.03), 0.0); w.box(tim, hx * 0.55 + 0.05, -hy - 0.07, (0.012, 0.03, 0.03), 0.0)
    if v == 1:
        for i in range(5):    # firewood stack at side
            for j in range(3 - i // 3):
                w.cyl(MT.bark(), (hx + 0.05 + i * 0.001, -0.12 + j * 0.035 + (i % 2) * 0.017, 0.02 + (i // 2) * 0.03), (hx + 0.05, -0.12 + j * 0.035 + (i % 2) * 0.017, 0.02 + (i // 2) * 0.03), 0.0, 0.0) if False else None
        woodpile(w, hx + 0.09, 0.05, 0.26, 3)
        barrel(w, hx * 0.1, -hy - 0.06)
    if v == 2:
        # lean-to shed on the +y side
        w.box(MT.planks((0.33, 0.27, 0.20), True, 0.05, 'shed'), 0.0, hy + 0.09, (0.34, 0.16, 0.18), 0.0)
        w.face(MT.clay_tile(), [(-0.19, hy - 0.01, 0.30), (0.19, hy - 0.01, 0.30), (0.19, hy + 0.20, 0.16), (-0.19, hy + 0.20, 0.16)])
        w.face(tim, [(-0.19, hy + 0.20, 0.16), (0.19, hy + 0.20, 0.16), (0.19, hy + 0.20, 0.14), (-0.19, hy + 0.20, 0.14)])
        crate(w, hx + 0.06, -0.1, 0.05); crate(w, hx + 0.06, -0.16, 0.04, 0.0, 0.3); crate(w, hx + 0.06, -0.1, 0.04, 0.043, 0.2)
    if v == 3:
        barrel(w, hx * 0.62, -hy - 0.07); crate(w, -hx * 0.75, -hy - 0.06, 0.045, 0.0, 0.2)
        # small porch roof
        w.box(tim, -0.0, -hy - 0.05, (0.20, 0.004, 0.0) if False else (0.20, 0.10, 0.012), 0.27)
        for sx in (-1, 1): w.box(tim, sx * 0.09, -hy - 0.09, (0.016, 0.016, 0.27), 0.0)
    return w.commit()

def woodpile(w, x, y, length, rows):
    bark = MT.bark(); end = MT.solid('endgrain', (0.55, 0.42, 0.26), 0.9)
    r = 0.016
    for j in range(rows):
        n = 8 - j
        for i in range(n):
            yy = y - length / 2 + (i + 0.5 + 0.5 * j) * (length / 8)
            w.cyl(bark, (x - 0.05, yy, r + j * r * 1.75), (x + 0.05, yy, r + j * r * 1.75), r * 0.95, r * 0.95, 8, capmat=end)

def farmhouse(ctr):
    w = W(ctr, 'farm')
    wx, wy, wh, rh = 0.82, 0.54, 0.38, 0.30
    hx, hy = wx / 2, wy / 2
    tim = MT.timber((0.25, 0.19, 0.14)); stone = MT.masonry('stone', False)
    pl = MT.plaster((0.84, 0.80, 0.70)); roof = MT.clay_tile()
    yard(w, 0.9, 0.8, name='yardf')
    fh = 0.06
    w.box(stone, 0, 0, (wx + 0.02, wy + 0.02, fh), 0)
    w.box(pl, 0, 0, (wx - 0.001, wy - 0.001, wh - fh), fh)
    for sx in (-1, 1):
        for sy in (-1, 1): w.box(tim, sx * (hx - 0.006), sy * (hy - 0.006), (0.028, 0.028, wh - fh), fh)
    for face, wall, L in (('y-', -hy, hx), ('y+', hy, hx), ('x+', hx, hy), ('x-', -hx, hy)):
        fb(w, tim, face, wall, 0, wh - 0.032, 2 * L, 0.032, 0.011); fb(w, tim, face, wall, 0, fh, 2 * L, 0.02, 0.011)
        n = int(L * 2 / 0.2)
        for k in range(1, n): fb(w, tim, face, wall, -L + 2 * L * k / n, fh, 0.02, wh - fh - 0.03, 0.009)
    w.gable(roof, pl, 0, 0, (wx, wy), wh, rh, 0.0, overhang=(0.05, 0.07), thick=0.018, mat_edge=tim)
    w.box(roof, 0, 0, (wx + 0.1, 0.035, 0.022), wh + rh - 0.008)
    zw = fh + (wh - fh) * 0.58
    door(w, 'y-', -hy, -hx * 0.45, dw=0.13, dh=0.24, z0=fh - 0.002)
    window(w, 'y-', -hy, -hx * 0.05, zw); window(w, 'y-', -hy, hx * 0.32, zw); window(w, 'y-', -hy, hx * 0.70, zw)
    for a in (-0.28, 0.0, 0.28): window(w, 'y+', hy, a, zw)
    window(w, 'x+', hx, 0, zw); window(w, 'x-', -hx, 0, zw)
    # hayloft opening in gable x+
    fb(w, MT.solid('hay', (0.05, 0.04, 0.03), 1), 'x+', hx, 0, wh + 0.07, 0.07, 0.09, 0.006)
    fb(w, tim, 'x+', hx, 0, wh + 0.16, 0.10, 0.012, 0.014)
    for face, wall, L in (('x+', hx, hy), ('x-', -hx, hy)):
        n, t = FACES[face]
        gp = lambda al, z, off=0.006: ((wall + n[0] * off), al, z)
        w.beam(tim, gp(0, wh), gp(0, wh + rh * 0.85), 0.018, 0.012); w.beam(tim, gp(-L, wh), gp(0, wh + rh), 0.016, 0.012); w.beam(tim, gp(L, wh), gp(0, wh + rh), 0.016, 0.012)
    brick = MT.brickwork()
    w.box(brick, -hx + 0.08, 0.0, (0.07, 0.08, rh + 0.14), wh - 0.04)
    w.box(MT.masonry('cap', True), -hx + 0.08, 0.0, (0.09, 0.10, 0.014), wh + rh + 0.10)
    # annex: open timber hay shelter on the +x end
    for dy in (-0.18, 0.18):
        for dx in (0.06, 0.26): w.box(tim, hx + dx, dy, (0.024, 0.024, 0.2), 0)
    w.face(MT.thatch(), [(hx + 0.0, -0.22, 0.22), (hx + 0.32, -0.22, 0.17), (hx + 0.32, 0.22, 0.17), (hx + 0.0, 0.22, 0.22)])
    w.box(MT.solid('hayb', (0.55, 0.46, 0.24), 1.0), hx + 0.16, 0.0, (0.2, 0.28, 0.07), 0.0)
    w.box(MT.solid('hayb2', (0.50, 0.42, 0.22), 1.0), hx + 0.17, 0.0, (0.16, 0.2, 0.06), 0.07)
    barrel(w, -hx * 0.7, -hy - 0.08)
    # fence stub
    for i in range(6): w.box(tim, -0.2 + i * 0.1, -hy - 0.2, (0.014, 0.014, 0.05), 0.0)
    w.beam(tim, (-0.2, -hy - 0.2, 0.04), (0.3, -hy - 0.2, 0.04), 0.01, 0.01)
    return w.commit()

def lumberjack(ctr):
    w = W(ctr, 'lumber')
    hx, hy = 0.22, 0.20
    bark = MT.bark(); end = MT.solid('endgrain', (0.56, 0.43, 0.27), 0.9)
    pl = MT.planks((0.33, 0.26, 0.19), True, 0.055, 'hutwood', 0.04)
    tim = MT.timber((0.24, 0.18, 0.13))
    yard(w, 0.82, 0.78, color=(0.34, 0.27, 0.19), name='yardl')
    # hut: x from -0.30..0.14, y -0.26..0.04 offset back-left
    cx, cy = -0.12, 0.14
    w.box(MT.masonry('stone', False), cx, cy, (0.42, 0.34, 0.04), 0)
    w.box(pl, cx, cy, (0.40, 0.32, 0.22), 0.04)
    for sx in (-1, 1):
        for sy in (-1, 1): w.box(tim, cx + sx * 0.195, cy + sy * 0.155, (0.024, 0.024, 0.22), 0.04)
    th = MT.thatch()
    w.gable(th, pl, cx, cy, (0.40, 0.32), 0.26, 0.20, 0.0, overhang=(0.05, 0.06), thick=0.025, mat_edge=th, mat_gable=pl)
    w.box(th, cx, cy, (0.5, 0.04, 0.025), 0.26 + 0.20 - 0.008)
    door(w, 'y-', cy - 0.16, cx - 0.06, dw=0.09, dh=0.17, z0=0.036)
    window(w, 'x+', cx + 0.2, 0.0 + cy, 0.17, ww=0.06, wh=0.07, shutters=False)
    w.box(MT.brickwork(), cx - 0.14, cy + 0.04, (0.05, 0.05, 0.30), 0.26)
    # log pile (stack of logs along y) at front right
    logs = []
    for j in range(4):
        n = 6 - j
        for i in range(n):
            xx = 0.22 + 0.0; yy = -0.16 + (i + 0.5 * j) * 0.058
            w.cyl(bark, (xx - 0.17, yy, 0.026 + j * 0.05), (xx + 0.17 + (0.0), yy, 0.026 + j * 0.05), 0.027, 0.027, 9, capmat=end)
    # felled trunk with branches, chopping block + axe, sawhorse
    w.cyl(bark, (-0.30, -0.34, 0.04), (0.10, -0.26, 0.035), 0.04, 0.034, 10, capmat=end)
    w.cyl(bark, (0.23, 0.0, 0.0), (0.23, 0.0, 0.07), 0.05, 0.048, 12, capmat=end)
    w.box(MT.iron(), 0.20, 0.0, (0.01, 0.07, 0.05), 0.06) if False else None
    w.beam(MT.timber(), (0.23, 0.0, 0.07), (0.24, -0.09, 0.15), 0.01, 0.01)
    w.box(MT.iron(), 0.24, -0.105, (0.012, 0.03, 0.035), 0.12)
    # split logs on the ground
    for k in range(5):
        a = k * 1.3; w.cyl(bark, (0.05 + 0.04 * math.cos(a), 0.26 + 0.03 * math.sin(a), 0.012), (0.05 + 0.04 * math.cos(a) + 0.07 * math.cos(a + 1), 0.26 + 0.03 * math.sin(a) + 0.07 * math.sin(a + 1), 0.012), 0.012, 0.012, 7, capmat=end)
    return w.commit()

def chapel(ctr):
    w = W(ctr, 'chapel')
    st = MT.masonry('chapel', False, big=True); stone_d = MT.masonry('stone', False); tim = MT.timber((0.26, 0.20, 0.15))
    roof = MT.slate_shingle('shingle', (0.38, 0.36, 0.34)); pl = MT.plaster((0.80, 0.77, 0.69))
    yard(w, 1.35, 1.25, color=(0.40, 0.36, 0.28), name='yardc', inner=0.62)
    # nave: along X, centred slightly
    nx, ny, nh, rh = 1.05, 0.62, 0.50, 0.40
    cx, cy = -0.12, 0.10
    w.box(stone_d, cx, cy, (nx + 0.03, ny + 0.03, 0.07), 0)
    w.box(st, cx, cy, (nx, ny, nh - 0.07), 0.07)
    w.gable(roof, st, cx, cy, (nx, ny), nh, rh, 0.0, overhang=(0.045, 0.06), thick=0.02, mat_edge=tim, mat_gable=st)
    w.box(roof, cx, cy, (nx + 0.1, 0.04, 0.025), nh + rh - 0.01)
    # buttresses on the long side
    hx, hy = nx / 2, ny / 2
    for a in (-0.38, -0.13, 0.12, 0.37):
        for sg in (-1, 1):
            yy = cy + sg * (hy + 0.025)
            w.box(st, cx + a, yy, (0.06, 0.05, 0.30), 0)
            w.face(st, [(cx + a - 0.03, yy + sg * (-0.025), 0.30), (cx + a + 0.03, yy + sg * (-0.025), 0.30), (cx + a + 0.03, yy + sg * 0.025, 0.28), (cx + a - 0.03, yy + sg * 0.025, 0.28)] if sg < 0 else [(cx + a + 0.03, yy - 0.025, 0.30), (cx + a - 0.03, yy - 0.025, 0.30), (cx + a - 0.03, yy + 0.025, 0.28), (cx + a + 0.03, yy + 0.025, 0.28)])
    # arched windows: tall dark glass w/ stone surround
    glass = MT.glass('chapelglass', 0.0)
    def arch_window(face, wall, along, z0, ww=0.075, wh=0.17):
        fb(w, MT.masonry('sill', True), face, wall, along, z0 - 0.01, ww + 0.036, wh + 0.03, 0.012)
        fb(w, glass, face, wall, along, z0, ww, wh, 0.016, 0.0)
        fb(w, MT.masonry('sill', True), face, wall, along, z0 + wh * 0.5, 0.01, wh * 0.5 + 0.03, 0.02)
        fb(w, MT.masonry('sill', True), face, wall, along, z0 + wh * 0.5 - 0.005, ww, 0.01, 0.02)
        fb(w, glass, face, wall, along, z0 + wh, ww * 0.7, 0.03, 0.016, 0.0)
        fb(w, MT.masonry('sill', True), face, wall, along, z0 + wh + 0.028, ww * 0.9, 0.014, 0.022)
    for a in (-0.255, 0.0, 0.255):
        arch_window('y-', cy - hy, cx + a, 0.17)
        arch_window('y+', cy + hy, cx + a, 0.17)
    # west facade (x-) door: heavy door with stone surround; east (x+) rose window
    # bell tower at the west (x-) end
    tx, ty = cx + hx + 0.06, cy
    tw = 0.34; th_ = 0.74
    w.box(stone_d, tx + 0.02, ty, (tw + 0.03, tw + 0.03, 0.07), 0)
    w.box(st, tx + 0.02, ty, (tw, tw, th_ - 0.07), 0.07)
    # tower string course + belfry openings
    w.box(MT.masonry('sill', True), tx + 0.02, ty, (tw + 0.02, tw + 0.02, 0.014), th_ - 0.01)
    bz = th_ + 0.0
    w.box(MT.masonry('chapel', True), tx + 0.02, ty, (tw - 0.02, tw - 0.02, 0.14), bz)
    for face, wall in (('x+', tx + 0.02 + (tw - 0.02) / 2), ('x-', tx + 0.02 - (tw - 0.02) / 2)):
        fb(w, glass, face, wall, ty, bz + 0.035, 0.06, 0.09, 0.006, 0.0)
        fb(w, MT.masonry('sill', True), face, wall, ty, bz + 0.12, 0.07, 0.014, 0.016)
    for face, wall in (('y-', ty - (tw - 0.02) / 2), ('y+', ty + (tw - 0.02) / 2)):
        fb(w, glass, face, wall, tx + 0.02, bz + 0.035, 0.06, 0.09, 0.006, 0.0)
        fb(w, MT.masonry('sill', True), face, wall, tx + 0.02, bz + 0.12, 0.07, 0.014, 0.016)
    # clock-less tower window slit on the lower tower
    for face, wall in (('y-', ty - tw / 2), ('x+', tx + 0.02 + tw / 2)):
        fb(w, glass, face, wall, tx + 0.02 if face[0] == 'y' else ty, 0.3, 0.03, 0.10, 0.006, 0.0)
    door(w, 'y-', ty - tw / 2, tx + 0.02, dw=0.14, dh=0.27, mat=MT.planks((0.22, 0.15, 0.10), True, 0.035, 'chdoor'), frame=MT.masonry('sill', True), z0=0.06)
    # spire: 4-sided pyramid with shingles
    sb = bz + 0.14; sp = 0.50
    hw = (tw - 0.02) / 2 + 0.02
    A = [(tx + 0.02 - hw, ty - hw), (tx + 0.02 + hw, ty - hw), (tx + 0.02 + hw, ty + hw), (tx + 0.02 - hw, ty + hw)]
    apex = (tx + 0.02, ty, sb + sp)
    sh = MT.slate_shingle('shingle', (0.38, 0.36, 0.34))
    for i in range(4):
        a0 = A[i]; a1 = A[(i + 1) % 4]
        w.face(sh, [(a0[0], a0[1], sb), (a1[0], a1[1], sb), apex])
    w.box(MT.iron(), tx + 0.02, ty, (0.012, 0.012, 0.07), sb + sp - 0.01)
    w.beam(MT.iron(), (tx + 0.02 - 0.03, ty, sb + sp + 0.045), (tx + 0.02 + 0.03, ty, sb + sp + 0.045), 0.006, 0.006)
    # porch / low annex on y+ side (vestry)
    w.box(stone_d, cx + 0.28, cy + hy + 0.14, (0.30, 0.24, 0.05), 0)
    w.box(st, cx + 0.28, cy + hy + 0.14, (0.28, 0.22, 0.22), 0.05)
    w.face(roof, [(cx + 0.28 - 0.17, cy + hy + 0.14 - 0.14, 0.27), (cx + 0.28 + 0.17, cy + hy + 0.14 - 0.14, 0.27), (cx + 0.28 + 0.17, cy + hy + 0.14 + 0.15, 0.20), (cx + 0.28 - 0.17, cy + hy + 0.14 + 0.15, 0.20)])
    # gravestones / bench
    for i, (gx, gy) in enumerate([(0.42, -0.42), (0.52, -0.30), (0.34, -0.55), (0.60, -0.50)]):
        w.box(MT.masonry('grave', True), gx, gy, (0.03, 0.012, 0.045 + 0.01 * (i % 2)), 0, 0.15 * i)
    return w.commit()

def warehouse(ctr):
    w = W(ctr, 'warehouse')
    tim = MT.timber((0.24, 0.18, 0.13)); st = MT.masonry('stone', False); roof = MT.clay_tile()
    pl = MT.plaster((0.78, 0.72, 0.60))
    board = MT.planks((0.34, 0.27, 0.19), True, 0.05, 'whboards', 0.04)
    yard(w, 1.38, 1.30, color=(0.34, 0.28, 0.20), name='yardw', inner=0.6)
    nx, ny, nh, rh = 1.16, 0.80, 0.52, 0.44
    cx, cy = 0.0, -0.05
    hx, hy = nx / 2, ny / 2
    w.box(st, cx, cy, (nx + 0.03, ny + 0.03, 0.18), 0)           # stone ground course
    w.box(board, cx, cy, (nx, ny, nh - 0.18), 0.18, mats=None)
    for sx in (-1, 1):
        for sy in (-1, 1): w.box(tim, cx + sx * (hx - 0.008), cy + sy * (hy - 0.008), (0.04, 0.04, nh - 0.18), 0.18)
    for face, wall, L in (('y-', cy - hy, hx), ('y+', cy + hy, hx), ('x+', cx + hx, hy), ('x-', cx - hx, hy)):
        fb(w, tim, face, wall - (0 if face[0] == 'y' else 0), (cx if face[0] == 'y' else cy), nh - 0.04, 2 * L, 0.04, 0.012)
        fb(w, tim, face, wall, (cx if face[0] == 'y' else cy), 0.18, 2 * L, 0.025, 0.012)
        n = int(2 * L / 0.26)
        for k in range(1, n): fb(w, tim, face, wall, (cx if face[0] == 'y' else cy) - L + 2 * L * k / n, 0.18, 0.03, nh - 0.22, 0.010)
    w.gable(roof, board, cx, cy, (nx, ny), nh, rh, 0.0, overhang=(0.05, 0.075), thick=0.02, mat_edge=tim, mat_gable=board)
    w.box(roof, cx, cy, (nx + 0.12, 0.04, 0.025), nh + rh - 0.01)
    # big double doors on y- (lit side) and loading door on x+
    big = MT.planks((0.26, 0.19, 0.13), True, 0.035, 'wdoor')
    for dx in (-0.22, 0.22):
        fb(w, MT.solid('dh', (0.02, 0.015, 0.01), 1.0), 'y-', cy - hy, cx + dx, 0.18, 0.2, 0.30, 0.004)
    fb(w, big, 'y-', cy - hy, cx - 0.105, 0.185, 0.2, 0.29, 0.012); fb(w, big, 'y-', cy - hy, cx + 0.105 + 0.0, 0.185, 0.2, 0.29, 0.012)
    fb(w, tim, 'y-', cy - hy, cx, 0.18, 0.43, 0.025, 0.02); fb(w, tim, 'y-', cy - hy, cx - 0.225, 0.18, 0.03, 0.33, 0.02); fb(w, tim, 'y-', cy - hy, cx + 0.225, 0.18, 0.03, 0.33, 0.02)
    fb(w, tim, 'y-', cy - hy, cx, 0.50, 0.50, 0.03, 0.02)
    for a in (-0.15, 0.15):
        fb(w, MT.iron(), 'y-', cy - hy, cx + a, 0.30, 0.012, 0.012, 0.02, 0.012) 
    # stone ramp
    w.box(st, cx, cy - hy - 0.08, (0.55, 0.14, 0.04), 0)
    # hoist beam and loading hatch in the gable (y- gable? ridge along X so gables are x+/x-); put hatch on x+ gable
    fb(w, MT.solid('hatch', (0.03, 0.025, 0.02), 1.0), 'x+', cx + hx, cy, nh + 0.08, 0.12, 0.14, 0.006)
    fb(w, big, 'x+', cx + hx, cy - 0.03, nh + 0.085, 0.055, 0.13, 0.01); fb(w, big, 'x+', cx + hx, cy + 0.03, nh + 0.085, 0.055, 0.13, 0.01)
    # hoist beam protruding
    w.beam(tim, (cx + hx - 0.02, cy, nh + rh * 0.55), (cx + hx + 0.28, cy, nh + rh * 0.55), 0.03, 0.03)
    w.beam(tim, (cx + hx, cy, nh + rh * 0.2), (cx + hx + 0.2, cy, nh + rh * 0.52), 0.016, 0.016)
    w.cyl(MT.rope(), (cx + hx + 0.26, cy, nh + rh * 0.55 - 0.01), (cx + hx + 0.26, cy, nh + rh * 0.55 - 0.20), 0.004, 0.004, 6)
    w.box(MT.iron(), cx + hx + 0.26, cy, (0.016, 0.01, 0.025), nh + rh * 0.55 - 0.23)
    # windows: small barred ones
    for face, wall, along in (('y-', cy - hy, cx - 0.42), ('y-', cy - hy, cx + 0.42), ('y+', cy + hy, cx - 0.3), ('y+', cy + hy, cx + 0.3), ('x-', cx - hx, cy)):
        window(w, face, wall, along, 0.34, ww=0.07, wh=0.075, shutters=True, shut=MT.painted('whshut', (0.34, 0.24, 0.17)))
    # attic vent windows on roof (dormer) y- side
    dx = cx + 0.25
    w.box(board, dx, cy - 0.17, (0.17, 0.14, 0.14), nh + 0.06)
    w.face(roof, [(dx - 0.105, cy - 0.255, nh + 0.215), (dx + 0.105, cy - 0.255, nh + 0.215), (dx + 0.105, cy - 0.10, nh + 0.285), (dx - 0.105, cy - 0.10, nh + 0.285)])
    fb(w, MT.glass('glass'), 'y-', cy - 0.24, dx, nh + 0.09, 0.07, 0.07, 0.008)
    # stock outside: barrels, crates, sacks, stacked planks
    for i, (bx, by) in enumerate([(cx - 0.5, cy - hy - 0.12), (cx - 0.43, cy - hy - 0.08), (cx - 0.54, cy - hy - 0.2), (cx + 0.5, cy - hy - 0.11)]):
        barrel(w, bx, by, r=0.03, h=0.065)
    for i, (bx, by, s_, z_) in enumerate([(cx + 0.62, cy - hy - 0.2, 0.06, 0.0), (cx + 0.69, cy - hy - 0.17, 0.05, 0.0), (cx + 0.63, cy - hy - 0.19, 0.045, 0.052)]):
        crate(w, bx, by, s_, z_, 0.2 * i)
    sack = MT.solid('sack', (0.55, 0.47, 0.34), 0.95)
    for i in range(4): w.sphere(sack, (cx + 0.72 + 0.04 * (i % 2), cy + 0.08 + 0.06 * (i // 2) - 0.0, 0.02 + 0.03 * (i // 3)), 0.026, scale=(1, 1.3, 0.75), seg=8, rings=6)
    for i in range(5): w.box(MT.planks((0.50, 0.40, 0.28), False, 0.02, 'lumberpile'), cx + hx + 0.2, cy + 0.34, (0.34, 0.1, 0.012), 0.012 * i + 0.0, 0.0)
    return w.commit()

def windmill(ctr):
    w = W(ctr, 'windmill')
    st = MT.masonry('mill', True); tim = MT.timber((0.22, 0.17, 0.12))
    yard(w, 0.85, 0.8, color=(0.40, 0.33, 0.24), name='yardm')
    n = 8; h0 = 0.62; rb = 0.27; rt = 0.17
    base = MT.masonry('stone', False)
    plast = MT.plaster((0.82, 0.78, 0.68), 0.14)
    # tapered octagonal tower as 8 faces
    def ring(r, z, k):
        a = 2 * math.pi * (k + 0.5) / n
        return (r * math.cos(a), r * math.sin(a), z)
    w.cyl(base, (0, 0, 0), (0, 0, 0.10), rb + 0.03, rb + 0.02, n, cap0=False, cap1=False)
    for k in range(n):
        w.face(plast, [ring(rb, 0.10, k), ring(rb, 0.10, k + 1), ring(rt, h0, k + 1), ring(rt, h0, k)][::1])
    # timber battens corner posts
    for k in range(n):
        w.beam(tim, ring(rb + 0.003, 0.10, k), ring(rt + 0.003, h0, k), 0.018, 0.018)
    w.cyl(tim, (0, 0, h0 - 0.012), (0, 0, h0 + 0.01), rt + 0.014, rt + 0.014, n, cap0=False)
    # door, windows
    ang = -math.pi / 2     # facing -y (lit side)
    w.box(MT.planks((0.24, 0.17, 0.12), True, 0.03, 'mdoor'), 0, -(rb - 0.016 * 0 + 0.0) * math.cos(math.pi / n) + 0.035, (0.11, 0.012, 0.20), 0.10)
    w.box(tim, 0, -(rb) * math.cos(math.pi / n) + 0.03, (0.14, 0.016, 0.02), 0.30)
    for k, zz in ((1, 0.42), (3, 0.40), (5, 0.38)):
        a = 2 * math.pi * (k + 0.5) / n + 0.0
        rr = (rb + (rt - rb) * (zz - 0.10) / (h0 - 0.10)) * math.cos(math.pi / n)
        w.box(MT.glass('glass'), rr * math.cos(2 * math.pi * (k + 0.0) / n + math.pi / n), rr * math.sin(2 * math.pi * k / n + math.pi / n), (0.02, 0.02, 0.06), zz, rot=2 * math.pi * k / n + math.pi / n) if False else None
    # cap: conical thatched/shingled dome
    cap = MT.slate_shingle('shingle', (0.26, 0.22, 0.19))
    tl = 12
    zc = h0
    for k in range(tl):
        a0 = 2 * math.pi * k / tl; a1 = 2 * math.pi * (k + 1) / tl
        w.face(cap, [(0.215 * math.cos(a0), 0.215 * math.sin(a0), zc), (0.215 * math.cos(a1), 0.215 * math.sin(a1), zc),
                     (0.03 * math.cos(a1), 0.03 * math.sin(a1), zc + 0.20), (0.03 * math.cos(a0), 0.03 * math.sin(a0), zc + 0.20)])
        w.face(cap, [(0.03 * math.cos(a0), 0.03 * math.sin(a0), zc + 0.20), (0.03 * math.cos(a1), 0.03 * math.sin(a1), zc + 0.20), (0, 0, zc + 0.215)])
    # sails: hub on a shaft pointing toward the viewer (+x,-y diagonal): axis d
    d = Vector((1, -1, 0)).normalized()
    side = Vector((1, 1, 0)).normalized()
    hub = Vector((0, 0, zc + 0.08)) + d * 0.24
    w.cyl(MT.iron(), tuple(Vector((0, 0, zc + 0.08)) + d * 0.05), tuple(hub + d * 0.04), 0.02, 0.025, 8)
    w.sphere(tim, tuple(hub + d * 0.05), 0.03, seg=8, rings=5)
    L = 0.62
    cl = MT.cloth('millsail', (0.80, 0.74, 0.60), 0.07, 0.3)
    for i in range(4):
        th = math.radians(22 + 90 * i)
        u = side * math.cos(th) + Vector((0, 0, 1)) * math.sin(th)      # blade direction in the sail plane
        pv = d.cross(u)                                                  # chordwise
        pv = (side * 0 + Vector((0, 0, 1)).cross(d)) if False else pv.normalized()
        p0 = hub + d * 0.05
        stock0 = p0 + u * 0.04; stock1 = p0 + u * L
        # whip (stock) and lattice frame
        wp = lambda v: tuple(v)
        w.beam(tim, wp(stock0), wp(stock1), 0.016, 0.016, up=tuple(d))
        off = pv * 0.012
        for sgn in (1, -1):
            pass
        # sail frame: panel to one side of the stock
        c1 = p0 + u * 0.16 + pv * 0.015; c2 = p0 + u * L + pv * 0.015
        c3 = p0 + u * L + pv * 0.115; c4 = p0 + u * 0.16 + pv * 0.115
        w.beam(tim, wp(c1), wp(c2), 0.008, 0.008); w.beam(tim, wp(c4), wp(c3), 0.012, 0.012); w.beam(tim, wp(c2), wp(c3), 0.01, 0.01); w.beam(tim, wp(c1), wp(c4), 0.01, 0.01)
        for k in range(1, 8):
            a = p0 + u * (0.16 + (L - 0.16) * k / 8) + pv * 0.015; b = a + pv * 0.10
            w.beam(tim, wp(a), wp(b), 0.005, 0.005)
        w.face(cl, [wp(c1 + d * 0.003), wp(c2 + d * 0.003), wp(c3 + d * 0.003), wp(c4 + d * 0.003)])
        w.face(cl, [wp(c4 - d * 0.003), wp(c3 - d * 0.003), wp(c2 - d * 0.003), wp(c1 - d * 0.003)])
    # balcony / gallery ring
    w.cyl(tim, (0, 0, 0.30), (0, 0, 0.312), 0.3, 0.3, 8, cap0=True, cap1=True)
    return w.commit()
