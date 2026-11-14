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
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((w.cx + cx + sx * rx, w.cy + cy + sy * ry, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs); bm.to_mesh(me); bm.free()
    me.materials.append(MT.dirt_decal(name, color, inner))
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.visible_shadow = False
    return o
