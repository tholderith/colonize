"""Neon Foundry models. Local footprint coords (u,v): u -> +X (screen right-down), v -> game +y (screen left-down)."""
from lib import *
import lib

C = dict(steel='#4a5058', steel_d='#2b3036', steel_l='#707880', rust='#7c3a1e', red='#8e2b22', teal='#1f6d72',
         mustard='#b08a22', blue='#2c4c80', grey='#6c7276', cream='#a9a79a', orange='#b4561c', concrete='#55575a', black='#14161a')
NEON = dict(cyan='#22eaff', mag='#ff2ea6', amber='#ffa622', green='#45ff86', red='#ff2a2a', violet='#b45cff', white='#e8f4ff')

def S(n, col=None, **k):
    col = C.get(col, col) if col else C[n]
    return surf(n if col is None else n + str(sorted(k.items())), col, **k)
def M(name, **k): return surf('m_' + name + str(sorted(k.items())), C.get(name, name), **k)
def G(name, s=6.0): return glow('g_' + name + str(s), NEON.get(name, name), s)

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
    nt.links.new(mx.outputs[0], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 1.6
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
def farmhouse():
    b = B('farm'); rnd = random.Random(5)
    ground_pad(b, 0.04, 0.04, 0.96, 0.96)
    wall = M('steel', rust=0.35, soot=0.6); dk = M('steel_d', rust=0.1)
    b.box(wall, XY(0.42, 0.55), (0.8, 0.5, 0.2), 0.03)
    # gabled glass roof, ridge along u
    glassm = surf('grow', '#7c3cc0', rough=0.2, metal=0.0, rust=0, soot=0, emit='#a850ff', es=1.5)
    u0, u1, v0, v1, z0, zr = 0.0, 0.84, 0.28, 0.82, 0.23, 0.46
    vm = (v0 + v1) / 2
    b.face(glassm, [X(u0, v0, z0), X(u1, v0, z0), X(u1, vm, zr), X(u0, vm, zr)][::-1])
    b.face(glassm, [X(u0, v1, z0), X(u0, vm, zr), X(u1, vm, zr), X(u1, v1, z0)][::-1])
    b.face(glassm, [X(u1, v0, z0), X(u1, v1, z0), X(u1, vm, zr)]); b.face(glassm, [X(u0, v1, z0), X(u0, v0, z0), X(u0, vm, zr)])
    for k in range(9):   # roof ribs
        uu = u0 + (u1 - u0) * k / 8
        b.beam(dk, X(uu, v0, z0), X(uu, vm, zr), 0.015, 0.015); b.beam(dk, X(uu, v1, z0), X(uu, vm, zr), 0.015, 0.015)
    b.beam(dk, X(u0, vm, zr), X(u1, vm, zr), 0.03, 0.02)
    # glowing grow-light stripes inside visible through glass => green/violet
    for k in range(3):
        b.box(G('violet', 3), XY(0.42, 0.40 + 0.12 * k), (0.7, 0.02, 0.01), 0.2 + 0.02 * k)
    # slit windows with green glow
    for i in range(5):
        b.box(G('green', 4), (0.14 + 0.15 * i, -0.82 - 0.004), (0.09, 0.012, 0.05), 0.1)
    sign(b, 'HYDRO', 'green', 0.45, 0.83, 0.17, 0.08)
    # tanks and pipes
    for k, (tu, tv) in enumerate(((0.87, 0.2), (0.75, 0.12))):
        b.cyl(M('teal', rust=0.3), X(tu, tv, 0.03), X(tu, tv, 0.5 - k * 0.1), 0.085, n=12)
        b.cyl(M('steel_l'), X(tu, tv, 0.5 - k * 0.1), X(tu, tv, 0.53 - k * 0.1), 0.09, n=12)
    b.beam(M('steel_l'), X(0.82, 0.3, 0.12), X(0.62, 0.3, 0.12), 0.03)
    b.cyl(M('steel_d'), X(0.2, 0.3, 0.46), X(0.2, 0.3, 0.6), 0.04, n=8)
    b.cyl(G('violet', 2), X(0.2, 0.3, 0.6), X(0.2, 0.3, 0.61), 0.035, n=8)
    lamp(b, 0.93, 0.9, 0.2, 'amber', 5, 0.5)
    point_light(X(0.5, 0.55, 0.3), (0.75, 0.3, 1.0), 4, 0.1, False)
    pool(0.5, 1.02, 0.55, NEON['violet'], 0.9)
    return b.commit()

# =============================================================== WHEAT FIELD -> hydroponic beds (flat 2x2)
def wheat_field():
    b = B('beds')
    ground_pad(b, 0.06, 0.06, 1.94, 1.94, z=0.02)
    tray = M('steel_d', rust=0.2, soot=0.7); pl = plants_mat()
    for i in range(5):
        u = 0.32 + 0.34 * i
        b.box(tray, XY(u, 1.0), (0.26, 1.7, 0.08), 0.02)
        b.box(pl, XY(u, 1.0), (0.2, 1.62, 0.025), 0.085)
        # grow-light bar on posts
        for vv in (0.2, 1.8): b.box(tray, XY(u, vv), (0.02, 0.02, 0.2), 0.02)
        b.box(G('mag' if i % 2 == 0 else 'violet', 4), XY(u, 1.0), (0.025, 1.7, 0.014), 0.215)
    for vv in (0.12, 1.88):
        b.beam(M('steel_l', rust=0.1, soot=0.3), X(0.15, vv, 0.06), X(1.85, vv, 0.06), 0.04)
    pool(1.0, 1.0, 1.3, NEON['green'], 0.5, power=1.2)
    point_light(X(1.0, 1.0, 0.4), (0.6, 1.0, 0.6), 5, 0.2, False)
    return b.commit()

# =============================================================== WINDMILL -> wind turbine
def windmill():
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
def lumberjack():
    rnd = random.Random(9); b = B('scrap')
    ground_pad(b, 0.03, 0.03, 0.97, 0.97)
    b.box(M('steel', rust=0.5, soot=0.7), XY(0.3, 0.3), (0.42, 0.36, 0.28), 0.03)                 # shed
    b.box(M('steel_d', rust=0.4), XY(0.3, 0.3), (0.5, 0.44, 0.03), 0.31, rot=0.0)                 # roof
    b.box(G('amber', 5), (0.3 + 0.0, -0.3 - 0.18 - 0.003), (0.16, 0.012, 0.09), 0.14)
    b.box(M('steel_d'), (0.3 + 0.21 + 0.003, -0.3), (0.01, 0.15, 0.2), 0.03)
    sign(b, 'SCRAP', 'amber', 0.3, 0.3 + 0.19, 0.2, 0.08)
    # scrap heap
    for i in range(16):
        ang = rnd.uniform(0, 6.28); rr = rnd.uniform(0, 0.2)
        u, v = 0.68 + math.cos(ang) * rr, 0.66 + math.sin(ang) * rr
        h = max(0.04, 0.3 - rr * 1.2) * rnd.uniform(0.5, 1.0)
        col = rnd.choice(['rust', 'steel', 'blue', 'orange', 'grey', 'red', 'steel_d'])
        if rnd.random() < 0.3:
            b.cyl(M(col), X(u, v, 0.03), X(u, v, 0.03 + h * 0.8), 0.045, n=8)
        else:
            b.box(M(col, rust=0.6, soot=0.5), XY(u, v), (rnd.uniform(0.1, 0.2), rnd.uniform(0.08, 0.16), h), 0.03 + max(0, 0.25 - rr) * 0.2 * rnd.random(), rot=rnd.uniform(0, 3))
    # crane
    b.cyl(M('steel_d'), X(0.9, 0.25, 0.03), X(0.9, 0.25, 0.65), 0.025, n=8)
    b.beam(M('orange', rust=0.2), X(0.9, 0.25, 0.64), X(0.62, 0.5, 0.6), 0.03, 0.04)
    b.beam(M('steel_d'), X(0.62, 0.5, 0.6), X(0.62, 0.5, 0.42), 0.006)
    b.cyl(M('steel_l'), X(0.62, 0.5, 0.36), X(0.62, 0.5, 0.42), 0.05, n=10)
    b.sphere(G('red', 8), X(0.9, 0.25, 0.68), 0.022, seg=8, rings=4)
    # drums
    for (u, v, c) in ((0.15, 0.78, 'blue'), (0.28, 0.85, 'orange'), (0.18, 0.9, 'rust')):
        b.cyl(M(c, rust=0.5), X(u, v, 0.03), X(u, v, 0.2), 0.055, n=10)
    b.box(G('green', 4), XY(0.28, 0.85), (0.04, 0.04, 0.01), 0.205)
    lamp(b, 0.53, 0.52, 0.34, 'amber', 6, 0.55)
    point_light(X(0.62, 0.6, 0.3), (1, 0.45, 0.1), 2, 0.1, False)
    return b.commit()

# =============================================================== CHAPEL -> comms spire (2x2)
def chapel():
    rnd = random.Random(21); b = B('spire')
    ground_pad(b, 0.05, 0.05, 1.95, 1.95, z=0.03)
    pod = M('concrete', rust=0.2, soot=0.6, rough=0.6, metal=0.2)
    b.box(pod, XY(1.0, 1.0), (1.6, 1.5, 0.34), 0.03)
    b.box(M('steel_d', rust=0.1), XY(1.0, 1.0), (1.66, 1.56, 0.04), 0.33)
    # neon strips on podium edge
    b.box(G('cyan', 5), (1.0, -1.0 - 0.78 - 0.004), (1.6, 0.014, 0.014), 0.3)
    b.box(G('cyan', 5), (1.0 + 0.83 + 0.004, -1.0), (0.014, 1.5, 0.014), 0.3)
    # entrance steps with warm door
    b.box(G('amber', 5), (1.0 - 0.3, -1.0 - 0.78 - 0.005), (0.22, 0.012, 0.2), 0.05)
    # windows on podium
    for i in range(4): b.box(G('amber', 3.5), (0.55 + 0.2 * i + 0.25, -1.0 - 0.78 - 0.005), (0.09, 0.012, 0.07), 0.15) if i > 0 else None
    # tower
    tw = M('steel', rust=0.35, soot=0.7, rough=0.45, metal=0.5)
    cu, cv = 1.0, 0.95
    def ring(h, w): return [(cu - w, -cv - w, h), (cu + w, -cv - w, h), (cu + w, -cv + w, h), (cu - w, -cv + w, h)]
    b.loft(tw, [ring(0.37, 0.32), ring(1.5, 0.30), ring(1.9, 0.20), ring(2.15, 0.12)])
    # window bands on visible faces (y- face at -cv-w, x+ face at cu+w)
    for k in range(6):
        z = 0.55 + k * 0.17
        w = 0.32 - (z - 0.37) / (1.5 - 0.37) * 0.02
        for j in range(3):
            if rnd.random() < 0.8:
                b.box(G('amber' if rnd.random() < 0.7 else 'cyan', 3.5), (cu - 0.18 + 0.18 * j, -cv - w - 0.004), (0.08, 0.012, 0.06), z)
            if rnd.random() < 0.8:
                b.box(G('amber' if rnd.random() < 0.7 else 'cyan', 3.5), (cu + w + 0.004, -cv - 0.18 + 0.18 * j), (0.012, 0.08, 0.06), z)
    # big sign panel on the left (y-) face, and blade sign on the right face
    wy = cv + 0.30 - (1.55 - 0.37) / (1.5 - 0.37) * 0.0
    b.box(M('black', rust=0, soot=0, rough=0.3, metal=0.0), (cu, -cv - 0.305 - 0.01), (0.54, 0.02, 0.2), 1.05) if False else None
    sign(b, 'KALDERA', 'mag', cu, cv + 0.302, 1.12, 0.098, 'y-', s=9)
    sign(b, 'RELAY', 'cyan', cu + 0.302, cv, 1.2, 0.09, 'x+', s=9)
    for dz in (1.05, 1.34): b.box(G('mag', 6), (cu, -cv - 0.31), (0.56, 0.012, 0.012), dz)
    # spire
    b.cyl(M('steel_l', rust=0.2), X(cu, cv, 2.1), X(cu, cv, 3.1), 0.03, 0.012, n=8)
    for k, z in enumerate((2.3, 2.6, 2.85)): b.cyl(G('cyan', 6), X(cu, cv, z), X(cu, cv, z + 0.02), 0.075 - 0.015 * k, n=12)
    b.cyl(M('cream', rust=0.1), X(cu + 0.1, cv - 0.02, 2.0), X(cu + 0.2, cv - 0.04, 2.1), 0.02, 0.1, n=10)    # dish
    b.beam(M('steel_l'), X(cu - 0.12, cv, 2.45), X(cu + 0.12, cv, 2.45), 0.012)
    b.sphere(G('red', 14), X(cu, cv, 3.12), 0.03, seg=8, rings=4)
    point_light(X(cu, cv, 3.15), (1, 0.1, 0.1), 3, 0.03, False)
    # downlight pools from signage
    point_light(X(cu - 0.05, cv + 0.5, 1.15), (1, 0.15, 0.6), 22, 0.1)
    point_light(X(cu + 0.5, cv, 1.2), (0.1, 0.9, 1), 12, 0.1)
    pool(cu, cv + 0.75, 0.9, NEON['mag'], 0.9, power=1.6); pool(cu + 0.8, cv + 0.1, 0.7, NEON['cyan'], 0.7, power=1.6)
    for (uu, vv) in ((0.2, 1.8), (1.8, 1.8)): lamp(b, uu, vv, 0.22, 'amber', 6, 0.5)
    b.cyl(M('steel_d'), X(0.2, 1.8, 0.03), X(0.2, 1.8, 0.22), 0.012, n=6); b.cyl(M('steel_d'), X(1.8, 1.8, 0.03), X(1.8, 1.8, 0.22), 0.012, n=6)
    return b.commit()

# =============================================================== WAREHOUSE -> container depot (2x2)
def warehouse():
    rnd = random.Random(33); b = B('depot')
    ground_pad(b, 0.05, 0.05, 1.95, 1.95, z=0.03)
    hall = M('steel', rust=0.5, soot=0.7, rough=0.5, metal=0.4)
    b.box(hall, XY(0.62, 0.55), (1.0, 0.85, 0.55), 0.03)
    b.box(M('steel_d', rust=0.2), XY(0.62, 0.55), (1.1, 0.95, 0.04), 0.58)
    # roller door glow on y- face (v = 0.55+0.425)
    vf = 0.55 + 0.425
    b.box(G('amber', 3.5), (0.62, -vf - 0.004), (0.5, 0.012, 0.36), 0.05)
    for k in range(6): b.box(M('steel_d'), (0.62, -vf - 0.008), (0.5, 0.01, 0.01), 0.07 + k * 0.06)
    sign(b, 'DEPOT-03', 'cyan', 0.62, vf + 0.015, 0.45, 0.075, 'y-', s=9)
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
def pier():
    b = B('pier')
    deck = M('steel_d', rust=0.4, soot=0.6, rough=0.45, metal=0.5)
    b.box(deck, XY(0.5, 0.5), (1.04, 0.5, 0.05), 0.04)
    b.box(hazard_mat(), XY(0.5, 0.26), (1.04, 0.035, 0.052), 0.04); b.box(hazard_mat(), XY(0.5, 0.74), (1.04, 0.035, 0.052), 0.04)
    for u in (0.1, 0.5, 0.9):
        for v in (0.24, 0.76): b.cyl(M('steel', rust=0.7, soot=0.8), X(u, v, -0.1), X(u, v, 0.05), 0.035, n=8, caps=False)
    for k in range(5): b.box(M('steel_l', rust=0.2), XY(0.14 + 0.18 * k, 0.5), (0.02, 0.4, 0.012), 0.09)
    for (u, v, c) in ((0.08, 0.2, 'amber'), (0.92, 0.2, 'cyan'), (0.92, 0.8, 'cyan'), (0.08, 0.8, 'amber')):
        b.box(M('steel_d'), XY(u, v), (0.04, 0.04, 0.1), 0.09); b.box(G(c, 9), XY(u, v), (0.05, 0.05, 0.03), 0.19)
    point_light(X(0.9, 0.5, 0.26), (0.1, 0.9, 1), 3, 0.05, False); point_light(X(0.1, 0.5, 0.26), (1, 0.6, 0.2), 3, 0.05, False)
    pool(0.5, 0.5, 0.75, NEON['amber'], 0.6, z=0.095, power=1.4)
    return b.commit()

# =============================================================== SHIP -> hover cargo hauler (2x2), long axis along v
def ship():
    rnd = random.Random(44); b = B('ship')
    hull = M('rust', rust=0.7, soot=0.7, rough=0.5, metal=0.45)
    cu = 1.0
    stations = [(0.12, 0.04, 0.36), (0.45, 0.27, 0.34), (0.95, 0.34, 0.31), (1.5, 0.34, 0.31), (1.88, 0.30, 0.31)]
    rings = []
    for (v, w, zt) in stations:
        rings.append([(cu - w, -v, zt), (cu + w, -v, zt), (cu + w * 0.78, -v, 0.07), (cu - w * 0.78, -v, 0.07)])
    b.loft(hull, rings)
    # deck
    b.loft(M('steel_d', rust=0.4, soot=0.8), [[(cu - 0.3, -0.45, 0.335), (cu + 0.3, -0.45, 0.335), (cu + 0.3, -1.8, 0.33), (cu - 0.3, -1.8, 0.33)],
                                              [(cu - 0.3, -0.45, 0.31), (cu + 0.3, -0.45, 0.31), (cu + 0.3, -1.8, 0.31), (cu - 0.3, -1.8, 0.31)]], cap_ends=False) if False else None
    # hazard stripe + waterline glow strip
    b.box(hazard_mat(), (cu + 0.335, -1.2), (0.01, 1.2, 0.03), 0.28)
    b.box(G('cyan', 5), (cu + 0.265, -1.2), (0.012, 1.45, 0.018), 0.07)
    b.box(G('cyan', 5), (cu, -1.89), (0.58, 0.012, 0.018), 0.07)
    b.box(M('steel_d', rust=0.3), (cu, -1.0), (0.64, 1.7, 0.02), 0.31)
    # cargo
    cols = ['red', 'teal', 'mustard', 'blue', 'cream', 'orange']
    for vv in (0.55, 1.05):
        for uu, nn in ((cu - 0.15, 2), (cu + 0.15, 3 if vv < 0.8 else 2)):
            for h in range(nn): cont(b, uu, vv, 0.33 + 0.18 * h, 'y', rnd.choice(cols), L=0.46, Wd=0.26, H=0.175, wins=False)
    # superstructure at stern
    sv = 1.62
    b.box(M('cream', rust=0.4, soot=0.6), XY(cu, sv), (0.56, 0.3, 0.36), 0.32)
    b.box(M('cream', rust=0.4, soot=0.6), XY(cu, sv), (0.46, 0.22, 0.14), 0.68)
    for k in range(4): b.box(G('amber', 4), (cu - 0.18 + 0.12 * k, -(sv + 0.151)), (0.075, 0.012, 0.05), 0.45)
    for k in range(3): b.box(G('amber', 4), (cu + 0.281, -(sv - 0.08 + 0.08 * k)), (0.012, 0.05, 0.05), 0.45)
    b.box(G('cyan', 5), (cu, -(sv + 0.111)), (0.4, 0.012, 0.06), 0.72)
    b.box(G('cyan', 5), (cu + 0.231, -sv), (0.012, 0.2, 0.06), 0.72)
    b.cyl(M('steel_d', rust=0.5, soot=0.9), X(cu - 0.15, sv + 0.02, 0.82), X(cu - 0.15, sv + 0.02, 1.05), 0.055, 0.045, n=10)
    b.cyl(M('red', rust=0.2), X(cu - 0.15, sv + 0.02, 1.0), X(cu - 0.15, sv + 0.02, 1.05), 0.06, 0.06, n=10)
    b.cyl(M('steel_l'), X(cu + 0.1, sv, 0.82), X(cu + 0.1, sv, 1.1), 0.01, n=6)
    for k, (du, dv, dz, r_) in enumerate(((0, 0, 0, 0.07), (0.05, -0.05, 0.1, 0.09), (0.0, -0.12, 0.22, 0.11))):
        b.sphere(steam_mat(), X(cu - 0.15 + du, sv + 0.02 + dv, 1.12 + dz), r_, seg=8, rings=4)
    # running lights
    b.sphere(G('red', 14), X(cu - 0.34, 1.7, 0.4), 0.028, seg=8, rings=4); b.sphere(G('green', 14), X(cu + 0.34, 1.7, 0.4), 0.028, seg=8, rings=4)
    b.sphere(G('white', 14), X(cu, 0.2, 0.42), 0.025, seg=8, rings=4); b.sphere(G('white', 14), X(cu + 0.1, sv, 1.12), 0.025, seg=8, rings=4)
    point_light(X(cu + 0.36, 1.7, 0.4), (0.2, 1.0, 0.3), 2.0, 0.03, False); point_light(X(cu - 0.36, 1.7, 0.4), (1.0, 0.1, 0.1), 2.0, 0.03, False)
    point_light(X(cu, sv + 0.3, 0.7), (1.0, 0.6, 0.2), 6, 0.05); point_light(X(cu, 1.2, 0.5), (0.1, 0.9, 1.0), 4, 0.05, False)
    pool(cu, 1.2, 1.25, NEON['cyan'], 0.55, z=0.002, power=1.8)
    return b.commit()

# =============================================================== CART -> hover cargo drone
def cart():
    b = B('drone')
    c, d = 0.5, 0.5
    b.box(M('steel', rust=0.4, soot=0.6), XY(c, d), (0.3, 0.3, 0.09), 0.1)
    b.box(M('orange', rust=0.5, soot=0.6), XY(c, d), (0.25, 0.25, 0.14), 0.19)
    b.box(M('steel_d'), XY(c, d), (0.27, 0.27, 0.02), 0.33)
    for (du, dv) in ((-0.14, -0.14), (0.14, -0.14), (0.14, 0.14), (-0.14, 0.14)):
        b.cyl(M('steel_d'), X(c + du, d + dv, 0.07), X(c + du, d + dv, 0.14), 0.04, n=8)
        b.cyl(G('cyan', 6), X(c + du, d + dv, 0.065), X(c + du, d + dv, 0.07), 0.037, n=8)
    b.box(G('cyan', 6), (c + 0.152, -d), (0.012, 0.12, 0.025), 0.14); b.box(G('cyan', 6), (c, -d - 0.152), (0.12, 0.012, 0.025), 0.14)
    b.cyl(M('steel_d'), X(c - 0.08, d - 0.08, 0.34), X(c - 0.08, d - 0.08, 0.5), 0.008, n=5)
    b.sphere(G('amber', 12), X(c - 0.08, d - 0.08, 0.51), 0.02, seg=8, rings=4)
    point_light(X(c - 0.08, d - 0.08, 0.52), (1, 0.55, 0.15), 1.5, 0.02, False)
    point_light(X(c, d, 0.03), (0.1, 0.9, 1.0), 2.5, 0.05, False)
    pool(c, d, 0.5, NEON['cyan'], 1.0, z=0.003, power=1.5)
    return b.commit()

# =============================================================== COLONIST (hooded raincoat)
COATS = ['mustard', 'teal', 'red', 'grey']
def colonist(v):
    b = B('col'); c, d = 0.5, 0.5
    coat = M(COATS[v], rust=0.1, soot=0.4, rough=0.35, metal=0.0)
    b.cyl(coat, X(c, d, 0.0), X(c, d, 0.2), 0.075, 0.048, n=12)
    b.sphere(coat, X(c, d, 0.2), 0.055, seg=10, rings=5, scale=(1, 1, 0.7))
    b.sphere(coat, X(c, d, 0.255), 0.05, seg=10, rings=6)
    fu, fv = c + 0.03, d + 0.03            # face toward camera
    b.sphere(M('black', rust=0, soot=0, rough=0.6, metal=0.0), X(fu, fv, 0.255), 0.032, seg=8, rings=4)
    b.box(G('cyan', 5), (c + 0.052, -d - 0.028), (0.008, 0.02, 0.01), 0.258)
    b.box(G('cyan', 5), (c + 0.028, -d - 0.052), (0.02, 0.008, 0.01), 0.258)
    if v in (0, 2):   # lantern
        b.sphere(G('amber', 9), X(c + 0.07, d + 0.05, 0.1), 0.02, seg=8, rings=4)
        point_light(X(c + 0.07, d + 0.05, 0.1), (1, 0.6, 0.2), 1.0, 0.02)
        pool(c + 0.1, d + 0.1, 0.3, NEON['amber'], 0.9, power=1.6)
    else:
        b.box(M('black'), XY(c - 0.05, d - 0.05), (0.05, 0.04, 0.09), 0.08)
        pool(c + 0.05, d + 0.05, 0.22, NEON['cyan'], 0.35, power=1.6)
    return b.commit()

# =============================================================== TREES -> mutants / pylons / antennae
def tree(v):
    rnd = random.Random(60 + v); b = B('tree')
    bark = M('black', rust=0.3, soot=0.2, rough=0.8, metal=0.0) if v in (0, 2) else None
    steel = M('steel', rust=0.5, soot=0.6, rough=0.5, metal=0.5)
    def twisted(p, h, w, n=5, jit=0.07, dirv=(0, 0)):
        pts = [Vector(p)]
        for k in range(1, n + 1):
            q = Vector((p[0] + dirv[0] * k / n + rnd.uniform(-jit, jit), p[1] + dirv[1] * k / n + rnd.uniform(-jit, jit), p[2] + h * k / n))
            pts.append(q)
        for k in range(n):
            b.cyl(bark, pts[k], pts[k + 1], w * (1 - k / (n + 1)), w * (1 - (k + 1) / (n + 1)), n=6)
        return pts
    if v == 0:
        tp = twisted((0.5, -0.5, 0.0), 0.5, 0.05)
        fol = surf('mutfol', '#12342e', rough=0.8, metal=0, rust=0, soot=0.3, emit='#18e0a0', es=0.5)
        for k in range(3):
            ang = rnd.uniform(0, 6.28); br = twisted((tp[3].x, tp[3].y, tp[3].z), 0.22, 0.022, 3, 0.04, (math.cos(ang) * 0.2, math.sin(ang) * 0.2))
            b.sphere(fol, br[-1], 0.1, seg=8, rings=4, jitter=0.15, rng=rnd)
            b.sphere(G('green', 6), br[-1] + Vector((0.07, -0.04, 0.03)), 0.018, seg=6, rings=3)
        b.sphere(fol, tp[-1], 0.13, seg=8, rings=4, jitter=0.15, rng=rnd); b.sphere(G('cyan', 6), tp[-1] + Vector((0.09, -0.08, 0.02)), 0.02, seg=6, rings=3)
        point_light(tuple(tp[-1] + Vector((0.1, -0.1, 0.0))), (0.2, 1.0, 0.7), 1.2, 0.03)
        pool(0.55, 0.55, 0.35, NEON['green'], 0.4, power=1.8)
    elif v == 1:
        h = 1.35
        pts = [(-0.14, -0.14), (0.14, -0.14), (0.14, 0.14), (-0.14, 0.14)]
        for (a, c_) in pts: b.beam(steel, (0.5 + a, -0.5 + c_, 0.0), (0.5 + a * 0.18, -0.5 + c_ * 0.18, h), 0.022)
        for z in (0.2, 0.55, 0.9, 1.2):
            f = 1 - z / h * 0.82
            for i in range(4):
                a0 = pts[i]; a1 = pts[(i + 1) % 4]
                b.beam(steel, (0.5 + a0[0] * f, -0.5 + a0[1] * f, z), (0.5 + a1[0] * f, -0.5 + a1[1] * f, z), 0.012)
                f2 = 1 - (z + 0.35) / h * 0.82
                if z < 1.1: b.beam(steel, (0.5 + a0[0] * f, -0.5 + a0[1] * f, z), (0.5 + a1[0] * f2, -0.5 + a1[1] * f2, z + 0.35), 0.01)
        b.beam(steel, (0.5 - 0.35, -0.5 + 0.35, 1.12), (0.5 + 0.35, -0.5 - 0.35, 1.12), 0.025, 0.02)
        b.beam(steel, (0.5 - 0.25, -0.5 + 0.25, 1.28), (0.5 + 0.25, -0.5 - 0.25, 1.28), 0.02, 0.02)
        for s_ in (-1, 1):
            b.cyl(M('cream', rust=0.0), (0.5 + 0.35 * s_, -0.5 - 0.35 * s_, 1.12), (0.5 + 0.35 * s_, -0.5 - 0.35 * s_, 1.0), 0.015, n=6)
        b.sphere(G('red', 14), (0.5, -0.5, h + 0.04), 0.03, seg=8, rings=4); point_light((0.5, -0.5, h + 0.06), (1, 0.1, 0.1), 2, 0.03, False)
        pool(0.5, 0.5, 0.3, NEON['red'], 0.3, power=2.0)
    elif v == 2:
        tp = twisted((0.5, -0.5, 0.0), 0.35, 0.065, 4, 0.08, (0.12, -0.08))
        pod = surf('pod', '#5a2a08', rough=0.4, metal=0, rust=0, soot=0.2, emit='#ff7a18', es=2.2)
        pod2 = surf('pod2', '#40105a', rough=0.4, metal=0, rust=0, soot=0.2, emit='#c040ff', es=2.0)
        for k, (du, dv, dz, r_, pm) in enumerate(((0.12, 0.08, 0.1, 0.1, pod), (-0.1, 0.05, 0.02, 0.07, pod2), (0.05, -0.12, 0.05, 0.08, pod), (-0.03, 0.14, -0.1, 0.06, pod2))):
            b.sphere(pm, (tp[-1].x + du, tp[-1].y - dv, tp[-1].z + dz), r_, seg=8, rings=5)
        point_light(tuple(tp[-1] + Vector((0.12, 0.1, 0.1))), (1.0, 0.45, 0.1), 2.2, 0.05)
        pool(0.62, 0.62, 0.4, NEON['amber'], 0.5, power=1.8)
    else:
        h = 1.5
        b.box(M('steel_d', rust=0.4), (0.5, -0.5), (0.18, 0.14, 0.14), 0.0)
        b.cyl(steel, (0.5, -0.5, 0.14), (0.5, -0.5, h), 0.022, 0.012, n=8)
        b.box(G('green', 7), (0.5 + 0.092, -0.5 - 0.02), (0.012, 0.03, 0.02), 0.08)
        for z, w in ((0.75, 0.2), (1.0, 0.17), (1.25, 0.12)):
            b.beam(steel, (0.5 - w, -0.5 + w * 0.2, z), (0.5 + w, -0.5 - w * 0.2, z), 0.012)
        b.cyl(M('cream'), (0.5 + 0.02, -0.5, 1.15), (0.5 + 0.12, -0.5 - 0.1, 1.28), 0.01, 0.07, n=8)
        for (a, c_) in ((0.28, 0.0), (-0.14, 0.24), (-0.14, -0.24)):
            b.beam(M('steel_d'), (0.5, -0.5, 1.35), (0.5 + a, -0.5 + c_, 0.0), 0.005)
        b.sphere(G('cyan', 12), (0.5, -0.5, h + 0.03), 0.028, seg=8, rings=4); point_light((0.5, -0.5, h + 0.06), (0.1, 0.9, 1.0), 2, 0.03, False)
        pool(0.52, 0.52, 0.3, NEON['cyan'], 0.35, power=2.0)
    return b.commit()

# =============================================================== ROCKS -> slag / scrap
def rock(v):
    rnd = random.Random(80 + v); b = B('rock')
    if v == 0:
        sl = slag_mat()
        for (u, d, r_, z) in ((0.5, 0.5, 0.26, 0.06), (0.36, 0.58, 0.17, 0.04), (0.64, 0.42, 0.16, 0.03), (0.55, 0.65, 0.12, 0.03)):
            b.sphere(sl, X(u, d, z), r_, seg=10, rings=6, scale=(1, 1, 0.8), jitter=0.25, rng=rnd, smooth=True)
        point_light(X(0.55, 0.62, 0.15), (1.0, 0.4, 0.08), 2.5, 0.05)
        pool(0.55, 0.62, 0.45, NEON['amber'], 0.45, power=1.7)
    else:
        ground_pad(b, 0.2, 0.2, 0.8, 0.8, z=0.015)
        for i in range(10):
            u, d = 0.5 + rnd.uniform(-0.2, 0.2), 0.5 + rnd.uniform(-0.2, 0.2)
            col = rnd.choice(['rust', 'steel', 'blue', 'orange', 'grey', 'steel_d'])
            b.box(M(col, rust=0.6), XY(u, d), (rnd.uniform(0.1, 0.22), rnd.uniform(0.06, 0.16), rnd.uniform(0.03, 0.09)), 0.015 + rnd.random() * 0.12, rot=rnd.uniform(0, 3))
        b.cyl(M('orange', rust=0.5), X(0.35, 0.65, 0.015), X(0.35, 0.65, 0.2), 0.05, n=8)
        b.cyl(M('steel_l', rust=0.5), X(0.66, 0.35, 0.015), X(0.62, 0.45, 0.3), 0.015, n=6)
        b.box(G('green', 5), XY(0.35, 0.65), (0.03, 0.03, 0.01), 0.205)
        point_light(X(0.35, 0.7, 0.28), (0.3, 1.0, 0.5), 0.8, 0.03, False)
    return b.commit()

# job table: name -> (fn, args, fw, fh, kwargs)
JOBS = {}
for v in range(4): JOBS[f'house_{v}'] = (house, (v,), 1, 1, {})
JOBS['farmhouse'] = (farmhouse, (), 1, 1, {})
JOBS['wheat_field'] = (wheat_field, (), 2, 2, dict(flat=True, catcher=False, H=700))
JOBS['windmill'] = (windmill, (), 1, 1, dict(H=1100, W=700))
JOBS['lumberjack'] = (lumberjack, (), 1, 1, {})
JOBS['chapel'] = (chapel, (), 2, 2, dict(H=1500, W=1000, samples=72))
JOBS['warehouse'] = (warehouse, (), 2, 2, dict(H=1100, samples=72))
JOBS['pier'] = (pier, (), 1, 1, dict(flat=True, catcher=False))
JOBS['ship'] = (ship, (), 2, 2, dict(H=1100, catcher=False))
JOBS['cart'] = (cart, (), 1, 1, dict(catcher=False))
for v in range(4): JOBS[f'colonist_{v}'] = (colonist, (v,), 1, 1, dict(W=300, H=360, samples=48))
for v in range(4): JOBS[f'tree_{v}'] = (tree, (v,), 1, 1, dict(H=900))
for v in range(2): JOBS[f'rock_{v}'] = (rock, (v,), 1, 1, dict(samples=48))
