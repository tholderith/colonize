"""Blender helpers for 'Pre-rendered 98': 90s-raytracer look = hard sun + flat ambient, no GI, plasticky specular,
simple procedural textures, Standard view transform. Game tile (gx,gy) -> Blender (X=gx, Y=-gy)."""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("R98WORK", "/tmp/retro98_work"); os.makedirs(WORK + "/raw", exist_ok=True)
SS = 2                                      # render at 2x the half-res (=final) size, Lanczos down to half-res
SCALE = 32 * SS * math.sqrt(2)              # px per ortho unit: 1 tile = 64px wide diamond at SS*half-res... (half-res 64 wide)
SCALE = 32 * SS * math.sqrt(2) * 1.0        # cos45*SCALE = half tile width (32 half-px * SS)
ZPX = SCALE * math.cos(math.radians(30))    # px per unit height
SUN = Vector((-0.55, -0.83, 0)).normalized()

def lin(h):
    if isinstance(h, str):
        h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    else: c = list(h[:3])
    return [(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) for v in c]
def hexmul(h, f):
    h = h.lstrip('#'); c = [min(255, int(int(h[i:i+2], 16) * f)) for i in (0, 2, 4)]
    return '#%02x%02x%02x' % tuple(c)

def reset(samples=48, W=300, H=400, ambient=0.8, sunE=3.9):
    bpy.ops.wm.read_factory_settings(use_empty=True); MATS.clear()
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; cy = sc.cycles
    cy.device = 'CPU'; cy.samples = samples; cy.use_denoising = False; cy.use_adaptive_sampling = False
    cy.max_bounces = 2; cy.diffuse_bounces = 1; cy.glossy_bounces = 2; cy.transmission_bounces = 0; cy.transparent_max_bounces = 4
    cy.sample_clamp_indirect = 2.0; cy.blur_glossy = 0.3
    sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True; sc.render.filter_size = 1.0
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.display_settings.display_device = 'sRGB'
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (*lin((0.62, 0.74, 0.95)), 1); bg.inputs['Strength'].default_value = ambient
    ld = bpy.data.lights.new("sun", 'SUN'); ld.energy = sunE; ld.angle = math.radians(0.6); ld.color = (1.0, 0.95, 0.84)
    d = SUN * math.cos(math.radians(50)); d.z = math.sin(math.radians(50))
    o = bpy.data.objects.new("sun", ld); bpy.context.collection.objects.link(o); o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

def camera(target, W, H, off):
    cam = bpy.data.cameras.new("cam"); cam.type = 'ORTHO'; cam.ortho_scale = max(W, H) / SCALE; cam.clip_start = 0.1; cam.clip_end = 200
    o = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(o)
    o.rotation_euler = Euler((math.radians(60), 0, math.radians(45)), 'XYZ')
    m = o.rotation_euler.to_matrix(); fwd = m @ Vector((0, 0, -1)); up = m @ Vector((0, 1, 0))
    o.location = Vector(target) + up * (off / SCALE) - fwd * 60
    bpy.context.scene.camera = o

# ---------------------------------------------------------------- materials
MATS = {}
def mat(col, kind='flat', rough=0.5, spec=0.3, scale=1.0, var=0.25, col2=None, name=None, emit=0.0):
    key = (col, kind, rough, spec, scale, var, col2)
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new(name or f"m{len(MATS)}"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); b = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
    def N(t, **kw):
        n = nt.nodes.new('ShaderNode' + t)
        for k, v in kw.items():
            if k in n.inputs: n.inputs[k].default_value = v
            else: setattr(n, k, v)
        return n
    def L(a, b_): nt.links.new(a, b_)
    c1 = (*lin(col), 1); c2 = (*lin(col2 or hexmul(col, 0.72)), 1)
    uv = N('TexCoord').outputs['UV']; ob = N('TexCoord').outputs['Object']
    if kind == 'flat': b.inputs['Base Color'].default_value = c1
    else:
        if kind == 'noise':
            f = N('TexNoise', Scale=6 / scale, Detail=4, Roughness=0.6); L(ob, f.inputs['Vector']); fac = f.outputs['Fac']
            r = N('ValToRGB'); r.color_ramp.elements[0].position = 0.35; r.color_ramp.elements[1].position = 0.65
            r.color_ramp.elements[0].color = c2; r.color_ramp.elements[1].color = c1; L(fac, r.inputs['Fac']); L(r.outputs[0], b.inputs['Base Color'])
        elif kind in ('brick', 'tile'):
            t = N('TexBrick', offset=0.5, offset_frequency=2, squash=1.0)
            bw, bh = (0.16, 0.07) if kind == 'brick' else (0.12, 0.085)
            t.inputs['Scale'].default_value = 1 / scale; t.inputs['Brick Width'].default_value = bw * 1.0; t.inputs['Row Height'].default_value = bh
            t.inputs['Mortar Size'].default_value = 0.012 if kind == 'brick' else 0.006; t.inputs['Mortar Smooth'].default_value = 0.0
            t.inputs['Color1'].default_value = c1; t.inputs['Color2'].default_value = c2
            t.inputs['Mortar'].default_value = (*lin('#c9c0a8'), 1) if kind == 'brick' else (*lin(hexmul(col, 0.35)), 1)
            t.inputs['Bias'].default_value = 0.0
            L(uv, t.inputs['Vector']); L(t.outputs['Color'], b.inputs['Base Color'])
        elif kind == 'plank':
            t = N('TexWave', wave_type='BANDS', bands_direction='X', wave_profile='SAW', Scale=11 / scale, Distortion=1.2, Detail=2)
            L(uv, t.inputs['Vector']); r = N('ValToRGB'); r.color_ramp.elements[0].color = c2; r.color_ramp.elements[1].color = c1
            r.color_ramp.elements[0].position = 0.1; r.color_ramp.elements[1].position = 0.95
            L(t.outputs['Fac'], r.inputs['Fac']); L(r.outputs[0], b.inputs['Base Color'])
        elif kind == 'rows':   # horizontal rows (thatch / hay / crops)
            t = N('TexWave', wave_type='BANDS', bands_direction='Y', wave_profile='SAW', Scale=14 / scale, Distortion=3.0, Detail=3)
            L(uv, t.inputs['Vector']); r = N('ValToRGB'); r.color_ramp.elements[0].color = c2; r.color_ramp.elements[1].color = c1
            r.color_ramp.elements[0].position = 0.0; r.color_ramp.elements[1].position = 1.0
            L(t.outputs['Fac'], r.inputs['Fac']); L(r.outputs[0], b.inputs['Base Color'])
        elif kind == 'stone':
            t = N('TexVoronoi', Scale=7 / scale); L(ob, t.inputs['Vector'])
            r = N('ValToRGB'); r.color_ramp.elements[0].position = 0.04; r.color_ramp.elements[1].position = 0.2
            r.color_ramp.elements[0].color = (*lin(hexmul(col, 0.4)), 1); r.color_ramp.elements[1].color = c1
            nz = N('TexNoise', Scale=9 / scale, Detail=2); L(ob, nz.inputs['Vector'])
            mx = N('MixRGB', blend_type='MULTIPLY'); mx.inputs['Fac'].default_value = var
            mx.inputs[2].default_value = c2
            L(t.outputs['Distance'], r.inputs['Fac']); L(r.outputs[0], mx.inputs[1]); L(nz.outputs['Fac'], mx.inputs['Fac'])
            L(mx.outputs[0], b.inputs['Base Color'])
        elif kind == 'speck':
            t = N('TexNoise', Scale=40 / scale, Detail=1, Roughness=0.8); L(ob, t.inputs['Vector'])
            r = N('ValToRGB'); r.color_ramp.elements[0].position = 0.4; r.color_ramp.elements[1].position = 0.6
            r.color_ramp.elements[0].color = c2; r.color_ramp.elements[1].color = c1; L(t.outputs['Fac'], r.inputs['Fac']); L(r.outputs[0], b.inputs['Base Color'])
    if emit:
        b.inputs['Emission Color'].default_value = c1; b.inputs['Emission Strength'].default_value = emit
    MATS[key] = m; return m

# ---------------------------------------------------------------- geometry
class G:
    def __init__(s, name="o"): s.name = name; s.bms = {}; s.mats = {}
    def _bm(s, m):
        if m.name not in s.bms: s.bms[m.name] = bmesh.new(); s.mats[m.name] = m; s.bms[m.name].loops.layers.uv.new("UVMap")
        return s.bms[m.name]
    def face(s, m, pts, flip=False):
        bm = s._bm(m); pts = [Vector(p) for p in pts]
        if flip: pts = pts[::-1]
        try: f = bm.faces.new([bm.verts.new(p) for p in pts])
        except ValueError: return
        n = f.normal
        if abs(n.z) > 0.999: u = Vector((1, 0, 0)); v = Vector((0, 1, 0))
        else: u = Vector((0, 0, 1)).cross(n).normalized(); v = n.cross(u)
        uvl = bm.loops.layers.uv.active
        for l in f.loops: l[uvl].uv = (l.vert.co.dot(u), l.vert.co.dot(v))
    def box(s, m, c, size, z0=0, rot=0, mats=None, taper=1.0):
        sx, sy, sz = size; R = Matrix.Rotation(rot, 3, 'Z')
        def P(a, b, z, k=1.0):
            v = R @ Vector((a * sx / 2 * k, b * sy / 2 * k, 0)); return (c[0] + v.x, c[1] + v.y, z0 + z * sz)
        mm = mats or {}; g = lambda k: mm.get(k, m); t = taper
        s.face(g('z-'), [P(-1,-1,0), P(-1,1,0), P(1,1,0), P(1,-1,0)])
        s.face(g('z+'), [P(-1,-1,1,t), P(1,-1,1,t), P(1,1,1,t), P(-1,1,1,t)])
        s.face(g('x+'), [P(1,-1,0), P(1,1,0), P(1,1,1,t), P(1,-1,1,t)])
        s.face(g('x-'), [P(-1,1,0), P(-1,-1,0), P(-1,-1,1,t), P(-1,1,1,t)])
        s.face(g('y+'), [P(1,1,0), P(-1,1,0), P(-1,1,1,t), P(1,1,1,t)])
        s.face(g('y-'), [P(-1,-1,0), P(1,-1,0), P(1,-1,1,t), P(-1,-1,1,t)])
    def roof(s, mroof, mgable, c, size, z0, ridge, rot=0, ov=(0.05, 0.06), thick=0.025, medge=None):
        """gable roof, ridge along local x"""
        sx, sy = size; ox, oy = ov; R = Matrix.Rotation(rot, 3, 'Z'); hx = sx / 2 + ox; hy = sy / 2 + oy
        def P(x, y, z): v = R @ Vector((x, y, 0)); return (c[0] + v.x, c[1] + v.y, z)
        zr = z0 + ridge; slope = ridge / (sy / 2); ze = z0 - slope * oy; me = medge or mroof; t = thick
        s.face(mroof, [P(-hx,-hy,ze), P(hx,-hy,ze), P(hx,0,zr), P(-hx,0,zr)])
        s.face(mroof, [P(hx,hy,ze), P(-hx,hy,ze), P(-hx,0,zr), P(hx,0,zr)])
        s.face(me, [P(-hx,-hy,ze), P(-hx,0,zr), P(-hx,0,zr-t), P(-hx,-hy,ze-t)])
        s.face(me, [P(hx,-hy,ze-t), P(hx,0,zr-t), P(hx,0,zr), P(hx,-hy,ze)])
        s.face(me, [P(hx,hy,ze), P(hx,0,zr), P(hx,0,zr-t), P(hx,hy,ze-t)])
        s.face(me, [P(-hx,hy,ze-t), P(-hx,0,zr-t), P(-hx,0,zr), P(-hx,hy,ze)])
        s.face(me, [P(-hx,-hy,ze-t), P(hx,-hy,ze-t), P(hx,-hy,ze), P(-hx,-hy,ze)])
        s.face(me, [P(hx,hy,ze-t), P(-hx,hy,ze-t), P(-hx,hy,ze), P(hx,hy,ze)])
        s.face(mgable, [P(sx/2,-sy/2,z0), P(sx/2,sy/2,z0), P(sx/2,0,zr)])
        s.face(mgable, [P(-sx/2,sy/2,z0), P(-sx/2,-sy/2,z0), P(-sx/2,0,zr)])
    def hip(s, m, c, size, z0, h, rot=0, ov=0.05, top=0.0):
        """pyramid / hip roof (square-ish), optional flat top fraction"""
        sx, sy = size; R = Matrix.Rotation(rot, 3, 'Z'); hx = sx / 2 + ov; hy = sy / 2 + ov
        def P(x, y, z): v = R @ Vector((x, y, 0)); return (c[0] + v.x, c[1] + v.y, z)
        a, b = hx * top, hy * top; zt = z0 + h
        q = [(-hx,-hy,z0 - ov * h / (sy / 2)), (hx,-hy,z0 - ov * h / (sy / 2)), (hx,hy,z0 - ov * h / (sy / 2)), (-hx,hy,z0 - ov * h / (sy / 2))]
        t = [(-a,-b,zt), (a,-b,zt), (a,b,zt), (-a,b,zt)]
        for i in range(4):
            j = (i + 1) % 4; s.face(m, [P(*q[i]), P(*q[j]), P(*t[j]), P(*t[i])])
        if top > 0: s.face(m, [P(*p) for p in t])
    def cyl(s, m, p0, p1, r0, r1=None, n=12, cap=True, smooth=True):
        r1 = r0 if r1 is None else r1; a = Vector(p0); b = Vector(p1); d = b - a
        dn = d.normalized(); ref = Vector((0, 0, 1)) if abs(dn.z) < .95 else Vector((1, 0, 0)); u = dn.cross(ref).normalized(); v = dn.cross(u)
        pt = lambda t, r, k: (a if t == 0 else b) + (u * math.cos(2 * math.pi * k / n) + v * math.sin(2 * math.pi * k / n)) * r
        for k in range(n):
            k2 = (k + 1) % n; s.face(m, [pt(0, r0, k), pt(0, r0, k2), pt(1, r1, k2), pt(1, r1, k)])
        if cap:
            s.face(m, [pt(0, r0, k) for k in range(n)][::-1]); 
            if r1 > 0: s.face(m, [pt(1, r1, k) for k in range(n)])
    def sph(s, m, c, r, seg=9, rings=6, sc=(1, 1, 1), jit=0.0, rng=None):
        rr = rng or random; c = Vector(c)
        def P(i, j):
            th = math.pi * j / rings; ph = 2 * math.pi * i / seg; jj = 1 + (rr.uniform(-jit, jit) if 0 < j < rings else 0)
            return c + Vector((math.sin(th) * math.cos(ph) * sc[0], math.sin(th) * math.sin(ph) * sc[1], math.cos(th) * sc[2])) * r * jj
        grid = [[P(i, j) for j in range(rings + 1)] for i in range(seg)]
        for i in range(seg):
            i2 = (i + 1) % seg
            for j in range(rings):
                if j == 0: s.face(m, [grid[i][0], grid[i][1], grid[i2][1]])
                elif j == rings - 1: s.face(m, [grid[i][j], grid[i][j+1], grid[i2][j]])
                else: s.face(m, [grid[i][j], grid[i][j+1], grid[i2][j+1], grid[i2][j]])
    def beam(s, m, p0, p1, w=0.02, h=None):
        h = h or w; a = Vector(p0); b = Vector(p1); d = (b - a)
        if d.length < 1e-6: return
        d.normalize(); u = Vector((0, 0, 1))
        if abs(d.dot(u)) > .99: u = Vector((1, 0, 0))
        r = d.cross(u).normalized(); u2 = r.cross(d).normalized()
        ring = lambda p: [p + r * w / 2 + u2 * h / 2, p - r * w / 2 + u2 * h / 2, p - r * w / 2 - u2 * h / 2, p + r * w / 2 - u2 * h / 2]
        A = ring(a); B = ring(b)
        for i in range(4): j = (i + 1) % 4; s.face(m, [A[i], A[j], B[j], B[i]])
        s.face(m, A[::-1]); s.face(m, B)
    def commit(s, smooth=False):
        for k, bm in s.bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            me = bpy.data.meshes.new(s.name + k); bm.to_mesh(me); bm.free(); me.materials.append(s.mats[k])
            if smooth:
                for p in me.polygons: p.use_smooth = True
            o = bpy.data.objects.new(s.name + k, me); bpy.context.collection.objects.link(o)
        s.bms = {}

def catcher(cx, cy, size):
    h = size / 2; me = bpy.data.meshes.new("catcher")
    me.from_pydata([(cx-h, cy-h, 0), (cx+h, cy-h, 0), (cx+h, cy+h, 0), (cx-h, cy+h, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("catcher", me); bpy.context.collection.objects.link(o); o.is_shadow_catcher = True; return o

def render_sprite(name, build, fw=1, fh=1, W=300, H=420, off=None, samples=48, shadow_col=None, flat=False, shadow=True, K=1.0, **extra):
    """two renders: (A) object only (colour+alpha), (B) with shadow catcher (alpha = shadow strength). post.py combines."""
    off = (H // 2 - 70) if off is None else off
    for variant in (('obj', 'shd') if shadow else ('obj',)):
        reset(samples if variant == 'obj' else max(16, samples // 2), W, H)
        camera((fw, -fh, 0), W, H, off)
        build((fw / 2, -fh / 2))
        if K != 1.0:
            cx_, cy_ = fw / 2, -fh / 2
            for o in list(bpy.data.objects):
                if o.type == 'MESH': o.matrix_world = Matrix.Translation((cx_, cy_, 0)) @ Matrix.Scale(K, 4) @ Matrix.Translation((-cx_, -cy_, 0))
        for o in list(bpy.data.objects):
            if o.type == 'MESH' and o.name == 'catcher': pass
        if variant == 'shd': catcher(fw / 2 + .8, -fh / 2 - .3, 8 if fw > 1 else 6)
        bpy.context.scene.render.filepath = f"{WORK}/raw/{name}_{variant}.png"
        bpy.ops.render.render(write_still=True)
    json.dump(dict(name=name, shadow=shadow, fw=fw, fh=fh, W=W, H=H, off=off, flat=flat, shadow_col=shadow_col, **extra), open(f"{WORK}/raw/{name}.json", "w"))
    print("RENDERED", name, flush=True)
