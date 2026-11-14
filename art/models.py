"""Neon Foundry models. Local footprint coords (u,v): u -> +X (screen right-down), v -> game +y (screen left-down)."""
from lib import *
import lib

C = dict(steel='#4a5058', steel_d='#2b3036', steel_l='#707880', rust='#7c3a1e', red='#8e2b22', teal='#1f6d72',
         mustard='#b08a22', blue='#2c4c80', grey='#6c7276', cream='#a9a79a', orange='#b4561c', concrete='#55575a', black='#14161a')
NEON = dict(hot='#ff5a14', cyan='#22eaff', mag='#ff2ea6', amber='#ffa622', green='#45ff86', red='#ff2a2a', violet='#b45cff', white='#e8f4ff')

def S(n, col=None, **k):
    col = C.get(col, col) if col else C[n]
    return surf(n if col is None else n + str(sorted(k.items())), col, **k)
def M(name, **k): return surf('m_' + name + str(sorted(k.items())), C.get(name, name), **k)
def G(name, s=6.0): return glow('g_' + name + str(s), NEON.get(name, name), s * 0.42)

def hazard_mat():
    if 'hazard' in MATS: return MATS['hazard']
    m, nt = lib._nodes(); m.name = 'hazard'
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'DIAGONAL'
    w.inputs['Scale'].default_value = 9; w.inputs['Distortion'].default_value = 0.0
    nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.interpolation = 'CONSTANT'
    r.color_ramp.elements[0].color = srgb('#16181a'); r.color_ramp.elements[1].color = srgb('#c79a1a'); r.color_ramp.elements[1].position = 0.5
    nt.links.new(w.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.5; MATS['hazard'] = m; return m

def plants_mat(col='#3cff7a'):
    key = 'plants' + col
    if key in MATS: return MATS[key]
    m, nt = lib._nodes(); m.name = key
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); v = nt.nodes.new('ShaderNodeTexVoronoi'); v.inputs['Scale'].default_value = 55
    nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = 0.15; r.color_ramp.elements[1].position = 0.55
    r.color_ramp.elements[0].color = (1, 1, 1, 1); r.color_ramp.elements[1].color = (0.05, 0.05, 0.05, 1)
    nt.links.new(v.outputs['Distance'], r.inputs['Fac'])
    mx = nt.nodes.new('ShaderNodeMixRGB'); mx.blend_type = 'MULTIPLY'; mx.inputs['Fac'].default_value = 1.0
    mx.inputs[1].default_value = srgb(col); nt.links.new(r.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 0.8
    nt.links.new(mx.outputs[0], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.7
    MATS[key] = m; return m

def slag_mat():
    if 'slag' in MATS: return MATS['slag']
    m, nt = lib._nodes(); m.name = 'slag'
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); v = nt.nodes.new('ShaderNodeTexVoronoi'); v.feature = 'DISTANCE_TO_EDGE'; v.inputs['Scale'].default_value = 9
    nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = 0.0; r.color_ramp.elements[1].position = 0.07
    r.color_ramp.elements[0].color = (1, 1, 1, 1); r.color_ramp.elements[1].color = (0, 0, 0, 1)
    nt.links.new(v.outputs['Distance'], r.inputs['Fac'])
    em = nt.nodes.new('ShaderNodeMixRGB'); em.blend_type = 'MULTIPLY'; em.inputs['Fac'].default_value = 1; em.inputs[1].default_value = srgb('#ff6a10')
    nt.links.new(r.outputs[0], em.inputs[2]); nt.links.new(em.outputs[0], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 4.0
    bs.inputs['Base Color'].default_value = srgb('#2a2624'); bs.inputs['Roughness'].default_value = 0.85
    MATS['slag'] = m; return m

def steam_mat():
    if 'steam' in MATS: return MATS['steam']
    m, nt = lib._nodes(); m.name = 'steam'
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    bs.inputs['Base Color'].default_value = srgb('#9aa6b8'); bs.inputs['Alpha'].default_value = 0.28; bs.inputs['Roughness'].default_value = 1.0
    bs.inputs['Emission Color'].default_value = srgb('#6a7a96'); bs.inputs['Emission Strength'].default_value = 0.5
    MATS['steam'] = m; return m

def lamp(b, u, v, z, col='amber', watts=5, pool_r=0.5, pool_s=1.3, r=0.022, pu=None, pv=None, shadow=True, es=9.0):
    b.sphere(G(col, es), X(u, v, z), r, seg=8, rings=4)
    point_light(X(u, v, z), _rgb(NEON[col]), watts, 0.03, shadow)
    pool(pu if pu is not None else u + 0.1, pv if pv is not None else v + 0.1, pool_r, NEON[col], pool_s)

def _rgb(h): return tuple(int(h.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4))

def winq(b, face, u, v, z, on=None, w=0.085, h=0.065, rnd=random):
    """window on a visible face of a container/wall at plane coordinates (u,v) (face centre point on the wall)."""
    r = rnd.random() if on is None else on
    cols = ['amber'] * 7 + ['cyan'] + ['green'] if r < 0.85 else None
    dark = M('steel_d', rust=0.0, soot=0.2)
    if cols is None:
        mat = surf('winoff', '#0b1620', rough=0.2, metal=0.0, rust=0, soot=0, emit='#16364a', es=0.3)
    else:
        mat = G(rnd.choice(cols), 4.5)
    if face == 'y-':   # wall plane at Blender Y = -v
        b.box(dark, (u, -v - 0.003), (w + 0.025, 0.012, h + 0.025), z - 0.0125)
        b.box(mat, (u, -v - 0.009), (w, 0.012, h), z)
    else:              # 'x+' wall plane at X = u
        b.box(dark, (u + 0.003, -v), (0.012, w + 0.025, h + 0.025), z - 0.0125)
        b.box(mat, (u + 0.009, -v), (0.012, w, h), z)

def cont(b, u, v, z, axis, col, L=0.78, Wd=0.36, H=0.29, wins=True, rnd=random, door=True):
    mat = M(col, rust=0.45, soot=0.6, rough=0.55, metal=0.35, bump=0.0)
    size = (L, Wd, H) if axis == 'x' else (Wd, L, H)
    b.box(mat, XY(u, v), size, z)
    dk = M('steel_d', rust=0.1, soot=0.5)
    # frame rails (top+bottom) for relief
    b.box(dk, XY(u, v), (size[0] + 0.012, size[1] + 0.012, 0.022), z)
    b.box(dk, XY(u, v), (size[0] + 0.012, size[1] + 0.012, 0.022), z + H - 0.022)
    if wins:
        if axis == 'x':
            n = 3
            for i in range(n):
                uu = u - L / 2 + (i + 0.5) * L / n; winq(b, 'y-', uu, v + Wd / 2, z + H * 0.5, rnd=rnd)
            if door:
                b.box(M('steel_d', rust=0.2), (u + L / 2 + 0.004, -v), (0.01, Wd * 0.55, H * 0.8), z + 0.02)
        else:
            n = 3
            for i in range(n):
                vv = v - L / 2 + (i + 0.5) * L / n; winq(b, 'x+', u + Wd / 2, vv, z + H * 0.5, rnd=rnd)
            if door:
                b.box(M('steel_d', rust=0.2), (u, -(v + L / 2) - 0.004), (Wd * 0.55, 0.01, H * 0.8), z + 0.02)

def legs(b, u0, v0, u1, v1, h=0.06):
    d = M('steel_d', rust=0.2)
    for u in (u0, u1):
        for v in (v0, v1): b.box(d, XY(u, v), (0.06, 0.06, h), 0.0)

def sign(b, txt, col, u, v, z, size, face='y-', s=7.0, frame=True, w=None, h=None):
    mat = G(col, s)
    if face == 'y-':
        o = text3d(txt, mat, (u, -v - 0.012, z), size, rot=(math.radians(90), 0, 0))
    else:
        o = text3d(txt, mat, (u + 0.012, -v, z), size, rot=(math.radians(90), 0, math.radians(90)))
    return o

def ground_pad(b, u0, v0, u1, v1, col='concrete', z=0.025):
    b.box(M(col, rust=0.1, soot=0.8, rough=0.8, metal=0.0), XY((u0 + u1) / 2, (v0 + v1) / 2), (u1 - u0, v1 - v0, z), 0.0)

# =============================================================== HOUSES

def house(v):
    rnd = random.Random(100 + v); b = B('house')
    ground_pad(b, 0.04, 0.04, 0.96, 0.96)
    legs(b, 0.12, 0.12, 0.88, 0.88)
    if v == 0:
        cont(b, 0.5, 0.28, 0.06, 'x', 'red', rnd=rnd); cont(b, 0.5, 0.72, 0.06, 'x', 'teal', rnd=rnd)
        cont(b, 0.5, 0.5, 0.35, 'y', 'mustard', L=0.76, rnd=rnd)
        b.box(M('steel_l', rust=0.2), XY(0.28, 0.3), (0.12, 0.1, 0.07), 0.64)       # roof AC
        b.box(G('mag', 6), (0.92, -0.5), (0.012, 0.012, 0.25), 0.1)                    # neon strip
        lamp(b, 0.96, 0.9, 0.2, 'amber', 6, 0.5)
    elif v == 1:
        cont(b, 0.45, 0.5, 0.06, 'x', 'blue', rnd=rnd); cont(b, 0.45, 0.5, 0.35, 'y', 'rust', rnd=rnd)
        cont(b, 0.38, 0.5, 0.64, 'x', 'grey', L=0.6, rnd=rnd)
        b.cyl(M('steel_l'), X(0.88, 0.2, 0.0), X(0.88, 0.2, 0.55), 0.07, n=10)           # water tank
        b.cyl(M('rust'), X(0.88, 0.2, 0.55), X(0.88, 0.2, 0.62), 0.075, n=10)
        for k in range(3): b.beam(M('steel_d'), X(0.82, 0.3 + 0.1 * k, 0.1 * k), X(0.82, 0.4 + 0.1 * k, 0.1 * k + 0.1), 0.05, 0.015)
        sign(b, 'BUNK', 'cyan', 0.45, 0.5 + 0.18 + 0.0, 0.0, 0.0) if False else None
        b.box(G('cyan', 6), XY(0.45 + 0.4, 0.85), (0.012, 0.012, 0.35), 0.35)
        lamp(b, 0.93, 0.78, 0.22, 'amber', 5, 0.5)
    elif v == 2:
        cont(b, 0.3, 0.5, 0.06, 'y', 'cream', rnd=rnd); cont(b, 0.7, 0.5, 0.06, 'y', 'orange', rnd=rnd)
        cont(b, 0.5, 0.45, 0.35, 'x', 'teal', L=0.72, rnd=rnd)
        b.sphere(M('steel_l', rust=0.1), X(0.62, 0.38, 0.64), 0.12, scale=(1, 1, 0.55), seg=12, rings=6)
        b.sphere(G('cyan', 1.5), X(0.62, 0.38, 0.655), 0.07, scale=(1, 1, 0.35), seg=10, rings=4)
        b.cyl(M('steel_d'), X(0.28, 0.35, 0.64), X(0.28, 0.35, 0.95), 0.012, n=6)
        b.box(G('red', 8), XY(0.28, 0.35), (0.03, 0.03, 0.03), 0.95)
        point_light(X(0.28, 0.35, 0.97), (1, 0.1, 0.1), 0.6, 0.02)
        lamp(b, 0.96, 0.15, 0.2, 'mag', 4, 0.45, 1.0)
    else:
        cont(b, 0.5, 0.74, 0.06, 'x', 'mustard', rnd=rnd); cont(b, 0.22, 0.33, 0.06, 'y', 'blue', L=0.5, rnd=rnd)
        cont(b, 0.42, 0.74, 0.35, 'x', 'red', L=0.7, rnd=rnd)
        b.box(M('steel_l', rust=0.2), XY(0.78, 0.4), (0.16, 0.16, 0.12), 0.06)    # generator
        b.cyl(M('steel_d'), X(0.78, 0.4, 0.18), X(0.78, 0.4, 0.55), 0.018, n=6)
        b.box(G('amber', 5), XY(0.2, 0.62), (0.012, 0.012, 0.2), 0.4)
        # satellite dish
        b.cyl(M('cream', rust=0.1), X(0.6, 0.7, 0.64), X(0.65, 0.78, 0.76), 0.02, 0.1, n=10)
        lamp(b, 0.93, 0.92, 0.22, 'cyan', 4, 0.45, 1.0)
    return b.commit()

# =============================================================== FARMHOUSE (hydroponics shed)


# =============================================================== HYDROPONICS (2x2): wheat_field beds + tanks + control shed
def hydroponics():
    b = B('hydro'); rnd = random.Random(7)
    ground_pad(b, 0.05, 0.05, 1.95, 1.95, z=0.03)
    tray = M('steel_d', rust=0.2, soot=0.7); pl = plants_mat(); st = M('steel_l', rust=0.1, soot=0.3)
    for i in range(5):
        u = 0.30 + 0.30 * i
        b.box(tray, XY(u, 0.78), (0.24, 1.3, 0.09), 0.03)
        b.box(pl, XY(u, 0.78), (0.19, 1.24, 0.025), 0.12)
        for vv in (0.2, 1.36): b.box(tray, XY(u, vv), (0.02, 0.02, 0.22), 0.03)
        b.box(G('mag' if i % 2 == 0 else 'violet', 4), XY(u, 0.78), (0.025, 1.3, 0.014), 0.25)
    for uu in (0.14, 1.66):
        b.beam(st, X(uu, 0.15, 0.1), X(uu, 1.42, 0.1), 0.04)
    # control shed along the front (v max): glowing slit windows + sign
    wall = M('steel', rust=0.35, soot=0.6)
    b.box(wall, XY(0.95, 1.68), (1.5, 0.44, 0.3), 0.03)
    b.box(M('steel_d', rust=0.2), XY(0.95, 1.68), (1.58, 0.52, 0.035), 0.33)
    vf = 1.68 + 0.22
    for i in range(6): b.box(G('green', 4), (0.3 + 0.2 * i, -vf - 0.004), (0.12, 0.012, 0.06), 0.14)
    sign(b, 'HYDRO', 'green', 0.95, vf + 0.014, 0.2, 0.09, s=7)
    b.box(G('cyan', 4), (0.95 + 0.75 + 0.004, -1.68), (0.012, 0.2, 0.08), 0.15)
    # nutrient tanks, back-right corner
    for k, (tu, tv) in enumerate(((1.88, 0.2), (1.88, 0.5), (1.6, 0.1))):
        b.cyl(M('teal', rust=0.3), X(tu, tv, 0.03), X(tu, tv, 0.62 - k * 0.1), 0.095, n=12)
        b.cyl(M('steel_l'), X(tu, tv, 0.62 - k * 0.1), X(tu, tv, 0.65 - k * 0.1), 0.10, n=12)
    b.beam(st, X(1.88, 0.2, 0.2), X(1.88, 0.5, 0.2), 0.03)
    b.cyl(G('green', 3), X(1.88, 0.2, 0.65), X(1.88, 0.2, 0.66), 0.05, n=8)
    lamp(b, 1.9, 1.88, 0.3, 'green', 4, 0.9, 0.6, pu=1.5, pv=1.2)
    lamp(b, 0.12, 1.9, 0.3, 'amber', 4, 0.5, 0.9)
    b.cyl(M('steel_d'), X(0.12, 1.9, 0.03), X(0.12, 1.9, 0.3), 0.012, n=6)
    point_light(X(1.0, 0.8, 0.5), (0.8, 0.35, 1.0), 14, 0.2, False)
    pool(1.0, 0.8, 1.2, NEON['violet'], 0.55, power=1.2)
    return b.commit()

# =============================================================== SCRAP YARD (2x2): lumberjack yard, bigger
def scrap_yard():
    rnd = random.Random(9); b = B('scrap')
    ground_pad(b, 0.05, 0.05, 1.95, 1.95, z=0.03)
    b.box(M('steel', rust=0.5, soot=0.7), XY(0.5, 0.45), (0.8, 0.6, 0.32), 0.03)                  # shed
    b.box(M('steel_d', rust=0.4), XY(0.5, 0.45), (0.9, 0.7, 0.035), 0.35)
    vf = 0.45 + 0.3
    b.box(G('amber', 5), (0.5, -vf - 0.004), (0.3, 0.012, 0.1), 0.14)
    b.box(M('steel_d'), (0.5 + 0.4 + 0.003, -0.45), (0.01, 0.22, 0.22), 0.03)
    sign(b, 'SCRAP', 'amber', 0.5, vf + 0.014, 0.25, 0.1, s=7)
    # heap
    for i in range(44):
        ang = rnd.uniform(0, 6.28); rr = rnd.uniform(0, 0.42)
        u, v = 1.3 + math.cos(ang) * rr, 1.3 + math.sin(ang) * rr
        h = max(0.04, 0.5 - rr * 1.1) * rnd.uniform(0.5, 1.0)
        col = rnd.choice(['rust', 'steel', 'blue', 'orange', 'grey', 'red', 'steel_d'])
        if rnd.random() < 0.25:
            b.cyl(M(col), X(u, v, 0.03), X(u, v, 0.03 + h * 0.8), 0.05, n=8)
        else:
            b.box(M(col, rust=0.6, soot=0.5), XY(u, v), (rnd.uniform(0.12, 0.24), rnd.uniform(0.1, 0.2), h), 0.03 + max(0, 0.4 - rr) * 0.2 * rnd.random(), rot=rnd.uniform(0, 3))
    # crane: mast at back right, jib reaching over the heap
    b.cyl(M('steel_d'), X(1.8, 0.3, 0.03), X(1.8, 0.3, 1.0), 0.03, n=8)
    b.beam(M('orange', rust=0.2), X(1.8, 0.3, 0.98), X(1.35, 1.0, 0.92), 0.035, 0.05)
    b.beam(M('steel_d'), X(1.35, 1.0, 0.92), X(1.35, 1.0, 0.66), 0.007)
    b.cyl(M('steel_l'), X(1.35, 1.0, 0.6), X(1.35, 1.0, 0.66), 0.06, n=10)
    b.sphere(G('red', 8), X(1.8, 0.3, 1.04), 0.026, seg=8, rings=4)
    point_light(X(1.8, 0.3, 1.06), (1, 0.1, 0.1), 1.2, 0.03, False)
    # drums + pallet bins
    for (u, v, c) in ((0.25, 1.4, 'blue'), (0.42, 1.52, 'orange'), (0.28, 1.62, 'rust'), (0.5, 1.75, 'blue'), (0.2, 1.8, 'red')):
        b.cyl(M(c, rust=0.5), X(u, v, 0.03), X(u, v, 0.22), 0.06, n=10)
    b.box(G('green', 4), XY(0.42, 1.52), (0.05, 0.05, 0.01), 0.225)
    cont(b, 0.75, 1.1, 0.03, 'y', 'mustard', L=0.5, Wd=0.26, H=0.22, wins=False)
    lamp(b, 0.98, 0.75, 0.38, 'amber', 8, 0.7, 1.0)
    lamp(b, 1.9, 1.9, 0.3, 'amber', 6, 0.6, 1.0)
    b.cyl(M('steel_d'), X(1.9, 1.9, 0.03), X(1.9, 1.9, 0.3), 0.012, n=6)
    point_light(X(1.3, 1.3, 0.4), (1, 0.45, 0.1), 5, 0.1, False)
    return b.commit()

# =============================================================== SMELTER (2x2): new. furnace block, twin stacks, glowing mouth + slag runnel
def smelter():
    rnd = random.Random(21); b = B('smelter')
    ground_pad(b, 0.05, 0.05, 1.95, 1.95, z=0.03)
    body = M('steel', rust=0.55, soot=0.85, rough=0.6, metal=0.35); dk = M('steel_d', rust=0.2, soot=0.7); lt = M('steel_l', rust=0.2)
    cu, cv = 0.75, 0.75; sx, sy, sh = 1.0, 0.9, 0.62
    b.box(body, XY(cu, cv), (sx, sy, sh), 0.03)
    b.box(dk, XY(cu, cv), (sx + 0.1, sy + 0.1, 0.04), 0.03 + sh)                                  # cap slab
    b.box(M('rust', rust=0.7, soot=0.6), XY(cu, cv), (sx * 0.55, sy * 0.55, 0.14), 0.03 + sh + 0.04)  # upper drum
    vf = cv + sy / 2; uf = cu + sx / 2
    # furnace mouth on the v-max face
    b.box(dk, (cu - 0.05, -vf - 0.003), (0.46, 0.012, 0.3), 0.07)
    b.box(G('hot', 9), (cu - 0.05, -vf - 0.010), (0.38, 0.012, 0.22), 0.11)
    for k in range(4): b.box(dk, (cu - 0.05, -vf - 0.014), (0.38, 0.01, 0.012), 0.13 + 0.05 * k)
    sign(b, 'SMELTER', 'hot', cu - 0.05, vf + 0.014, 0.42, 0.085, s=8)
    # side vents on the u-max face
    for k in range(3): b.box(G('hot', 5), (uf + 0.004, -(cv - 0.25 + 0.25 * k)), (0.012, 0.12, 0.05), 0.35)
    # slag runnel from mouth to a pit
    b.box(slag_mat(), XY(cu - 0.05, vf + 0.25), (0.2, 0.5, 0.012), 0.03)
    b.box(dk, XY(cu - 0.05, vf + 0.58), (0.36, 0.16, 0.06), 0.03)
    b.box(G('hot', 7), XY(cu - 0.05, vf + 0.58), (0.28, 0.1, 0.01), 0.09)
    # twin stacks behind the block
    for (su, sv, hh, r0) in ((0.45, 0.4, 1.55, 0.11), (0.85, 0.35, 1.3, 0.09)):
        b.cyl(M('steel', rust=0.6, soot=0.9), X(su, sv, 0.03 + sh), X(su, sv, hh), r0, r0 * 0.7, n=14)
        for z in (0.95, 1.2):
            if z < hh - 0.05: b.cyl(dk, X(su, sv, z), X(su, sv, z + 0.04), r0 * 0.95, n=14)
        b.cyl(G('hot', 6), X(su, sv, hh), X(su, sv, hh + 0.012), r0 * 0.66, n=14)             # glowing mouth of the stack
        b.cyl(dk, X(su, sv, hh - 0.04), X(su, sv, hh), r0 * 0.76, r0 * 0.74, n=14, caps=False)
        b.sphere(G('red', 10), X(su, sv, hh + 0.07), 0.024, seg=8, rings=4)
        point_light(X(su, sv, hh + 0.05), (1.0, 0.35, 0.08), 3, 0.05, False)
        b.beam(lt, X(su, sv, 0.03 + sh + 0.1), X(cu + 0.1, cv, 0.03 + sh + 0.2), 0.035)
    # crucible + gantry on the right
    b.cyl(M('rust', rust=0.5, soot=0.8), X(1.55, 0.85, 0.03), X(1.55, 0.85, 0.28), 0.16, 0.12, n=12)
    b.cyl(G('hot', 8), X(1.55, 0.85, 0.28), X(1.55, 0.85, 0.285), 0.115, n=12)
    for (uu, vv) in ((1.4, 0.7), (1.7, 0.7), (1.4, 1.0), (1.7, 1.0)): b.box(M('orange', rust=0.4, soot=0.5), XY(uu, vv), (0.04, 0.04, 0.55), 0.03)
    b.beam(M('orange', rust=0.4), X(1.4, 0.7, 0.58), X(1.4, 1.0, 0.58), 0.04); b.beam(M('orange', rust=0.4), X(1.7, 0.7, 0.58), X(1.7, 1.0, 0.58), 0.04)
    b.beam(M('orange', rust=0.4), X(1.4, 0.85, 0.6), X(1.7, 0.85, 0.6), 0.04)
    # ingots + coal bunker
    for k in range(6):
        b.box(M('steel_l', rust=0.1, soot=0.2, rough=0.3, metal=0.8), XY(1.4 + 0.18 * (k % 3), 1.5 + 0.12 * (k // 3)), (0.16, 0.1, 0.07), 0.03)
        b.box(G('hot', 3), XY(1.4 + 0.18 * (k % 3), 1.5 + 0.12 * (k // 3)), (0.11, 0.06, 0.008), 0.1)
    cont(b, 0.35, 1.75, 0.03, 'x', 'rust', L=0.7, Wd=0.3, H=0.25, wins=False)
    for k in range(10):
        b.sphere(M('black', rust=0, soot=0.2), X(0.2 + 0.07 * k, 1.75 + rnd.uniform(-0.04, 0.04), 0.3), 0.06, seg=6, rings=4, jitter=0.2, rng=rnd)
    lamp(b, 1.1, 1.3, 0.35, 'amber', 6, 0.6, 1.0)
    b.cyl(M('steel_d'), X(1.1, 1.3, 0.03), X(1.1, 1.3, 0.35), 0.012, n=6)
    lamp(b, 1.9, 1.9, 0.3, 'cyan', 4, 0.5, 0.9)
    b.cyl(M('steel_d'), X(1.9, 1.9, 0.03), X(1.9, 1.9, 0.3), 0.012, n=6)
    point_light(X(cu - 0.05, vf + 0.2, 0.2), (1.0, 0.4, 0.08), 26, 0.1)
    point_light(X(1.55, 0.95, 0.4), (1.0, 0.4, 0.08), 10, 0.1, False)
    pool(cu - 0.05, vf + 0.35, 0.8, NEON['hot'], 1.2, power=1.4)
    return b.commit()


def wind_turbine():
    b = B('turb')
    b.box(M('concrete', rust=0.0, soot=0.9), XY(0.5, 0.5), (0.7, 0.7, 0.05), 0.0)
    tw = M('cream', rust=0.45, soot=0.7, rough=0.5, metal=0.2)
    H = 2.2
    b.cyl(tw, X(0.5, 0.5, 0.05), X(0.5, 0.5, H), 0.085, 0.045, n=14)
    for z in (0.5, 1.0, 1.5): b.cyl(M('rust', rust=0.8), X(0.5, 0.5, z), X(0.5, 0.5, z + 0.03), 0.07 - 0.02 * z / 1.5, n=14, caps=False) if False else None
    b.box(M('steel_d', rust=0.2), XY(0.7, 0.3), (0.16, 0.12, 0.2), 0.05)       # transformer
    b.box(M('steel_d', rust=0.2), XY(0.4, 0.78), (0.1, 0.12, 0.12), 0.05)
    b.box(G('amber', 5), (0.78, -0.3), (0.012, 0.06, 0.04), 0.14)
    b.box(G('green', 6), (0.5 + 0.1, -0.5 - 0.05), (0.03, 0.012, 0.18), 0.2)       # tower door light strip
    # nacelle
    a = Vector((0.62, -0.78, 0)).normalized()          # rotor axis (toward camera-ish)
    ctr = Vector((0.5, -0.5, H))
    b.box(M('steel_l', rust=0.25), (ctr.x, ctr.y), (0.26, 0.12, 0.12), H - 0.04, rot=math.atan2(a.y, a.x))
    hub = ctr + a * 0.15 + Vector((0, 0, 0.0))
    b.sphere(M('cream', rust=0.2), hub, 0.06, seg=10, rings=6, scale=(1.2, 1.2, 1.2))
    perp = Vector((0, 0, 1)).cross(a).normalized(); up = a.cross(perp).normalized()
    ph = math.radians(18)
    for k in range(3):
        ang = ph + k * 2 * math.pi / 3; d = perp * math.cos(ang) + Vector((0, 0, 1)) * math.sin(ang)
        n = d.cross(a).normalized()
        def ring(t, w, th): p = hub + d * t; return [p + n * w / 2 + a * th / 2, p - n * w / 2 + a * th / 2, p - n * w / 2 - a * th / 2, p + n * w / 2 - a * th / 2]
        b.loft(M('cream', rust=0.2, soot=0.3, rough=0.4), [ring(0.04, 0.07, 0.02), ring(0.25, 0.06, 0.012), ring(0.8, 0.015, 0.006)])
        b.loft(M('red', rust=0.0, soot=0.0), [ring(0.72, 0.02, 0.008), ring(0.8, 0.015, 0.006)])
    b.sphere(G('red', 14), (ctr.x - 0.05, ctr.y + 0.03, H + 0.1), 0.028, seg=8, rings=4)
    b.cyl(M('steel_d'), (ctr.x - 0.05, ctr.y + 0.03, H + 0.06), (ctr.x - 0.05, ctr.y + 0.03, H + 0.1), 0.01, n=6)
    point_light((ctr.x - 0.05, ctr.y + 0.03, H + 0.12), (1, 0.1, 0.1), 3, 0.03, False)
    lamp(b, 0.78, 0.4, 0.22, 'amber', 3, 0.4, 1.0)
    return b.commit()

# =============================================================== LUMBERJACK -> scrap yard

def depot():
    rnd = random.Random(33); b = B('depot')
    ground_pad(b, 0.05, 0.05, 1.95, 1.95, z=0.03)
    hall = M('steel', rust=0.5, soot=0.7, rough=0.5, metal=0.4)
    b.box(hall, XY(0.62, 0.55), (1.0, 0.85, 0.55), 0.03)
    b.box(M('steel_d', rust=0.2), XY(0.62, 0.55), (1.1, 0.95, 0.04), 0.58)
    # roller door glow on y- face (v = 0.55+0.425)
    vf = 0.55 + 0.425
    b.box(G('amber', 3.5), (0.62, -vf - 0.004), (0.5, 0.012, 0.36), 0.05)
    for k in range(6): b.box(M('steel_d'), (0.62, -vf - 0.008), (0.5, 0.01, 0.01), 0.07 + k * 0.06)
    sign(b, 'DEPOT', 'cyan', 0.62, vf + 0.015, 0.45, 0.075, 'y-', s=9)
    uf = 0.62 + 0.5
    for k in range(3): b.box(G('amber', 3.5), (uf + 0.004, -(0.3 + k * 0.25)), (0.012, 0.1, 0.07), 0.3)
    for k in range(4): b.cyl(M('steel_d'), X(0.3 + 0.28 * k, 0.55, 0.62), X(0.3 + 0.28 * k, 0.55, 0.7), 0.04, n=8)   # roof vents
    # container stacks
    cols = ['red', 'teal', 'mustard', 'blue', 'cream', 'orange', 'rust', 'grey']
    for (u, v, n_, ax) in ((1.45, 0.45, 3, 'x'), (1.45, 0.85, 2, 'x'), (1.4, 1.45, 3, 'y'), (1.72, 1.45, 2, 'y'), (0.4, 1.5, 2, 'x'), (0.4, 1.8, 3, 'x')):
        for h in range(n_):
            cont(b, u, v, 0.03 + h * 0.2, ax, rnd.choice(cols), L=0.62, Wd=0.28, H=0.195, wins=False)
    # gantry crane (portal over the yard) spanning along u at v=1.15
    st = M('orange', rust=0.4, soot=0.5, rough=0.5, metal=0.4)
    for (uu, vv) in ((0.9, 1.05), (0.9, 1.25), (1.9, 1.05), (1.9, 1.25)): b.box(st, XY(uu, vv), (0.05, 0.05, 1.05), 0.03)
    for uu in (0.9, 1.9):
        b.beam(st, X(uu, 1.05, 1.05), X(uu, 1.25, 1.05), 0.05)
    b.beam(st, X(0.75, 1.05, 1.08), X(2.0, 1.05, 1.08), 0.06, 0.09); b.beam(st, X(0.75, 1.25, 1.08), X(2.0, 1.25, 1.08), 0.06, 0.09)
    b.box(M('steel_d'), XY(1.45, 1.15), (0.2, 0.3, 0.07), 1.0)                           # trolley
    b.beam(M('steel_d'), X(1.45, 1.15, 1.0), X(1.45, 1.15, 0.58), 0.008)
    cont(b, 1.45, 1.15, 0.34, 'y', 'mustard', L=0.5, Wd=0.24, H=0.2, wins=False)
    b.box(G('amber', 6), XY(0.9, 1.05), (0.06, 0.06, 0.03), 1.1); b.sphere(G('red', 12), X(1.9, 1.05, 1.17), 0.025, seg=8, rings=4)
    for (uu, vv) in ((0.9, 1.05), (1.9, 1.25)): b.box(M('steel_l'), XY(uu, vv), (0.07, 0.07, 0.02), 1.08)
    point_light(X(0.95, 1.1, 1.0), (1.0, 0.55, 0.2), 12, 0.06)
    point_light(X(1.85, 1.0, 1.0), (1.0, 0.55, 0.2), 12, 0.06)
    point_light(X(0.62, vf + 0.15, 0.3), (1.0, 0.6, 0.2), 14, 0.08)
    point_light(X(0.62, vf + 0.15, 0.55), (0.1, 0.9, 1.0), 6, 0.08)
    pool(0.62, vf + 0.3, 0.75, NEON['amber'], 1.1, power=1.5); pool(1.3, 1.4, 0.8, NEON['amber'], 0.8, power=1.8)
    lamp(b, 0.12, 1.9, 0.3, 'cyan', 5, 0.5, 0.9)
    b.cyl(M('steel_d'), X(0.12, 1.9, 0.03), X(0.12, 1.9, 0.3), 0.012, n=6)
    return b.commit()

# =============================================================== PIER (flat) -> steel gantry jetty

JOBS = {}
JOBS['pod_house'] = (house, (0,), 1, 1, {})
JOBS['hydroponics'] = (hydroponics, (), 2, 2, dict(H=1000))
JOBS['scrap_yard'] = (scrap_yard, (), 2, 2, dict(H=1100))
JOBS['smelter'] = (smelter, (), 2, 2, dict(H=1500, W=1000))
JOBS['wind_turbine'] = (wind_turbine, (), 1, 1, dict(H=1100, W=700))
JOBS['depot'] = (depot, (), 2, 2, dict(H=1100, samples=64))
