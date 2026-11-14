"""Shared Blender helpers for the 'Realistic' style (Blender 4.0 + Cycles, CPU).
Game tile (gx,gy) -> Blender (X=gx, Y=-gy). Camera: ortho, yaw 45, pitch 30 (true 2:1 dimetric)."""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Euler, Matrix
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
WORK = os.environ.get("CWORK", "/tmp/cin_work")
os.makedirs(WORK, exist_ok=True)

SS = 2                                   # supersample factor
PX = 64 * math.sqrt(2) * SS              # px per world unit along X/Y axes ... (128/sqrt2 per axis * SS)
PX = 128 / math.sqrt(2) * SS * math.sqrt(2) / 1.0  # placeholder replaced below
# one tile unit along X projects to (cos45*s, sin45*sin(pitch)*s) ; need cos45*s = 64*SS  -> s = 64*SS*sqrt2
SCALE = 64 * SS * math.sqrt(2)           # px per ortho unit (at SS x)
PITCH_DEG = 30.0                         # sin(pitch)=0.5 gives exact 2:1 tile diamond
ZPX = SCALE * math.cos(math.radians(PITCH_DEG))   # px per unit of height (at SS x)

def srgb(h):
    """hex or tuple (sRGB 0..1) -> linear rgba"""
    if isinstance(h, str):
        h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    else:
        c = list(h[:3])
    lin = [(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c]
    return (lin[0], lin[1], lin[2], 1.0)

# ------------------------------------------------------------------ scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear()

def setup_render(samples=128, w=512, h=512, light=True):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_denoising = False
    cy.sample_clamp_indirect = 3.0
    cy.sample_clamp_direct = 0
    cy.max_bounces = 5; cy.diffuse_bounces = 3; cy.glossy_bounces = 3
    cy.transmission_bounces = 2; cy.transparent_max_bounces = 8
    cy.use_adaptive_sampling = False
    cy.blur_glossy = 0.5
    sc.render.threads_mode = 'AUTO'
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.filter_size = 1.0
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    sc.view_settings.view_transform = os.environ.get("RTONE", "AgX")
    try:
        sc.view_settings.look = os.environ.get("RLOOK", "AgX - Medium High Contrast")
    except Exception:
        pass
    sc.view_settings.exposure = float(os.environ.get("REXP", "0.0"))
    sc.display_settings.display_device = 'sRGB'
    if light:
        make_world(); make_sun()

def make_world():
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w
    w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'EASE'
    # z=-1 ground bounce .. z=0 horizon .. z=1 zenith  (input mapped z*0.5+0.5)
    m = nt.nodes.new('ShaderNodeMapRange'); m.inputs['From Min'].default_value = -1; m.inputs['From Max'].default_value = 1
    nt.links.new(sep.outputs['Z'], m.inputs['Value']); nt.links.new(m.outputs[0], ramp.inputs['Fac'])
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = srgb((0.30, 0.28, 0.24))
    cr.elements[1].position = 1.0; cr.elements[1].color = srgb((0.26, 0.48, 0.80))
    e = cr.elements.new(0.47); e.color = srgb((0.46, 0.45, 0.42))
    e = cr.elements.new(0.56); e.color = srgb((0.88, 0.80, 0.70))
    e = cr.elements.new(0.80); e.color = srgb((0.42, 0.62, 0.90))
    nt.links.new(ramp.outputs[0], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = float(os.environ.get("RSKY", "2.1"))
    nt.links.new(bg.outputs[0], out.inputs[0])

SUN_DIR = Vector((-0.55, -0.80, 0.0))   # horizontal part of direction TOWARD the sun (upper-left on screen)
def make_sun(strength=None, elev=float(os.environ.get('CSUNEL','44'))):
    d = SUN_DIR.normalized() * math.cos(math.radians(elev)); d.z = math.sin(math.radians(elev))
    ld = bpy.data.lights.new("sun", 'SUN')
    ld.energy = strength if strength else float(os.environ.get("RSUN", "3.7"))
    ld.angle = math.radians(4.0)
    ld.color = (1.0, 0.80, 0.56)
    o = bpy.data.objects.new("sun", ld); bpy.context.collection.objects.link(o)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return o

def make_camera(target, w, h, off=0):
    cam = bpy.data.cameras.new("cam"); cam.type = 'ORTHO'
    cam.ortho_scale = max(w, h) / SCALE
    cam.clip_start = 0.1; cam.clip_end = 200
    o = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(o)
    o.rotation_euler = Euler((math.radians(90 - PITCH_DEG), 0, math.radians(45)), 'XYZ')
    fwd = o.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    up = o.rotation_euler.to_matrix() @ Vector((0, 1, 0))
    o.location = Vector(target) + up * (off / SCALE) - fwd * 60
    bpy.context.scene.camera = o
    bpy.context.scene.render.resolution_x = w; bpy.context.scene.render.resolution_y = h
    return o

# ------------------------------------------------------------------ nodes helpers
MATS = {}
class MB:
    """Material builder with terse node helpers."""
    def __init__(s, name):
        s.m = bpy.data.materials.new(name); s.m.use_nodes = True
        s.nt = s.m.node_tree; s.nt.nodes.clear()
        s.out = s.nt.nodes.new('ShaderNodeOutputMaterial')
        s.bsdf = s.nt.nodes.new('ShaderNodeBsdfPrincipled')
        s.nt.links.new(s.bsdf.outputs[0], s.out.inputs[0])
        s.bsdf.inputs['Roughness'].default_value = 0.8
    def n(s, typ, **kw):
        nd = s.nt.nodes.new('ShaderNode' + typ)
        for k, v in kw.items():
            if k in nd.inputs: nd.inputs[k].default_value = v
            else: setattr(nd, k, v)
        return nd
    def link(s, a, b):
        if hasattr(a, 'outputs'): a = a.outputs[0]
        if hasattr(b, 'inputs'): b = b.inputs[0]
        s.nt.links.new(a, b)
    def set(s, name, v):
        if isinstance(v, (int, float, tuple, list)): s.bsdf.inputs[name].default_value = v
        else: s.link(v, s.bsdf.inputs[name])
    def coord(s, kind='Object'):
        return s.n('TexCoord').outputs[kind]
    def mapping(s, vec, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0)):
        mp = s.n('Mapping'); s.link(vec, mp.inputs['Vector'])
        mp.inputs['Scale'].default_value = scale; mp.inputs['Location'].default_value = loc; mp.inputs['Rotation'].default_value = rot
        return mp.outputs[0]
    def noise(s, vec, scale=5, detail=4, rough=0.55, dist=0.0, w=0.0):
        nz = s.n('TexNoise', noise_dimensions='4D' if w else '3D')
        if w: nz.inputs['W'].default_value = w
        nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
        nz.inputs['Roughness'].default_value = rough; nz.inputs['Distortion'].default_value = dist
        if vec is not None: s.link(vec, nz.inputs['Vector'])
        return nz.outputs['Fac']
    def voronoi(s, vec, scale=5, feature='F1', out='Distance', rnd=1.0):
        v = s.n('TexVoronoi', feature=feature); v.inputs['Scale'].default_value = scale
        v.inputs['Randomness'].default_value = rnd
        s.link(vec, v.inputs['Vector']); return v.outputs[out]
    def ramp(s, fac, stops, interp='LINEAR'):
        r = s.n('ValToRGB'); cr = r.color_ramp; cr.interpolation = interp
        while len(cr.elements) < len(stops): cr.elements.new(0.5)
        for e, (p, c) in zip(cr.elements, stops):
            e.position = p; e.color = srgb(c) if not (isinstance(c, tuple) and len(c) == 4) else c
        s.link(fac, r.inputs['Fac']); return r.outputs['Color']
    def fmap(s, fac, a, b, c=0, d=1, clamp=True):
        m = s.n('MapRange'); m.clamp = clamp
        s.link(fac, m.inputs['Value'])
        for k, v in zip(('From Min', 'From Max', 'To Min', 'To Max'), (a, b, c, d)): m.inputs[k].default_value = v
        return m.outputs[0]
    def mix(s, fac, a, b, blend='MIX'):
        mx = s.n('MixRGB', blend_type=blend)
        if isinstance(fac, (int, float)): mx.inputs['Fac'].default_value = fac
        else: s.link(fac, mx.inputs['Fac'])
        for i, v in ((1, a), (2, b)):
            if isinstance(v, tuple): mx.inputs[i].default_value = v if len(v) == 4 else srgb(v)
            else: s.link(v, mx.inputs[i])
        return mx.outputs[0]
    def math(s, op, a, b=None, clamp=False):
        m = s.n('Math', operation=op); m.use_clamp = clamp
        for i, v in ((0, a), (1, b)):
            if v is None: continue
            if isinstance(v, (int, float)): m.inputs[i].default_value = v
            else: s.link(v, m.inputs[i])
        return m.outputs[0]
    def bump(s, h, strength=0.5, dist=0.02, invert=False):
        b = s.n('Bump', invert=invert); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = dist
        s.link(h, b.inputs['Height']); return b.outputs[0]
    def sepz(s, vec):
        sp = s.n('SeparateXYZ'); s.link(vec, sp.inputs[0]); return sp.outputs
    def brick(s, vec, color1, color2, mortar, scale=1, bw=0.5, bh=0.25, ms=0.02, offset=0.5, bias=0.0):
        b = s.n('TexBrick'); b.offset = offset; b.offset_frequency = 2
        b.inputs['Color1'].default_value = srgb(color1) ; b.inputs['Color2'].default_value = srgb(color2)
        b.inputs['Mortar'].default_value = srgb(mortar)
        b.inputs['Scale'].default_value = scale; b.inputs['Mortar Size'].default_value = ms
        b.inputs['Mortar Smooth'].default_value = 0.1; b.inputs['Bias'].default_value = bias
        b.inputs['Brick Width'].default_value = bw; b.inputs['Row Height'].default_value = bh
        s.link(vec, b.inputs['Vector']); return b.outputs['Color'], b.outputs['Fac']
    def done(s, color=None, rough=None, bump=None, **kw):
        if color is not None: s.set('Base Color', color if not isinstance(color, str) else srgb(color))
        if rough is not None: s.set('Roughness', rough)
        if bump is not None: s.link(bump, s.bsdf.inputs['Normal'])
        for k, v in kw.items(): s.set(k.replace('_', ' '), v)
        return s.m

def M(key, fn):
    """memoised material"""
    if key not in MATS: MATS[key] = fn()
    return MATS[key]

# ------------------------------------------------------------------ geometry builder
class B:
    """Collects faces per material in WORLD coordinates (so Object-space textures are world-anchored)."""
    def __init__(s, name="obj"):
        s.name = name; s.bms = {}; s.mats = {}
    def bm(s, mat):
        k = mat.name
        if k not in s.bms:
            s.bms[k] = bmesh.new(); s.mats[k] = mat; s.bms[k].loops.layers.uv.new("UVMap")
        return s.bms[k]
    def face(s, mat, pts, uvs=None, smooth=False):
        bm = s.bm(mat)
        vs = [bm.verts.new(Vector(p)) for p in pts]
        try: f = bm.faces.new(vs)
        except ValueError: return None
        f.smooth = smooth
        uvl = bm.loops.layers.uv.active
        n = f.normal
        if uvs is None:
            if abs(n.z) > 0.999: u = Vector((1, 0, 0)); v = Vector((0, 1, 0))
            else:
                u = Vector((0, 0, 1)).cross(n).normalized(); v = n.cross(u)
            for l in f.loops: l[uvl].uv = (l.vert.co.dot(u), l.vert.co.dot(v))
        else:
            for l, uv in zip(f.loops, uvs): l[uvl].uv = uv
        return f
    def box(s, mat, c, size, z0=0.0, rot=0.0, mats=None, tilt=None):
        """box centred at XY=c, base at z0, size (sx,sy,sz), rotated rot (rad) about Z.  mats: optional dict face->material
        faces: 'x+','x-','y+','y-','z+','z-'"""
        sx, sy, sz = size
        rotm = Matrix.Rotation(rot, 3, 'Z')
        def P(x, y, z): 
            v = rotm @ Vector((x * sx / 2, y * sy / 2, 0)); return (c[0] + v.x, c[1] + v.y, z0 + z * sz)
        # unit cube corners
        co = {(a, b, d): P(a, b, d) for a in (-1, 1) for b in (-1, 1) for d in (0, 1)}
        mm = mats or {}
        g = lambda k: mm.get(k, mat)
        s.face(g('z-'), [co[(-1, -1, 0)], co[(-1, 1, 0)], co[(1, 1, 0)], co[(1, -1, 0)]])
        s.face(g('z+'), [co[(-1, -1, 1)], co[(1, -1, 1)], co[(1, 1, 1)], co[(-1, 1, 1)]])
        s.face(g('x+'), [co[(1, -1, 0)], co[(1, 1, 0)], co[(1, 1, 1)], co[(1, -1, 1)]])
        s.face(g('x-'), [co[(-1, 1, 0)], co[(-1, -1, 0)], co[(-1, -1, 1)], co[(-1, 1, 1)]])
        s.face(g('y+'), [co[(1, 1, 0)], co[(-1, 1, 0)], co[(-1, 1, 1)], co[(1, 1, 1)]])
        s.face(g('y-'), [co[(-1, -1, 0)], co[(1, -1, 0)], co[(1, -1, 1)], co[(-1, -1, 1)]])
    def beam(s, mat, p0, p1, w=0.02, h=None, up=(0, 0, 1)):
        """rectangular beam between 2 points with cross section w x h"""
        h = h or w
        a = Vector(p0); b = Vector(p1); d = (b - a)
        if d.length < 1e-6: return
        d.normalize(); u = Vector(up)
        if abs(d.dot(u)) > 0.99: u = Vector((1, 0, 0))
        r = d.cross(u).normalized(); u2 = r.cross(d).normalized()
        def ring(p): return [p + r * w / 2 + u2 * h / 2, p - r * w / 2 + u2 * h / 2, p - r * w / 2 - u2 * h / 2, p + r * w / 2 - u2 * h / 2]
        A = ring(a); Bq = ring(b)
        for i in range(4):
            j = (i + 1) % 4
            s.face(mat, [A[i], A[j], Bq[j], Bq[i]])
        s.face(mat, A[::-1]); s.face(mat, Bq)
    def cyl(s, mat, p0, p1, r0, r1=None, n=10, cap0=True, cap1=True, capmat=None, smooth=True):
        r1 = r0 if r1 is None else r1
        a = Vector(p0); b = Vector(p1); d = b - a
        if d.length < 1e-6: return
        dn = d.normalized(); ref = Vector((0, 0, 1)) if abs(dn.z) < 0.95 else Vector((1, 0, 0))
        u = dn.cross(ref).normalized(); v = dn.cross(u)
        cm = capmat or mat
        def pt(t, rr, k): 
            ang = 2 * math.pi * k / n; return (a if t == 0 else b) + (u * math.cos(ang) + v * math.sin(ang)) * rr
        for k in range(n):
            k2 = (k + 1) % n
            s.face(mat, [pt(0, r0, k), pt(0, r0, k2), pt(1, r1, k2), pt(1, r1, k)], smooth=smooth)
        for t, rr, flag, rev in ((0, r0, cap0, True), (1, r1, cap1, False)):
            if not flag: continue
            pts = [pt(t, rr, k) for k in range(n)]
            uvs = [(0.5 + 0.5 * math.cos(2 * math.pi * k / n), 0.5 + 0.5 * math.sin(2 * math.pi * k / n)) for k in range(n)]
            if rev: pts = pts[::-1]; uvs = uvs[::-1]
            s.face(cm, pts, uvs=uvs)
    def sphere(s, mat, c, r, seg=8, rings=6, scale=(1, 1, 1), rot=0.0, jitter=0.0, rng=None, smooth=True):
        c = Vector(c); rotm = Matrix.Rotation(rot, 3, 'Z')
        rr = rng or random
        def P(i, j):
            th = math.pi * j / rings; ph = 2 * math.pi * i / seg
            rj = 1 + (rr.uniform(-jitter, jitter) if jitter and 0 < j < rings else 0)
            v = Vector((math.sin(th) * math.cos(ph) * scale[0], math.sin(th) * math.sin(ph) * scale[1], math.cos(th) * scale[2])) * r * rj
            return c + rotm @ v
        grid = [[P(i, j) for j in range(rings + 1)] for i in range(seg)]
        for i in range(seg):
            i2 = (i + 1) % seg
            for j in range(rings):
                if j == 0: s.face(mat, [grid[i][0], grid[i][1], grid[i2][1]], smooth=smooth)
                elif j == rings - 1: s.face(mat, [grid[i][j], grid[i][j + 1], grid[i2][j]], smooth=smooth)
                else: s.face(mat, [grid[i][j], grid[i][j + 1], grid[i2][j + 1], grid[i2][j]], smooth=smooth)
    def prism_gable(s, mat_roof, mat_wall, c, size, z0, ridge_h, rot=0.0, overhang=(0.04, 0.05), mat_gable=None, thick=0.02, mat_edge=None):
        """Gable roof. size=(sx,sy) of walls; ridge runs along local X. Returns nothing."""
        sx, sy = size; ox, oy = overhang; rotm = Matrix.Rotation(rot, 3, 'Z')
        hx = sx / 2 + ox; hy = sy / 2 + oy
        def P(x, y, z): v = rotm @ Vector((x, y, 0)); return (c[0] + v.x, c[1] + v.y, z)
        e0 = z0 - 0.02; zr = z0 + ridge_h
        # eave z drops by slope*overhang
        slope = ridge_h / (sy / 2)
        ze = z0 - slope * oy * 0.9
        # slopes (outer)
        s.face(mat_roof, [P(-hx, -hy, ze), P(hx, -hy, ze), P(hx, 0, zr), P(-hx, 0, zr)])
        s.face(mat_roof, [P(hx, hy, ze), P(-hx, hy, ze), P(-hx, 0, zr), P(hx, 0, zr)])
        # underside / thickness
        t = thick
        s.face(mat_edge or mat_roof, [P(-hx, -hy, ze), P(-hx, 0, zr), P(-hx, 0, zr - t), P(-hx, -hy, ze - t)])
        s.face(mat_edge or mat_roof, [P(hx, -hy, ze - t), P(hx, 0, zr - t), P(hx, 0, zr), P(hx, -hy, ze)])
        s.face(mat_edge or mat_roof, [P(hx, hy, ze), P(hx, 0, zr), P(hx, 0, zr - t), P(hx, hy, ze - t)])
        s.face(mat_edge or mat_roof, [P(-hx, hy, ze - t), P(-hx, 0, zr - t), P(-hx, 0, zr), P(-hx, hy, ze)])
        s.face(mat_edge or mat_roof, [P(-hx, -hy, ze - t), P(hx, -hy, ze - t), P(hx, -hy, ze), P(-hx, -hy, ze)])
        s.face(mat_edge or mat_roof, [P(hx, hy, ze - t), P(-hx, hy, ze - t), P(-hx, hy, ze), P(hx, hy, ze)])
        # gable end triangles
        mg = mat_gable or mat_wall
        s.face(mg, [P(sx / 2, -sy / 2, z0), P(sx / 2, sy / 2, z0), P(sx / 2, 0, zr)])
        s.face(mg, [P(-sx / 2, sy / 2, z0), P(-sx / 2, -sy / 2, z0), P(-sx / 2, 0, zr)])
        # underside closure
        s.face(mat_edge or mat_roof, [P(-hx, -hy, ze - t), P(-hx, hy, ze - t), P(hx, hy, ze - t), P(hx, -hy, ze - t)][::-1])
    def commit(s, subsurf=False):
        objs = []
        for k, bm in s.bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            me = bpy.data.meshes.new(s.name + k); bm.to_mesh(me); bm.free()
            me.materials.append(s.mats[k])
            o = bpy.data.objects.new(s.name + k, me); bpy.context.collection.objects.link(o)
            objs.append(o)
        s.bms = {}
        return objs

def smooth_all(objs):
    for o in objs:
        for p in o.data.polygons: p.use_smooth = True

# ------------------------------------------------------------------ rendering
def add_catcher(cx, cy, size=10, mat=None):
    me = bpy.data.meshes.new("catcher")
    h = size / 2
    me.from_pydata([(cx - h, cy - h, 0), (cx + h, cy - h, 0), (cx + h, cy + h, 0), (cx - h, cy + h, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("catcher", me); bpy.context.collection.objects.link(o)
    o.is_shadow_catcher = True
    if mat: me.materials.append(mat)
    return o

def render_png(path, w, h, samples, seed=0):
    sc = bpy.context.scene
    sc.cycles.samples = samples; sc.cycles.seed = seed
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

def sprite(name, build, fw=1, fh=1, W=None, H=None, samples=128, flat=False, catcher=True, catcher_mat=None,
           seed=0, always_diamond=True, cat_size=None, off=None, K=1.0, **extra):
    """Render one raw sprite (+meta json); post.py crops/downsamples. build(ctr) called after scene reset."""
    import json
    ctr = (fw / 2, -fh / 2)             # footprint centre in Blender coords
    S = (fw, -fh, 0)                    # south corner of footprint: game (fw,fh) -> blender (fw,-fh)
    big = fw > 1 or fh > 1
    W = W or (1040 if big else 560); H = H or (1120 if big else 640)
    off = (H // 2 - 110) if off is None else off
    W += W % 2; H += H % 2
    reset()
    setup_render(samples, W, H)
    make_camera(S, W, H, off)
    if catcher: add_catcher(ctr[0] + 0.8, ctr[1] - 0.3, cat_size or (14 if fw > 1 else 12), catcher_mat)
    build(ctr)
    if K != 1.0:
        for o in list(bpy.data.objects):
            if o.type == 'MESH' and o.name != 'catcher':
                o.matrix_world = Matrix.Translation((ctr[0], ctr[1], 0)) @ Matrix.Scale(K, 4) @ Matrix.Translation((-ctr[0], -ctr[1], 0))
    os.makedirs(os.path.join(WORK, "raw"), exist_ok=True)
    tmp = os.path.join(WORK, "raw", name + ".png")
    render_png(tmp, W, H, samples, seed)
    json.dump(dict(name=name, fw=fw, fh=fh, W=W, H=H, flat=flat, diamond=always_diamond, off=off, **extra), open(os.path.join(WORK, "raw", name + ".json"), "w"))
    print("RAW", name, flush=True)

def args():
    argv = sys.argv
    return argv[argv.index('--') + 1:] if '--' in argv else []
