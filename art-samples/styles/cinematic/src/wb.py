"""World-builder wrapper: coordinates relative to the footprint centre."""
from common import *
import mats as MT

class W:
    def __init__(s, ctr, name='o'):
        s.b = B(name); s.cx, s.cy = ctr
    def P(s, x, y, z=0): return (s.cx + x, s.cy + y, z)
    def box(s, mat, x, y, size, z0=0.0, rot=0.0, mats=None): s.b.box(mat, (s.cx + x, s.cy + y), size, z0, rot, mats)
    def beam(s, mat, p0, p1, w=0.02, h=None, up=(0, 0, 1)): s.b.beam(mat, s.P(*p0), s.P(*p1), w, h, up)
    def cyl(s, mat, p0, p1, r0, r1=None, n=10, **k): s.b.cyl(mat, s.P(*p0), s.P(*p1), r0, r1, n, **k)
    def sphere(s, mat, c, r, **k): s.b.sphere(mat, s.P(*c), r, **k)
    def face(s, mat, pts, **k): s.b.face(mat, [s.P(*p) for p in pts], **k)
    def gable(s, rm, wm, x, y, size, z0, rh, rot=0.0, **k): s.b.prism_gable(rm, wm, (s.cx + x, s.cy + y), size, z0, rh, rot, **k)
    def commit(s): return s.b.commit()

FACES = {'x+': ((1, 0), (0, 1)), 'x-': ((-1, 0), (0, -1)), 'y+': ((0, 1), (-1, 0)), 'y-': ((0, -1), (1, 0))}

def fb(w, mat, face, wall, along, z0, ww, hh, d, out0=0.0):
    """box on a wall: face ('x+'..), wall = wall plane coordinate (signed), along = coordinate along tangent, outward offset out0"""
    n, t = FACES[face]
    cx = n[0] * (abs(wall) + out0 + d / 2) * (1 if (n[0] > 0 or n[1] > 0) else 1)
    # wall plane is at 'wall' (signed); outward unit n
    px = (wall + n[0] * (out0 + d / 2)) if n[0] else along
    py = (wall + n[1] * (out0 + d / 2)) if n[1] else along
    size = (d, ww) if n[0] else (ww, d)
    w.box(mat, px, py, (size[0], size[1], hh), z0)

def window(w, face, wall, along, zc, ww=0.085, wh=0.10, shutters=True, frame=None, glass=None, shut=None, sill=True, warm=0.0):
    frame = frame or MT.painted('winframe', (0.55, 0.52, 0.46)); glass = glass or MT.glass('glass', warm)
    z0 = zc - wh / 2; fw = 0.012
    fb(w, glass, face, wall, along, z0, ww, wh, 0.006, 0.0)
    fb(w, frame, face, wall, along - ww / 2 - fw / 2, z0 - fw, fw, wh + 2 * fw, 0.014)
    fb(w, frame, face, wall, along + ww / 2 + fw / 2, z0 - fw, fw, wh + 2 * fw, 0.014)
    fb(w, frame, face, wall, along, z0 - fw, ww, fw, 0.014)
    fb(w, frame, face, wall, along, z0 + wh, ww, fw, 0.014)
    fb(w, frame, face, wall, along, zc - 0.003, ww, 0.006, 0.012)       # transom
    fb(w, frame, face, wall, along - 0.003, z0, 0.006, wh, 0.012)      # mullion
    if sill: fb(w, MT.masonry('sill', True), face, wall, along, z0 - 0.022, ww + 0.04, 0.012, 0.03)
    if shutters:
        shut = shut or MT.painted('shutter', (0.30, 0.40, 0.32))
        for sg in (-1, 1):
            fb(w, shut, face, wall, along + sg * (ww / 2 + fw + ww / 4 + 0.002), z0 - 0.004, ww / 2 - 0.004, wh + 0.008, 0.008)

def door(w, face, wall, along, dw=0.12, dh=0.235, mat=None, frame=None, z0=0.0):
    mat = mat or MT.planks((0.30, 0.20, 0.13), True, 0.03, 'door')
    frame = frame or MT.timber()
    fw = 0.018
    fb(w, MT.solid('doorhole', (0.02, 0.015, 0.01), 1.0), face, wall, along, z0, dw, dh, 0.004, 0.0)
    fb(w, mat, face, wall, along, z0 + 0.003, dw - 0.012, dh - 0.01, 0.008, 0.0)
    fb(w, frame, face, wall, along - dw / 2 - fw / 2, z0, fw, dh + fw, 0.02)
    fb(w, frame, face, wall, along + dw / 2 + fw / 2, z0, fw, dh + fw, 0.02)
    fb(w, frame, face, wall, along, z0 + dh, dw + 2 * fw, fw, 0.02)
    # stone step
    fb(w, MT.masonry('step', True), face, wall, along, 0.0, dw + 0.06, 0.012, 0.05)
    # iron handle
    fb(w, MT.iron(), face, wall, along + dw * 0.3, z0 + dh * 0.45, 0.01, 0.01, 0.014, 0.003)

def barrel(w, x, y, z0=0.0, r=0.028, h=0.06, wood=None, n=10):
    wood = wood or MT.planks((0.42, 0.30, 0.18), True, 0.02, 'barrelwood')
    w.cyl(wood, (x, y, z0), (x, y, z0 + h), r * 0.92, r * 0.92, n, capmat=wood)
    w.cyl(wood, (x, y, z0 + h * 0.2), (x, y, z0 + h * 0.8), r, r, n, cap0=False, cap1=False)
    for zz in (0.18, 0.5, 0.82):
        w.cyl(MT.iron(), (x, y, z0 + h * zz - 0.002), (x, y, z0 + h * zz + 0.002), r * 1.01 if zz == 0.5 else r * 0.96, None, n, cap0=False, cap1=False)

def crate(w, x, y, s=0.04, z0=0.0, rot=0.0):
    w.box(MT.planks((0.40, 0.31, 0.20), False, 0.02, 'crate'), x, y, (s, s, s * 0.85), z0, rot)

def yard(w, rx, ry, color=(0.38, 0.30, 0.21), z=0.0015, name='yard', cx=0, cy=0, inner=0.5):
    return None   # ground darkening/dirt is baked into the continuous underlay
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((w.cx + cx + sx * rx, w.cy + cy + sy * ry, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs); bm.to_mesh(me); bm.free()
    me.materials.append(MT.dirt_decal(name, color, inner))
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.visible_shadow = False
    return o

# ------------------------------------------------------------------ small life props (cinematic additions)
def flower_box(w, face, wall, along, zc, wh=0.10, ww=0.095, seed=0, shades=((0.82, 0.22, 0.16), (0.95, 0.80, 0.25), (0.92, 0.88, 0.85))):
    rng = random.Random(seed)
    wood = MT.painted('fbox', (0.30, 0.22, 0.15))
    z0 = zc - wh / 2 - 0.038
    fb(w, wood, face, wall, along, z0, ww + 0.02, 0.026, 0.034, 0.002)
    n, t = FACES[face]
    leaf = MT.solid('fleaf', (0.18, 0.36, 0.12), 0.8)
    for k in range(7):
        a = along + (k - 3) * (ww / 7.0) * 1.2
        px = (wall + n[0] * 0.030) if n[0] else a
        py = (wall + n[1] * 0.030) if n[1] else a
        w.sphere(leaf, (px, py, z0 + 0.034), 0.016, seg=6, rings=4, scale=(1, 1, 0.8), rng=rng)
        c = shades[(k + seed) % len(shades)]
        w.sphere(MT.solid('fl%s' % (c,), c, 0.6), (px + n[0] * 0.004, py + n[1] * 0.004, z0 + 0.048 + rng.uniform(0, 0.008)), 0.009, seg=5, rings=3)

def laundry(w, x0, y0, x1, y1, z=0.20, seed=0):
    rng = random.Random(seed)
    post = MT.timber((0.25, 0.19, 0.13))
    for (x, y) in ((x0, y0), (x1, y1)): w.cyl(post, (x, y, 0.0), (x, y, z + 0.02), 0.007, 0.006, 6)
    w.cyl(MT.rope(), (x0, y0, z + 0.015), (x1, y1, z + 0.015), 0.0025, 0.0025, 4)
    cols = [(0.92, 0.90, 0.84), (0.30, 0.42, 0.62), (0.78, 0.30, 0.22), (0.88, 0.80, 0.55), (0.92, 0.90, 0.84)]
    dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); ang = math.atan2(dy, dx)
    for k in range(4):
        t = (k + 0.7) / 4.4
        cx, cy = x0 + dx * t, y0 + dy * t
        hh = rng.uniform(0.055, 0.085)
        w.box(MT.solid('lau%d' % k, cols[(k + seed) % 5], 0.95), cx, cy, (L / 4 * 0.62, 0.003, hh), z + 0.012 - hh, rot=ang)

def haystack(w, x, y, r=0.085):
    hay = MT.thatch()
    w.sphere(hay, (x, y, r * 0.62), r, seg=12, rings=8, scale=(1, 1, 1.15), smooth=True)
    w.cyl(hay, (x, y, 0.0), (x, y, r * 0.6), r * 0.97, r, 12, cap0=False, cap1=False)
    w.cyl(MT.solid('hayrope', (0.30, 0.22, 0.12), 0.9), (x, y, r * 0.4), (x, y, r * 0.43), r * 1.01, r * 1.01, 12, cap0=False, cap1=False)

def fence(w, x0, y0, x1, y1, h=0.05, n=None, wood=None):
    wood = wood or MT.timber((0.31, 0.24, 0.17), 'fencewood')
    L = math.hypot(x1 - x0, y1 - y0); n = n or max(2, int(L / 0.07))
    for i in range(n + 1):
        t = i / n; x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
        w.box(wood, x, y, (0.012, 0.012, h), 0.0)
    for z in (h * 0.45, h * 0.8):
        w.beam(wood, (x0, y0, z), (x1, y1, z), 0.008, 0.008)
