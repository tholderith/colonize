"""Nature + ship + props: trees, rocks, wheat, pier, ship, cart, colonists."""
from wb import *
import mats as MT
import random
from mathutils import noise as mnoise

def tree(ctr, v):
    rng = random.Random(7 + v * 31)
    w = W(ctr, f'tree{v}')
    P = [dict(th=0.34, cz=0.74, rx=0.40, rz=0.36, n=120, cr=(0.065, 0.115), dark=(0.10, 0.20, 0.06), light=(0.40, 0.52, 0.16), yel=0.15, bark=(0.20, 0.16, 0.12)),
         dict(th=0.30, cz=0.66, rx=0.36, rz=0.30, n=100, cr=(0.06, 0.105), dark=(0.12, 0.22, 0.07), light=(0.46, 0.55, 0.17), yel=0.45, bark=(0.24, 0.19, 0.14)),
         dict(th=0.28, cz=0.82, rx=0.24, rz=0.52, n=110, cr=(0.055, 0.10), dark=(0.09, 0.19, 0.07), light=(0.36, 0.50, 0.18), yel=0.1, bark=(0.30, 0.27, 0.22)),
         None][v]
    if v == 3: return conifer(w, rng)
    bk = MT.bark(P['bark']); fol = MT.foliage('oak%d' % v, P['dark'], P['light'], P['yel'])
    th = P['th']
    # trunk (flared, leaning slightly) + limbs
    lean = (rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03))
    w.cyl(bk, (0, 0, -0.01), (lean[0], lean[1], th * 0.5), 0.05, 0.032, 9, cap0=False)
    w.cyl(bk, (lean[0], lean[1], th * 0.5), (lean[0] * 1.5, lean[1] * 1.5, th + 0.12), 0.032, 0.02, 9)
    for i in range(7):    # roots
        a = i * 2 * math.pi / 7 + rng.uniform(-0.3, 0.3)
        w.cyl(bk, (0.02 * math.cos(a), 0.02 * math.sin(a), 0.03), (0.075 * math.cos(a), 0.075 * math.sin(a), -0.005), 0.016, 0.006, 5, cap0=False, cap1=False)
    top = (lean[0] * 1.5, lean[1] * 1.5, th + 0.1)
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.15, 0.3)
        w.cyl(bk, top, (top[0] + r * math.cos(a), top[1] + r * math.sin(a), P['cz'] + rng.uniform(-0.1, 0.05)), 0.016, 0.006, 6)
    # canopy: big base masses + many small leaf clumps on the shell (ragged, leafy silhouette)
    placed = 0
    def inside(): 
        while True:
            x, y, z = rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)
            d = x * x + y * y + z * z
            if d <= 1 and d >= 0.05: return x, y, z, d
    while placed < 55:
        x, y, z, d = inside()
        if z < -0.5 and d < 0.8: continue
        w.sphere(fol, (x * P['rx'] * 0.78 + lean[0] * 1.5, y * P['rx'] * 0.78 + lean[1] * 1.5, P['cz'] + z * P['rz'] * 0.78), rng.uniform(0.09, 0.13), seg=8, rings=5, scale=(1, 1, 0.8), rot=rng.uniform(0, 3), jitter=0.06, rng=rng)
        placed += 1
    placed = 0
    while placed < 520:
        x, y, z, d = inside()
        if d < 0.45: continue
        if z < -0.45 and d < 0.85: continue
        s_ = (1.0 / math.sqrt(d)) * rng.uniform(0.80, 1.0)
        px, py, pz = x * s_ * P['rx'] + lean[0] * 1.5, y * s_ * P['rx'] + lean[1] * 1.5, P['cz'] + z * s_ * P['rz']
        crad = rng.uniform(0.032, 0.058)
        w.sphere(fol, (px, py, pz), crad, seg=6, rings=4, scale=(1.0, 1.0, 0.75), rot=rng.uniform(0, 3), jitter=0.12, rng=rng)
        placed += 1
    yard(w, 0.30, 0.30, color=(0.20, 0.16, 0.10), name='treeyard', inner=0.2)
    # dark underside fill
    return w.commit()

def conifer(w, rng):
    bk = MT.bark((0.24, 0.17, 0.12)); fol = MT.foliage('pine', (0.04, 0.12, 0.08), (0.20, 0.36, 0.18), 0.0)
    w.cyl(bk, (0, 0, -0.01), (0, 0, 0.9), 0.035, 0.012, 8, cap0=False)
    tiers = 13
    for t in range(tiers):
        f = t / (tiers - 1)
        z = 0.20 + f * 0.95
        R = 0.36 * (1 - f) ** 0.9 + 0.05
        n = int(7 + 14 * (1 - f))
        for k in range(n):
            a = 2 * math.pi * k / n + t * 0.7 + rng.uniform(-0.2, 0.2)
            rr = R * rng.uniform(0.55, 1.0)
            cr = 0.058 * (1 - f * 0.5) + 0.017
            w.sphere(fol, (rr * math.cos(a), rr * math.sin(a), z + rng.uniform(-0.03, 0.03) - 0.1 * rr), cr, seg=7, rings=4, scale=(1.5, 1.5, 0.5), rot=a, jitter=0.1, rng=rng)
        w.sphere(fol, (0, 0, z), R * 0.45 + 0.03, seg=7, rings=4, scale=(1, 1, 0.7), jitter=0.15, rng=rng)
    w.sphere(fol, (0, 0, 1.17), 0.045, seg=6, rings=4, scale=(1, 1, 2.2))
    return w.commit()

def _noise_rock(seed, r, sq, nz=0.45):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
    off = Vector((seed * 5.3, seed * 2.1, seed * 3.7))
    for vtx in bm.verts:
        p = vtx.co.copy()
        d = mnoise.fractal(p * 3.2 + off, 1.0, 2.0, 4) * nz + mnoise.noise(p * 9 + off) * 0.06
        vtx.co = p * (1 + d)
        vtx.co.z *= sq
    for vtx in bm.verts:
        if vtx.co.z < 0.0: vtx.co.z = vtx.co.z * 0.2
    return bm

def rock(ctr, v):
    rng = random.Random(40 + v)
    w = W(ctr, f'rock{v}')
    me = bpy.data.meshes.new('rock'); bm = bmesh.new()
    specs = [((0, 0, 0), 0.20, 0.62, 1), ((0.17, 0.07, 0), 0.11, 0.7, 2), ((-0.14, 0.11, 0), 0.09, 0.8, 3)] if v == 0 else [((0, 0, 0), 0.17, 0.72, 5), ((-0.15, -0.09, 0), 0.12, 0.6, 6), ((0.14, 0.1, 0), 0.08, 0.9, 7), ((0.05, -0.17, 0), 0.06, 0.8, 8)]
    for (c, r, sq, sd) in specs:
        b2 = _noise_rock(sd, r, sq)
        for f in b2.faces:
            vs = [bm.verts.new(vv.co + Vector((w.cx + c[0], w.cy + c[1], 0.01))) for vv in f.verts]
            try: bm.faces.new(vs)
            except ValueError: pass
        b2.free()
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    mb = MB('rockmat%d' % v); co = mb.coord('Object'); nrm = mb.coord('Normal')
    n1 = mb.noise(co, 12, 5, 0.6, 0.3); n2 = mb.noise(co, 60, 4)
    col = mb.mix(mb.fmap(n1, 0.3, 0.7), (0.30, 0.29, 0.27), (0.55, 0.52, 0.47))
    col = mb.mix(mb.fmap(n2, 0.3, 0.7, 0, 0.35), col, (0.20, 0.19, 0.17))
    nz = mb.sepz(nrm)['Z']
    top = mb.math('MULTIPLY', mb.fmap(nz, 0.5, 0.9, 0, 1), mb.fmap(mb.noise(co, 14, 4), 0.4, 0.65))
    col = mb.mix(mb.math('MULTIPLY', top, 0.85), col, (0.30, 0.36, 0.17))
    lich = mb.fmap(mb.noise(co, 30, 3), 0.62, 0.75, 0, 0.7)
    col = mb.mix(lich, col, (0.62, 0.62, 0.45))
    bump = mb.bump(mb.math('ADD', n1, n2), 1.0, 0.012)
    mb.done(col, 0.88, bump)
    me.materials.append(mb.m)
    o = bpy.data.objects.new('rock', me); bpy.context.collection.objects.link(o)
    yard(w, 0.5, 0.5, color=(0.30, 0.27, 0.20), name='rockyard', inner=0.35)
    return [o]

def wheat(ctr):
    w = W(ctr, 'wheat')
    rng = random.Random(5)
    # soil
    soil = MB('soil'); co = soil.coord('Object'); g = soil.coord('Generated')
    sub = soil.n('VectorMath', operation='SUBTRACT'); soil.link(g, sub.inputs[0]); sub.inputs[1].default_value = (0.5, 0.5, 0)
    ab = soil.n('VectorMath', operation='ABSOLUTE'); soil.link(sub.outputs[0], ab.inputs[0])
    sp = soil.n('SeparateXYZ'); soil.link(ab.outputs[0], sp.inputs[0])
    m = soil.math('MAXIMUM', sp.outputs['X'], sp.outputs['Y'])
    nzz = soil.noise(co, 7, 4, 0.55, 0.2)
    m2 = soil.math('ADD', m, soil.math('MULTIPLY', soil.math('SUBTRACT', nzz, 0.5), 0.07))
    alpha = soil.fmap(m2, 0.5, 0.435, 0.0, 1.0)
    rows = soil.noise(soil.mapping(co, (60, 12, 1)), 1, 2, 0.5)
    scol = soil.mix(soil.fmap(soil.noise(co, 30, 4), 0.3, 0.7), (0.20, 0.14, 0.09), (0.36, 0.26, 0.17))
    soil.bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
    soil.link(scol, soil.bsdf.inputs['Base Color']); soil.set('Roughness', 0.97)
    soil.link(soil.bump(soil.math('ADD', rows, soil.noise(co, 80, 3)), 0.8, 0.01), soil.bsdf.inputs['Normal'])
    tr = soil.n('BsdfTransparent'); mx = soil.n('MixShader'); soil.link(alpha, mx.inputs['Fac'])
    soil.nt.links.new(tr.outputs[0], mx.inputs[1]); soil.nt.links.new(soil.bsdf.outputs[0], mx.inputs[2]); soil.nt.links.new(mx.outputs[0], soil.out.inputs[0])
    me = bpy.data.meshes.new('soil'); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    h = 1.0
    f = bm.faces.new([bm.verts.new((w.cx + sx * h, w.cy + sy * h, 0.0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bm.to_mesh(me); bm.free(); me.materials.append(soil.m)
    o = bpy.data.objects.new('soil', me); bpy.context.collection.objects.link(o)
    # wheat stalks
    stalk = MT.solid('stalk', (0.55, 0.44, 0.17), 0.8)
    ear = MB('ear'); ear.bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
    eco = ear.coord('Object')
    ecol = ear.mix(ear.fmap(ear.noise(eco, 9, 3), 0.3, 0.7), (0.60, 0.46, 0.17), (0.80, 0.64, 0.28))
    ecol = ear.mix(ear.fmap(ear.noise(eco, 3, 2, 0.5, 0.2), 0.55, 0.75, 0, 0.8), ecol, (0.42, 0.48, 0.17))
    ear.link(ecol, ear.bsdf.inputs['Base Color']); ear.set('Roughness', 0.75)
    nrow = 20; hs = 0.88
    for r in range(nrow):
        y = -hs + (r + 0.5) * 2 * hs / nrow + rng.uniform(-0.006, 0.006)
        nt_ = 60
        for k in range(nt_):
            x = -hs + (k + rng.random()) * 2 * hs / nt_
            # irregular edges
            ed = max(abs(x), abs(y)) / hs
            if ed > 0.9 and rng.random() < (ed - 0.9) * 8: continue
            for j in range(2):
                hgt = rng.uniform(0.085, 0.125)
                tx, ty = rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03)
                bx, by = x + rng.uniform(-0.01, 0.01), y + rng.uniform(-0.012, 0.012)
                w.cyl(stalk, (bx, by, 0.0), (bx + tx, by + ty, hgt), 0.004, 0.0025, 4, cap0=False, cap1=False, smooth=False)
                w.cyl(ear.m, (bx + tx, by + ty, hgt - 0.012), (bx + tx * 1.25, by + ty * 1.25, hgt + 0.032), 0.0075, 0.0015, 5, cap0=False, cap1=False, smooth=False)
    return w.commit() + [o]

def pier(ctr):
    w = W(ctr, 'pier')
    wood = MT.planks((0.36, 0.29, 0.21), False, 0.05, 'deck', 0.05)
    pile = MT.timber((0.22, 0.17, 0.12), 'pile')
    beam = MT.timber((0.28, 0.21, 0.15))
    zd = 0.085
    L0, L1 = -0.60, 0.95
    hw = 0.17
    # deck planks across (Y) laid along x
    n = int((L1 - L0) / 0.055)
    for i in range(n):
        x = L0 + (i + 0.5) * (L1 - L0) / n
        w.box(MT.planks((0.33 + 0.05 * ((i * 7) % 5) / 5, 0.26, 0.19), True, 0.05, 'pl%d' % (i % 4), 0.04), x, 0.0, ((L1 - L0) / n - 0.004, 2 * hw, 0.016), zd)
    for sy in (-1, 1):
        w.box(beam, (L0 + L1) / 2, sy * (hw - 0.012), (L1 - L0, 0.026, 0.03), zd - 0.028)
    for i in range(6):
        x = L0 + 0.06 + i * (L1 - L0 - 0.12) / 5
        for sy in (-1, 1):
            w.cyl(pile, (x, sy * (hw - 0.012), -0.03), (x, sy * (hw - 0.012), zd + 0.07 if i % 2 == 0 else zd + 0.02), 0.019, 0.017, 8, cap0=False)
    # cross bearers
    for i in range(0, 6):
        x = L0 + 0.06 + i * (L1 - L0 - 0.12) / 5
        w.box(beam, x, 0, (0.025, 2 * hw, 0.022), zd - 0.045)
    # coiled rope, bollards, a crate and barrels
    w.cyl(MT.iron(), (0.55, hw - 0.03, zd + 0.016), (0.55, hw - 0.03, zd + 0.05), 0.014, 0.012, 8)
    w.cyl(MT.iron(), (-0.30, -hw + 0.03, zd + 0.016), (-0.30, -hw + 0.03, zd + 0.05), 0.014, 0.012, 8)
    barrel(w, 0.05, -hw + 0.05, zd + 0.016, r=0.028, h=0.06); barrel(w, 0.12, -hw + 0.06, zd + 0.016, r=0.028, h=0.06)
    crate(w, -0.15, hw - 0.06, 0.06, zd + 0.016, 0.3)
    w.cyl(MT.rope(), (0.30, hw - 0.06, zd + 0.016), (0.30, hw - 0.06, zd + 0.03), 0.026, 0.026, 12)
    foam = MT.alpha_mat('pierfoam', (0.8, 0.85, 0.85), 40, strength=0.5)
    return w.commit()

# ------------------------------------------------------------------ ship
def ship(ctr):
    w = W(ctr, 'ship')
    L = 1.7; bmax = 0.235
    hull_m = M('hullmat', lambda: _hull_mat())
    deck_m = MT.planks((0.42, 0.33, 0.23), False, 0.022, 'shipdeck', 0.05)
    rail_m = MT.painted('rail', (0.30, 0.22, 0.14))
    tim = MT.timber((0.26, 0.19, 0.13)); mast_m = MT.timber((0.34, 0.25, 0.16), 'mast')
    rope = MT.rope()
    def Bp(t):
        if t < 0.42: f = 0.55 + 0.45 * (1 - ((0.42 - t) / 0.42) ** 2)
        else: f = max(0.0, 1 - ((t - 0.42) / 0.58) ** 2) ** 0.55
        return bmax * f
    def ztop(t): return 0.165 + 0.07 * max(0, (t - 0.55) / 0.45) ** 2 + 0.05 * max(0, (0.25 - t) / 0.25) ** 2
    NS, NV = 40, 6
    xs = [-L / 2 + L * i / NS for i in range(NS + 1)]
    ts = [i / NS for i in range(NS + 1)]
    def Y(i, v, sy):  # hull surface point
        t = ts[i]; B = Bp(t)
        return (xs[i], sy * B * (0.74 + 0.20 * (v ** 0.7) - 0.0), ztop(t) * v)
    for sy in (-1, 1):
        for i in range(NS):
            for j in range(NV):
                v0, v1 = j / NV, (j + 1) / NV
                pts = [Y(i, v0, sy), Y(i + 1, v0, sy), Y(i + 1, v1, sy), Y(i, v1, sy)]
                if sy > 0: pts = pts[::-1]
                if i == NS - 1:
                    pts = [pts[0], pts[1], pts[2]] if False else pts
                w.face(hull_m, pts, smooth=True)
    # transom
    A = [Y(0, 0, -1), Y(0, 0, 1), Y(0, 1, 1), Y(0, 1, -1)]
    w.face(hull_m, [A[0], A[3], A[2], A[1]])
    # deck + bulwarks
    zdk = lambda t: ztop(t) - 0.05
    for i in range(NS):
        t0, t1 = ts[i], ts[i + 1]
        yb0, yb1 = Bp(t0) * 0.93 - 0.012, Bp(t1) * 0.93 - 0.012
        w.face(deck_m, [(xs[i], -yb0, zdk(t0)), (xs[i + 1], -yb1, zdk(t1)), (xs[i + 1], yb1, zdk(t1)), (xs[i], yb0, zdk(t0))])
        for sy in (-1, 1):
            # inner bulwark face & top rail
            p0 = (xs[i], sy * yb0, zdk(t0)); p1 = (xs[i + 1], sy * yb1, zdk(t1)); p2 = (xs[i + 1], sy * yb1, ztop(t1)); p3 = (xs[i], sy * yb0, ztop(t0))
            w.face(rail_m, [p0, p1, p2, p3] if sy < 0 else [p3, p2, p1, p0])
            o0 = (xs[i], sy * (yb0 + 0.024), ztop(t0)); o1 = (xs[i + 1], sy * (yb1 + 0.024), ztop(t1))
            w.face(rail_m, [p3, p2, o1, o0] if sy > 0 else [o0, o1, p2, p3])
    # wale (thick plank band) along the side
    for sy in (-1, 1):
        for i in range(NS):
            a = Y(i, 0.50, sy); b = Y(i + 1, 0.50, sy); a2 = Y(i, 0.62, sy); b2 = Y(i + 1, 0.62, sy)
            ex = lambda p: (p[0], p[1] + (0.007 * sy), p[2])
            w.face(rail_m, [ex(a), ex(b), ex(b2), ex(a2)] if sy < 0 else [ex(a2), ex(b2), ex(b), ex(a)])
    # gun ports
    for sy in (-1, 1):
        for k in range(5):
            xx = -0.45 + k * 0.22
            i = int((xx + L / 2) / L * NS); t = ts[i]
            yy = sy * (Bp(t) * (0.74 + 0.2 * 0.55 ** 0.7) + 0.008)
            w.box(MT.solid('port', (0.03, 0.02, 0.015), 1.0), xx, yy, (0.05, 0.004, 0.04) if False else (0.045, 0.006, 0.035), ztop(t) * 0.44)
    # stern castle (poop) and forecastle
    sc_x0, sc_x1 = -0.84, -0.50
    zb = zdk(0.05)
    w.box(hull_m, (sc_x0 + sc_x1) / 2, 0, (sc_x1 - sc_x0, 0.30, 0.15), zb)
    w.box(rail_m, (sc_x0 + sc_x1) / 2, 0, (sc_x1 - sc_x0 + 0.02, 0.32, 0.012), zb + 0.15)
    # poop rail posts (visible side)
    for sy in (-1, 1):
        for k in range(8):
            w.box(rail_m, sc_x0 + 0.02 + k * 0.045, sy * 0.158, (0.008, 0.008, 0.045), zb + 0.162)
        w.box(rail_m, (sc_x0 + sc_x1) / 2, sy * 0.158, (sc_x1 - sc_x0, 0.008, 0.008), zb + 0.205)
    w.box(rail_m, sc_x0 + 0.005, 0, (0.008, 0.32, 0.008), zb + 0.205)
    # stern/side windows
    gl = MT.glass('shipglass', 0.0); gold = MT.solid('gilt', (0.55, 0.42, 0.18), 0.4, 0.6)
    for k in range(4):
        xx = sc_x0 + 0.055 + k * 0.075
        w.box(gold, xx, -0.153, (0.05, 0.006, 0.056), zb + 0.045)
        w.box(gl, xx, -0.157, (0.038, 0.004, 0.042), zb + 0.052)
    w.box(gold, sc_x0 + 0.01, 0, (0.004, 0.30, 0.012), zb + 0.12)
    # forecastle
    w.box(hull_m, 0.60, 0, (0.20, 0.17, 0.085), zdk(0.8))
    w.box(rail_m, 0.60, 0, (0.22, 0.19, 0.010), zdk(0.8) + 0.085)
    # bowsprit, figurehead stem
    w.cyl(mast_m, (0.74, 0, zdk(0.9) + 0.04), (1.12, 0, 0.36), 0.013, 0.007, 7)
    w.beam(hull_m, (L / 2 - 0.02, 0, 0.0), (L / 2 + 0.07, 0, 0.17), 0.016, 0.03)
    # capstan, hatch, mid-deck props
    zdm = zdk(0.45)
    w.box(tim, 0.12, 0, (0.14, 0.12, 0.012), zdm); w.box(MT.solid('hatchd', (0.05, 0.04, 0.03), 1.0), 0.12, 0, (0.11, 0.09, 0.006), zdm + 0.011)
    w.cyl(tim, (0.30, 0.0, zdm), (0.30, 0.0, zdm + 0.04), 0.022, 0.018, 8)
    # longboat on deck
    lb = MT.planks((0.36, 0.28, 0.20), False, 0.02, 'boat', 0.04)
    for k in range(10):
        t = k / 9; xx = -0.18 + 0.04 * k
        w.box(lb, xx - 0.0, -0.05 + 0 * t, (0.045, 0.07 * (1 - (2 * t - 1) ** 2 * 0.5), 0.024), zdm + 0.002) if False else None
    w.box(lb, -0.28, 0.07, (0.26, 0.075, 0.03), zdm)
    # masts
    mdefs = [(0.38, 1.02, 0.015), (-0.08, 1.30, 0.018), (-0.58, 0.88, 0.013)]
    zdeck = zdk(0.5)
    for mx, mh, mr in mdefs:
        w.cyl(mast_m, (mx, 0, zdeck - 0.02), (mx, 0, zdeck + mh), mr, mr * 0.45, 9)
        # top platform
        w.cyl(tim, (mx, 0, zdeck + mh * 0.50), (mx, 0, zdeck + mh * 0.50 + 0.01), 0.042, 0.042, 10)
        for sy in (-1, 1):   # shrouds
            for k in range(4):
                xx = mx - 0.045 + k * 0.03
                w.cyl(rope, (mx, sy * 0.015, zdeck + mh * 0.5), (xx, sy * (0.205), zdk(0.5) + 0.0), 0.0025, 0.0025, 4, cap0=False, cap1=False)
        w.sphere(tim, (mx, 0, zdeck + mh + 0.005), 0.013, seg=6, rings=4)
    # yards & sails
    sail = MT.cloth('shipsail', (0.86, 0.80, 0.67))
    def square_sail(mx, zy, zf, wh_, wf, bulge, furled=False, seed=0):
        yard = MT.timber((0.30, 0.22, 0.14), 'yard')
        w.cyl(yard, (mx, -wh_ / 2 - 0.02, zy), (mx, wh_ / 2 + 0.02, zy), 0.0085, 0.0085, 6)
        if furled:
            w.cyl(sail, (mx + 0.012, -wh_ / 2 + 0.01, zy + 0.012), (mx + 0.012, wh_ / 2 - 0.01, zy + 0.012), 0.016, 0.016, 8)
            return
        nu, nv = 10, 8
        for iu in range(nu):
            for iv in range(nv):
                def pt(a, b):
                    s = b / nv; u = a / nu
                    ww = wh_ + (wf - wh_) * s
                    xx = mx + 0.012 + bulge * math.sin(math.pi * u) * (math.sin(math.pi * (0.15 + 0.7 * s)) ** 1.0)
                    return (xx, (u - 0.5) * ww, zy + (zf - zy) * s - (0.012 * math.sin(math.pi * u)) * s)
                w.face(sail, [pt(iu, iv), pt(iu + 1, iv), pt(iu + 1, iv + 1), pt(iu, iv + 1)][::-1], smooth=True)
        # bolt rope / foot
        w.cyl(rope, (mx + 0.012, -wf / 2, zf), (mx + 0.012, wf / 2, zf), 0.003, 0.003, 4)
    zm = lambda mh, f: zdeck + mh * f
    # fore mast
    square_sail(0.38, zm(1.02, 0.60), zm(1.02, 0.30), 0.40, 0.46, 0.055)
    square_sail(0.38, zm(1.02, 0.90), zm(1.02, 0.66), 0.30, 0.36, 0.040, furled=True)
    # main mast
    square_sail(-0.08, zm(1.30, 0.56), zm(1.30, 0.22), 0.52, 0.58, 0.065)
    square_sail(-0.08, zm(1.30, 0.82), zm(1.30, 0.58), 0.38, 0.46, 0.05)
    square_sail(-0.08, zm(1.30, 0.98), zm(1.30, 0.84), 0.26, 0.30, 0.03, furled=True)
    # mizzen: lateen sail on slanted yard
    mx = -0.58
    yb = (mx - 0.18, 0, zdeck + 0.18); yt = (mx + 0.22, 0, zdeck + 0.80)
    w.cyl(MT.timber((0.30, 0.22, 0.14), 'yard'), (yb[0], 0, yb[2]), (yt[0], 0, yt[2]), 0.0075, 0.005, 6)
    pts = []
    nu = 8
    tackp = (mx - 0.26, 0, zdeck + 0.08)
    for iu in range(nu):
        for iv in range(4):
            def lp(a, b):
                u = a / nu; s = b / 4
                top = Vector(yb) * (1 - u) + Vector(yt) * u
                bot = Vector(tackp) * (1 - u) + Vector((mx + 0.0, 0, zdeck + 0.18)) * u
                p = top * (1 - s) + bot * s
                p.x += 0.012 + 0.05 * math.sin(math.pi * u) * math.sin(math.pi * (0.1 + 0.8 * s))
                p.y += 0.004
                return tuple(p)
            w.face(sail, [lp(iu, iv), lp(iu + 1, iv), lp(iu + 1, iv + 1), lp(iu, iv + 1)][::-1], smooth=True)
    # stays and rigging
    tops = [(m[0], 0, zdeck + m[1] * 0.5) for m in mdefs]
    mt = [(m[0], 0, zdeck + m[1]) for m in mdefs]
    w.cyl(rope, mt[1], mt[0], 0.003, 0.003, 4); w.cyl(rope, mt[0], (1.10, 0, 0.35), 0.003, 0.003, 4)
    w.cyl(rope, mt[2], (mdefs[1][0], 0, zdeck + 0.4), 0.003, 0.003, 4)
    w.cyl(rope, tops[0], (0.74, 0, zdk(0.9)), 0.003, 0.003, 4); w.cyl(rope, tops[1], (0.38, 0, zdeck + 0.3), 0.003, 0.003, 4)
    # pennant (muted ochre) at main top
    pc = MT.painted('pennant', (0.55, 0.34, 0.16), 0.8)
    mpx = mdefs[1][0]; mpz = zdeck + mdefs[1][1]
    w.face(pc, [(mpx, 0.0, mpz), (mpx - 0.16, 0.012, mpz - 0.01), (mpx - 0.30, 0.04, mpz - 0.025), (mpx - 0.16, 0.03, mpz - 0.055), (mpx, 0.0, mpz - 0.05)])
    out = w.commit()
    # foam / contact water ring (vertices follow waterline)
    def wl(i, sy): return (xs[i], sy * Bp(ts[i]) * 0.74)
    me = bpy.data.meshes.new('foam'); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    ring_out = lambda i, sy, d: (w.cx + xs[i] + (0.0 if 0 < i < NS else (-d if i == 0 else d * 0.8)), w.cy + sy * (Bp(ts[i]) * 0.74 + d), 0.004)
    ring_in = lambda i, sy: (w.cx + xs[i], w.cy + sy * (Bp(ts[i]) * 0.74 - 0.004), 0.004)
    for sy in (-1, 1):
        for i in range(NS):
            q = [ring_in(i, sy), ring_in(i + 1, sy), ring_out(i + 1, sy, 0.05), ring_out(i, sy, 0.05)]
            if sy > 0: q = q[::-1]
            try: bm.faces.new([bm.verts.new(p) for p in q])
            except Exception: pass
    bm.to_mesh(me); bm.free()
    me.materials.append(MT.alpha_mat('shipfoam', (0.78, 0.84, 0.84), 30, strength=0.55, mask_noise=0.2))
    o = bpy.data.objects.new('foam', me); bpy.context.collection.objects.link(o); o.visible_shadow = False
    # soft dark contact band under hull
    me2 = bpy.data.meshes.new('contact'); bm = bmesh.new()
    for sy in (-1, 1):
        for i in range(NS):
            q = [ring_in(i, sy), ring_in(i + 1, sy), ring_out(i + 1, sy, 0.08 * (1 if 0 < i < NS - 1 else 0.3)), ring_out(i, sy, 0.08 * (1 if 0 < i < NS - 1 else 0.3))]
            q = [(a, b, 0.002) for a, b, c in q]
            if sy > 0: q = q[::-1]
            try: bm.faces.new([bm.verts.new(p) for p in q])
            except Exception: pass
    bm.to_mesh(me2); bm.free()
    me2.materials.append(MT.alpha_mat('shipcontact', (0.02, 0.10, 0.12), 8, strength=0.55, mask_noise=0.1))
    o2 = bpy.data.objects.new('contact', me2); bpy.context.collection.objects.link(o2); o2.visible_shadow = False
    return out

def _hull_mat():
    mb = MB('hull'); uv = mb.coord('UV'); co = mb.coord('Object')
    c, f = mb.brick(uv, (0.15, 0.11, 0.08), (0.24, 0.17, 0.11), (0.03, 0.02, 0.015), 1, 3.0, 0.030, 0.0035, offset=0.0)
    z = mb.sepz(co)['Z']
    wet = mb.fmap(z, 0.07, 0.0, 0, 1)
    col = mb.mix(mb.fmap(mb.noise(co, 40, 4), 0.3, 0.7, 0, 0.5), c, (0.10, 0.09, 0.07))
    col = mb.mix(mb.fmap(mb.noise(mb.mapping(co, (30, 30, 3)), 1, 3), 0.55, 0.8, 0, 0.35), col, (0.36, 0.33, 0.28))
    col = mb.mix(mb.math('MULTIPLY', wet, mb.fmap(mb.noise(co, 25, 3), 0.3, 0.6, 0.3, 0.9)), col, (0.10, 0.17, 0.11))
    mb.done(col, 0.7, mb.bump(f, 0.7, 0.004))
    return mb.m

# ------------------------------------------------------------------ cart + ox, colonists
def cart(ctr):
    w = W(ctr, 'cart')
    wood = MT.planks((0.38, 0.28, 0.18), False, 0.02, 'cartwood'); tim = MT.timber((0.28, 0.20, 0.14)); iron = MT.iron()
    # cart along X, ox ahead (+x)
    cx0 = -0.10
    w.box(wood, cx0, 0, (0.24, 0.13, 0.012), 0.065)
    for sy in (-1, 1): w.box(wood, cx0, sy * 0.062, (0.24, 0.008, 0.045), 0.075)
    w.box(wood, cx0 - 0.116, 0, (0.008, 0.13, 0.045), 0.075)
    for sx in (-1, 1): w.box(tim, cx0 + sx * 0.1, 0, (0.018, 0.17, 0.014), 0.05)
    # wheels: on both sides
    for sy in (-1, 1):
        wy = sy * 0.092
        r = 0.052
        w.cyl(tim, (cx0, wy - 0.006, 0.052), (cx0, wy + 0.006, 0.052), 0.012, 0.012, 8)
        for k in range(8):
            a = k * math.pi / 4
            w.beam(tim, (cx0, wy, 0.052), (cx0 + r * math.cos(a), wy, 0.052 + r * math.sin(a)), 0.007, 0.007)
        for k in range(16):
            a0 = k * math.pi / 8; a1 = (k + 1) * math.pi / 8
            w.beam(tim, (cx0 + r * math.cos(a0), wy, 0.052 + r * math.sin(a0)), (cx0 + r * math.cos(a1), wy, 0.052 + r * math.sin(a1)), 0.014, 0.013, up=(0, 1, 0))
    barrel(w, cx0 + 0.05, -0.02, 0.077, r=0.03, h=0.07); barrel(w, cx0 - 0.04, 0.03, 0.077, r=0.03, h=0.07)
    sack = MT.solid('sack', (0.55, 0.47, 0.34), 0.95)
    w.sphere(sack, (cx0 - 0.07, -0.03, 0.095), 0.03, scale=(1.2, 1, 0.75), seg=8, rings=6)
    # pole + yoke
    w.beam(tim, (cx0 + 0.1, 0, 0.065), (0.18, 0, 0.1), 0.014, 0.012)
    # ox
    hide = MB('hide'); co = hide.coord('Object')
    col = hide.mix(hide.fmap(hide.noise(co, 25, 4), 0.35, 0.65), (0.30, 0.20, 0.13), (0.46, 0.32, 0.21))
    col = hide.mix(hide.fmap(hide.noise(co, 9, 3), 0.55, 0.62, 0, 1), col, (0.78, 0.72, 0.62))
    hide.bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1); hide.link(col, hide.bsdf.inputs['Base Color']); hide.set('Roughness', 0.9)
    ox = 0.27
    w.sphere(hide.m, (ox, 0, 0.088), 0.062, scale=(1.35, 0.62, 0.78), seg=10, rings=7)
    w.sphere(hide.m, (ox + 0.05, 0, 0.098), 0.045, scale=(1.0, 0.75, 0.9), seg=8, rings=6)
    w.sphere(hide.m, (ox + 0.115, 0, 0.088), 0.028, scale=(1.3, 0.8, 0.85), seg=8, rings=6)
    for sy in (-1, 1):
        w.beam(MT.solid('horn', (0.8, 0.75, 0.6), 0.5), (ox + 0.11, sy * 0.02, 0.105), (ox + 0.105, sy * 0.05, 0.125), 0.008, 0.008)
        for dx in (-0.065, 0.065):
            w.cyl(hide.m, (ox + dx, sy * 0.025, 0.07), (ox + dx, sy * 0.025, 0.0), 0.012, 0.008, 6)
    w.beam(hide.m, (ox - 0.08, 0, 0.09), (ox - 0.12, 0, 0.05), 0.007, 0.007)
    w.beam(tim, (ox + 0.0, -0.045, 0.14), (ox + 0.0, 0.045, 0.14), 0.012, 0.012)
    return w.commit()

def colonist(ctr, v):
    w = W(ctr, f'col{v}')
    coats = [(0.30, 0.22, 0.16), (0.25, 0.31, 0.38), (0.45, 0.20, 0.15), (0.48, 0.40, 0.24)]
    legs_ = [(0.16, 0.13, 0.10), (0.20, 0.18, 0.14), (0.14, 0.12, 0.1), (0.30, 0.27, 0.22)]
    hats = [(0.10, 0.08, 0.07), (0.30, 0.26, 0.20), (0.12, 0.10, 0.09), (0.16, 0.12, 0.10)]
    coat = MT.solid(f'coat{v}', coats[v], 0.9); trou = MT.solid(f'trou{v}', legs_[v], 0.9)
    skin = MT.solid('skin', (0.66, 0.50, 0.38), 0.6); hat = MT.solid(f'hat{v}', hats[v], 0.85)
    ph = [0.0, 0.5, 1.4, 2.2][v]
    s = 1.0
    dx, dy = 0.0, 0.0
    # legs
    for sy in (-1, 1):
        w.cyl(trou, (0, sy * 0.014, 0.0), (0.004 * sy, sy * 0.014, 0.088), 0.0125, 0.012, 6)
    w.cyl(coat, (0, 0, 0.082), (0, 0, 0.17), 0.030, 0.024, 8)
    w.cyl(coat, (0, 0, 0.082), (0, 0, 0.11), 0.034, 0.034, 8) if v == 1 else None
    for sy in (-1, 1):
        w.cyl(coat, (0, sy * 0.032, 0.158), (0.012 + 0.01 * sy, sy * 0.036, 0.100), 0.010, 0.008, 6)
    w.sphere(skin, (0, 0, 0.192), 0.020, seg=8, rings=6)
    if v in (0, 3): w.cyl(hat, (0, 0, 0.202), (0, 0, 0.206), 0.036, 0.036, 10); w.cyl(hat, (0, 0, 0.203), (0, 0, 0.226), 0.020, 0.017, 8)
    elif v == 1: w.cyl(hat, (0, 0, 0.205), (0, 0, 0.222), 0.021, 0.018, 8)
    else: w.sphere(hat, (0, 0, 0.205), 0.021, seg=8, rings=5, scale=(1, 1, 0.7))
    # carried item
    if v == 2: w.box(MT.planks((0.4, 0.3, 0.2), False, 0.02, 'cartwood'), 0.0, 0.05, (0.022, 0.12, 0.012), 0.09)
    if v == 1: w.cyl(MT.timber(), (0.03, 0.03, 0.02), (0.045, 0.03, 0.17), 0.004, 0.004, 5)
    return w.commit()

JOBS = {}
for v in range(4): JOBS[f'tree_{v}'] = (tree, (v,), 1, 1, dict(W=800, H=800, K=1.3))
for v in range(2): JOBS[f'rock_{v}'] = (rock, (v,), 1, 1, dict(K=1.35))
JOBS['wheat_field'] = (wheat, (), 2, 2, dict(flat=True, catcher=False, spp=96))
JOBS['pier'] = (pier, (), 1, 1, dict(flat=True))
JOBS['ship'] = (ship, (), 2, 2, dict(spp=128, K=1.18))
JOBS['cart'] = (cart, (), 1, 1, {})
for v in range(4): JOBS[f'colonist_{v}'] = (colonist, (v,), 1, 1, dict(spp=96))
