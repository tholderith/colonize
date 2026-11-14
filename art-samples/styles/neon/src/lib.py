"""Neon Foundry - shared Blender helpers (Blender 4.0 Cycles CPU, no denoiser).
Game tile (gx,gy) -> Blender (X=gx, Y=-gy). Camera ortho yaw 45 / pitch 30 (true 2:1).
Local footprint coords used by models: (u,v) -> Blender (u,-v); u runs screen right-down, v runs screen left-down.
Visible faces: 'x+' (right face, warm sodium lit) and 'y-' (left face, cool moon lit)."""
import bpy, bmesh, math, os, sys, random, json
from mathutils import Vector, Euler, Matrix

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WORK = os.environ.get("NWORK", "/tmp/neon_work"); os.makedirs(WORK, exist_ok=True)
SS = 2
SCALE = 64 * SS * math.sqrt(2)        # px per ortho unit at SS x
PITCH = 30.0

def srgb(h):
    if isinstance(h, str):
        h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    else: c = list(h[:3])
    lin = [(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c]
    return (lin[0], lin[1], lin[2], 1.0)

MATS = {}
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True); MATS.clear()

def setup_render(samples, w, h):
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; cy = sc.cycles
    cy.device = 'CPU'; cy.samples = samples; cy.use_denoising = False
    cy.sample_clamp_indirect = 2.0; cy.sample_clamp_direct = 12.0
    cy.max_bounces = 4; cy.diffuse_bounces = 2; cy.glossy_bounces = 3; cy.transmission_bounces = 2; cy.transparent_max_bounces = 6
    cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02; cy.adaptive_min_samples = 16
    cy.blur_glossy = 1.0
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True; sc.render.filter_size = 1.0
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    sc.view_settings.exposure = float(os.environ.get("NEXP", "0.4"))
    make_world(); make_lights()

def make_world():
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    m = nt.nodes.new('ShaderNodeMapRange'); m.inputs['From Min'].default_value = -1; m.inputs['From Max'].default_value = 1
    nt.links.new(sep.outputs['Z'], m.inputs['Value'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    nt.links.new(m.outputs[0], ramp.inputs['Fac'])
    cr.elements[0].position = 0.0; cr.elements[0].color = srgb((0.10, 0.10, 0.13))
    cr.elements[1].position = 1.0; cr.elements[1].color = srgb((0.05, 0.08, 0.20))
    e = cr.elements.new(0.50); e.color = srgb((0.50, 0.22, 0.36))   # magenta dusk horizon
    e = cr.elements.new(0.60); e.color = srgb((0.22, 0.20, 0.38))
    e = cr.elements.new(0.78); e.color = srgb((0.07, 0.11, 0.26))
    nt.links.new(ramp.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.55
    nt.links.new(bg.outputs[0], out.inputs[0])

def sun(name, toward, elev, energy, color, shadow=True, angle=6):
    d = Vector(toward).normalized() * math.cos(math.radians(elev)); d.z = math.sin(math.radians(elev))
    ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = color; ld.angle = math.radians(angle)
    ld.use_shadow = shadow
    o = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(o)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

def make_lights():
    sun('moon', (-0.35, -0.9, 0), 42, 1.5, (0.55, 0.72, 1.0))                 # cool key from upper-left (lights left faces)
    sun('sodium', (0.9, -0.35, 0), 22, 0.85, (1.0, 0.58, 0.25), shadow=False)  # warm fill on right faces
    sun('rim', (-0.6, 0.8, 0), 25, 0.5, (0.9, 0.3, 0.7), shadow=False)         # magenta back-rim for silhouettes

def make_camera(target, w, h, off=0):
    cam = bpy.data.cameras.new("cam"); cam.type = 'ORTHO'; cam.ortho_scale = max(w, h) / SCALE
    cam.clip_start = 0.1; cam.clip_end = 200
    o = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(o)
    o.rotation_euler = Euler((math.radians(90 - PITCH), 0, math.radians(45)), 'XYZ')
    fwd = o.rotation_euler.to_matrix() @ Vector((0, 0, -1)); up = o.rotation_euler.to_matrix() @ Vector((0, 1, 0))
    o.location = Vector(target) + up * (off / SCALE) - fwd * 60
    bpy.context.scene.camera = o
    bpy.context.scene.render.resolution_x = w; bpy.context.scene.render.resolution_y = h

# ---------------------------------------------------------------- materials
def _nodes():
    m = bpy.data.materials.new("m"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    return m, nt

def surf(name, col, rough=0.55, metal=0.4, rust=0.35, soot=0.5, emit=None, es=0.0, bump=0.0, wet=False):
    """grimy painted steel: base colour + rust streaks + soot, procedural in world space."""
    if name in MATS: return MATS[name]
    m, nt = _nodes(); m.name = name
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bs.outputs[0], out.inputs[0])
    bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal
    base = srgb(col)
    if rust > 0 or soot > 0:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (9, 9, 1.4)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 5
        nt.links.new(mp.outputs[0], nz.inputs['Vector'])
        rr = nt.nodes.new('ShaderNodeValToRGB'); rr.color_ramp.elements[0].position = 0.5; rr.color_ramp.elements[1].position = 0.7
        nt.links.new(nz.outputs['Fac'], rr.inputs['Fac'])
        mx = nt.nodes.new('ShaderNodeMixRGB'); mx.inputs[1].default_value = base
        mx.inputs[2].default_value = srgb((0.50, 0.22, 0.08))
        nt.links.new(rr.outputs[0], mx.inputs['Fac'])
        # scale rust by factor
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = rust
        nt.links.new(rr.outputs[0], mul.inputs[0]); nt.links.new(mul.outputs[0], mx.inputs['Fac'])
        # soot noise (fine) darkens
        n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 14.0; n2.inputs['Detail'].default_value = 4
        nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
        m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = soot * 0.9
        nt.links.new(n2.outputs['Fac'], m2.inputs[0])
        mx2 = nt.nodes.new('ShaderNodeMixRGB'); mx2.blend_type = 'MULTIPLY'
        nt.links.new(m2.outputs[0], mx2.inputs['Fac']); nt.links.new(mx.outputs[0], mx2.inputs[1])
        mx2.inputs[2].default_value = (0.25, 0.23, 0.22, 1)
        nt.links.new(mx2.outputs[0], bs.inputs['Base Color'])
        if bump > 0:
            b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = bump; b.inputs['Distance'].default_value = 0.01
            nt.links.new(n2.outputs['Fac'], b.inputs['Height']); nt.links.new(b.outputs[0], bs.inputs['Normal'])
    else:
        bs.inputs['Base Color'].default_value = base
    if emit is not None:
        bs.inputs['Emission Color'].default_value = srgb(emit); bs.inputs['Emission Strength'].default_value = es
        bs.inputs['Base Color'].default_value = tuple(v * 0.2 for v in srgb(emit)[:3]) + (1,)
    MATS[name] = m; return m

def glow(name, col, s=6.0):
    """pure emission (neon tubes, windows, lamps)"""
    if name in MATS: return MATS[name]
    m, nt = _nodes(); m.name = name
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = srgb(col); em.inputs['Strength'].default_value = s
    nt.links.new(em.outputs[0], out.inputs[0]); MATS[name] = m; return m

def pool_mat(name, col, s, power=2.0):
    if name in MATS: return MATS[name]
    m, nt = _nodes(); m.name = name
    out = nt.nodes.new('ShaderNodeOutputMaterial'); mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = srgb(col); em.inputs['Strength'].default_value = s
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sub = nt.nodes.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0)
    nt.links.new(tc.outputs['UV'], sub.inputs[0])
    mu = nt.nodes.new('ShaderNodeVectorMath'); mu.operation = 'SCALE'; mu.inputs['Scale'].default_value = 2.0
    nt.links.new(sub.outputs[0], mu.inputs[0])
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    nt.links.new(mu.outputs[0], gr.inputs['Vector'])
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = power
    nt.links.new(gr.outputs['Fac'], pw.inputs[0])
    cl = nt.nodes.new('ShaderNodeMath'); cl.operation = 'MULTIPLY'; cl.inputs[1].default_value = 0.9; cl.use_clamp = True
    nt.links.new(pw.outputs[0], cl.inputs[0])
    nt.links.new(cl.outputs[0], mix.inputs['Fac']); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0]); MATS[name] = m; return m

# ---------------------------------------------------------------- geometry builder
class B:
    def __init__(s, name="o"): s.name = name; s.bms = {}; s.mats = {}
    def bm(s, mat):
        k = mat.name
        if k not in s.bms: s.bms[k] = bmesh.new(); s.mats[k] = mat
        return s.bms[k]
    def face(s, mat, pts, smooth=False):
        bm = s.bm(mat)
        try: f = bm.faces.new([bm.verts.new(Vector(p)) for p in pts])
        except ValueError: return
        f.smooth = smooth
    def box(s, mat, c, size, z0=0.0, rot=0.0, mats=None):
        """c=(x,y) Blender coords."""
        sx, sy, sz = size; R = Matrix.Rotation(rot, 3, 'Z')
        def P(a, b, d):
            v = R @ Vector((a * sx / 2, b * sy / 2, 0)); return (c[0] + v.x, c[1] + v.y, z0 + d * sz)
        co = {(a, b, d): P(a, b, d) for a in (-1, 1) for b in (-1, 1) for d in (0, 1)}
        g = lambda k: (mats or {}).get(k, mat)
        s.face(g('z-'), [co[(-1, -1, 0)], co[(-1, 1, 0)], co[(1, 1, 0)], co[(1, -1, 0)]])
        s.face(g('z+'), [co[(-1, -1, 1)], co[(1, -1, 1)], co[(1, 1, 1)], co[(-1, 1, 1)]])
        s.face(g('x+'), [co[(1, -1, 0)], co[(1, 1, 0)], co[(1, 1, 1)], co[(1, -1, 1)]])
        s.face(g('x-'), [co[(-1, 1, 0)], co[(-1, -1, 0)], co[(-1, -1, 1)], co[(-1, 1, 1)]])
        s.face(g('y+'), [co[(1, 1, 0)], co[(-1, 1, 0)], co[(-1, 1, 1)], co[(1, 1, 1)]])
        s.face(g('y-'), [co[(-1, -1, 0)], co[(1, -1, 0)], co[(1, -1, 1)], co[(-1, -1, 1)]])
    def beam(s, mat, p0, p1, w=0.02, h=None, up=(0, 0, 1)):
        h = h or w; a = Vector(p0); b = Vector(p1); d = b - a
        if d.length < 1e-6: return
        d.normalize(); u = Vector(up)
        if abs(d.dot(u)) > 0.99: u = Vector((1, 0, 0))
        r = d.cross(u).normalized(); u2 = r.cross(d).normalized()
        ring = lambda p: [p + r * w / 2 + u2 * h / 2, p - r * w / 2 + u2 * h / 2, p - r * w / 2 - u2 * h / 2, p + r * w / 2 - u2 * h / 2]
        A = ring(a); Q = ring(b)
        for i in range(4):
            j = (i + 1) % 4; s.face(mat, [A[i], A[j], Q[j], Q[i]])
        s.face(mat, A[::-1]); s.face(mat, Q)
    def cyl(s, mat, p0, p1, r0, r1=None, n=12, caps=True, smooth=True):
        r1 = r0 if r1 is None else r1; a = Vector(p0); b = Vector(p1); d = b - a
        if d.length < 1e-6: return
        dn = d.normalized(); ref = Vector((0, 0, 1)) if abs(dn.z) < 0.95 else Vector((1, 0, 0))
        u = dn.cross(ref).normalized(); v = dn.cross(u)
        pt = lambda t, rr, k: (a if t == 0 else b) + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * rr
        for k in range(n):
            k2 = (k + 1) % n; s.face(mat, [pt(0, r0, k), pt(0, r0, k2), pt(1, r1, k2), pt(1, r1, k)], smooth=smooth)
        if caps:
            s.face(mat, [pt(0, r0, k) for k in range(n)][::-1]); s.face(mat, [pt(1, r1, k) for k in range(n)])
    def sphere(s, mat, c, r, seg=10, rings=6, scale=(1, 1, 1), jitter=0.0, rng=None, smooth=True):
        c = Vector(c); rr = rng or random
        def P(i, j):
            th = math.pi * j / rings; ph = 2 * math.pi * i / seg
            rj = 1 + (rr.uniform(-jitter, jitter) if jitter and 0 < j < rings else 0)
            return c + Vector((math.sin(th) * math.cos(ph) * scale[0], math.sin(th) * math.sin(ph) * scale[1], math.cos(th) * scale[2])) * r * rj
        g = [[P(i, j) for j in range(rings + 1)] for i in range(seg)]
        for i in range(seg):
            i2 = (i + 1) % seg
            for j in range(rings):
                if j == 0: s.face(mat, [g[i][0], g[i][1], g[i2][1]], smooth=smooth)
                elif j == rings - 1: s.face(mat, [g[i][j], g[i][j + 1], g[i2][j]], smooth=smooth)
                else: s.face(mat, [g[i][j], g[i][j + 1], g[i2][j + 1], g[i2][j]], smooth=smooth)
    def loft(s, mat, rings, cap_ends=True):
        """rings: list of closed polygons (lists of 3D pts), same vertex count, consecutive stations."""
        n = len(rings[0])
        for a, b in zip(rings[:-1], rings[1:]):
            for i in range(n):
                j = (i + 1) % n; s.face(mat, [a[i], a[j], b[j], b[i]])
        if cap_ends:
            s.face(mat, rings[0][::-1]); s.face(mat, rings[-1])
    def commit(s):
        objs = []
        for k, bm in s.bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            me = bpy.data.meshes.new(s.name + k); bm.to_mesh(me); bm.free(); me.materials.append(s.mats[k])
            o = bpy.data.objects.new(s.name + k, me); bpy.context.collection.objects.link(o); objs.append(o)
        s.bms = {}; return objs

def X(u, v, z=0.0): return (u, -v, z)       # local footprint -> Blender
def XY(u, v): return (u, -v)

def point_light(pos, color, watts, radius=0.05, shadow=True):
    ld = bpy.data.lights.new("pl", 'POINT'); ld.energy = watts; ld.color = color[:3]; ld.shadow_soft_size = radius
    o = bpy.data.objects.new("pl", ld); bpy.context.collection.objects.link(o); o.location = pos
    return o

def pool(u, v, r, col, s=1.5, z=0.004, power=2.2, rot=0.0):
    """light-pool decal on the ground, local footprint coords."""
    key = f"pool_{col}_{s}_{power}"
    me = bpy.data.meshes.new("pool")
    me.from_pydata([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for l, c in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[l.index].uv = c
    me.materials.append(pool_mat(key, col, s, power))
    o = bpy.data.objects.new("pool", me); bpy.context.collection.objects.link(o); o.location = (u, -v, z)
    o.visible_shadow = False
    return o

def text3d(txt, mat, pos, size, rot=(math.radians(90), 0, 0), extrude=0.006, align='CENTER'):
    cu = bpy.data.curves.new("t", 'FONT'); cu.body = txt; cu.size = size; cu.extrude = extrude; cu.align_x = align
    cu.materials.append(mat)
    o = bpy.data.objects.new("t", cu); bpy.context.collection.objects.link(o)
    o.location = pos; o.rotation_euler = rot
    return o

# ---------------------------------------------------------------- sprite render
def add_catcher(cx, cy, size):
    me = bpy.data.meshes.new("catcher"); h = size / 2
    me.from_pydata([(cx - h, cy - h, 0), (cx + h, cy - h, 0), (cx + h, cy + h, 0), (cx - h, cy + h, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("catcher", me); bpy.context.collection.objects.link(o); o.is_shadow_catcher = True

def sprite(name, build, fw=1, fh=1, W=None, H=None, samples=64, flat=False, catcher=True, seed=0, extra_off=0, K=1.0):
    ctr = (fw / 2, -fh / 2); S = (fw, -fh, 0)
    big = fw > 1 or fh > 1
    W = W or (1000 if big else 600); H = H or (1000 if big else 640)
    off = H // 2 - 130 + extra_off
    W += W % 2; H += H % 2
    reset(); setup_render(samples, W, H); make_camera(S, W, H, off)
    if catcher: add_catcher(ctr[0] + 0.8, ctr[1] - 0.3, 9 if big else 6)
    random.seed(seed); build()
    os.makedirs(os.path.join(WORK, "raw"), exist_ok=True)
    sc = bpy.context.scene; sc.cycles.seed = seed; sc.render.filepath = os.path.join(WORK, "raw", name + ".png")
    bpy.ops.render.render(write_still=True)
    json.dump(dict(name=name, fw=fw, fh=fh, W=W, H=H, flat=flat, off=off), open(os.path.join(WORK, "raw", name + ".json"), "w"))
    print("RAW", name, flush=True)

def args():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
