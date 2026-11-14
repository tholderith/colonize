import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

N = 16; OV = 0.06
TEX = os.path.join(WORK, "tex")

def terrain_mat(typ, k):
    key = f"{typ}_{k}"
    mb = MB(key)
    c = bpy.data.images.load(os.path.join(TEX, f"{typ}_{k}_c.png")); c.colorspace_settings.name = 'sRGB'
    h = bpy.data.images.load(os.path.join(TEX, f"{typ}_{k}_h.png")); h.colorspace_settings.name = 'Non-Color'
    uv = mb.coord('UV')
    tc = mb.n('TexImage', image=c, interpolation='Cubic', extension='EXTEND')
    mb.link(uv, tc.inputs['Vector'])
    th = mb.n('TexImage', image=h, interpolation='Cubic', extension='EXTEND')
    mb.link(uv, th.inputs['Vector'])
    H = th.outputs['Color']
    P = {  # roughness, bump strength, bump dist
        'grass': (0.92, 1.0, 0.0045), 'sand': (0.95, 1.0, 0.004), 'road': (0.93, 1.0, 0.006),
        'deep': (0.10, 1.0, 0.030), 'shallow': (0.14, 1.0, 0.012)}[typ]
    bump = mb.bump(H, P[1], P[2])
    mb.bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
    mb.link(tc.outputs['Color'], mb.bsdf.inputs['Base Color'])
    mb.set('Roughness', P[0]); mb.link(bump, mb.bsdf.inputs['Normal'])
    mb.bsdf.inputs['Specular IOR Level'].default_value = 0.5
    if typ in ('deep', 'shallow'):
        mb.set('IOR', 1.333); mb.bsdf.inputs['Specular IOR Level'].default_value = 0.55
    if typ == 'sand':
        mb.bsdf.inputs['Specular IOR Level'].default_value = 0.25
    return mb.m

def build_tile(typ, k):
    def build(ctr):
        me = bpy.data.meshes.new("tile"); bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
        h = 0.5 + OV; cx, cy = 0.5, -0.5
        vs = [bm.verts.new((cx + sx * h, cy + sy * h, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = bm.faces.new(vs)
        for l, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uvl].uv = uv
        bm.to_mesh(me); bm.free()
        me.materials.append(terrain_mat(typ, k))
        o = bpy.data.objects.new("tile", me); bpy.context.collection.objects.link(o)
    return build

if __name__ == '__main__':
    a = args(); types = a[0].split(',') if a else ['grass', 'sand', 'road', 'deep', 'shallow']
    ks = range(N) if len(a) < 2 else [int(v) for v in a[1].split(',')]
    spp = int(os.environ.get("TSPP", "64"))
    for typ in types:
        for k in ks:
            sprite(f"{typ}_{k}", build_tile(typ, k), 1, 1, W=320, H=340, off=0, samples=spp, catcher=False, terrain=True, seed=k * 17 + 3)
