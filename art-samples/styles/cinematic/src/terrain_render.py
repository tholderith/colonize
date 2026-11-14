"""Cinematic style - step 2 (Blender/Cycles): ONE continuous terrain mesh + water, rendered with the exact game camera.
Output: $CWORK/raw/terrain.png (3840x2160, 2x supersampled; post.py downsamples to 1920x1080)."""
import sys, os, json, array, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

FD = os.path.join(WORK, 'fields')
info = json.load(open(os.path.join(FD, 'info.json')))
X0, N, V, nv, DMAX = info['X0'], info['N'], info['V'], info['nv'], info['DMAX']
SPP = int(os.environ.get('TSPP', '96'))
W2, H2 = 1920 * SS, 1080 * SS

reset()
setup_render(SPP, W2, H2)
sc = bpy.context.scene
sc.render.film_transparent = False
sc.cycles.sample_clamp_direct = 12.0
sc.cycles.sample_clamp_indirect = 2.5
sc.cycles.max_bounces = int(os.environ.get('TMB','6')); sc.cycles.diffuse_bounces = int(os.environ.get('TDB','3')); sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = int(os.environ.get('TTB','12'))
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02; sc.cycles.adaptive_min_samples = 24
# camera: centre of the 1920x1080 frame is the ground point gx=gy=9.5625  (sx=960, sy=540)
c = 9.5625
make_camera((c, -c, 0), W2, H2, 0)

hs = array.array('f'); hs.fromfile(open(os.path.join(FD, 'height.f32'), 'rb'), nv * nv)

def load(name, nc=False):
    im = bpy.data.images.load(os.path.join(FD, name)); im.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
    im.alpha_mode = 'NONE'; return im

# ---------------------------------------------------------------- terrain mesh
verts = []; uvs = []
for j in range(nv):
    gy = X0 + j / V
    for i in range(nv):
        gx = X0 + i / V
        verts.append((gx, -gy, hs[j * nv + i]))
faces = []
for j in range(nv - 1):
    for i in range(nv - 1):
        a = j * nv + i
        faces.append((a, a + 1, a + nv + 1, a + nv))
me = bpy.data.meshes.new('terrain'); me.from_pydata(verts, [], faces)
for p in me.polygons: p.use_smooth = True
uv = me.uv_layers.new(name='UVMap')
for li, loop in enumerate(me.loops):
    vi = loop.vertex_index; i = vi % nv; j = vi // nv
    uv.data[li].uv = (i / (nv - 1) * (nv - 1) / V / N, 1 - j / V / N)
terr = bpy.data.objects.new('terrain', me); bpy.context.collection.objects.link(terr)

# land / seabed shader
mb = MB('ground'); co = mb.coord('Object'); uvc = mb.coord('UV')
colt = mb.n('TexImage'); colt.image = load('color.png'); colt.interpolation = 'Cubic'; colt.extension = 'EXTEND'
mb.link(uvc, colt.inputs['Vector'])
wett = mb.n('TexImage'); wett.image = load('wet.png', True); wett.extension = 'EXTEND'; mb.link(uvc, wett.inputs['Vector'])
wet = wett.outputs['Color']
wetv = mb.sepz(wet)['X'] if False else mb.n('SeparateColor')
mb.link(wet, wetv.inputs[0]); wetf = wetv.outputs[0]
base = mb.mix(wetf, colt.outputs['Color'], (0.8, 0.8, 0.8, 1))     # wet sand darkening handled in the albedo; keep tint
bump = mb.bump(mb.math('ADD', mb.noise(co, 70, 4, 0.6), mb.math('MULTIPLY', mb.noise(co, 9, 3, 0.5), 0.6)), 0.5, 0.02)
mb.set('Base Color', colt.outputs['Color'])
mb.set('Roughness', mb.fmap(wetf, 0, 1, 0.9, 0.38))
mb.link(bump, mb.bsdf.inputs['Normal'])
mb.set('Specular IOR Level', 0.25)
terr.data.materials.append(mb.m)

# ---------------------------------------------------------------- water plane (alpha from depth, colour ramp, foam, ripples)
ext = 70.0
wme = bpy.data.meshes.new('water')
x0, x1 = X0, X0 + N
wme.from_pydata([(x0, -x0, 0), (x1, -x0, 0), (x1, -x1, 0), (x0, -x1, 0)], [], [(0, 1, 2, 3)])
wuv = wme.uv_layers.new(name='UVMap')
for li, (u, v) in enumerate([(0, 1), (1, 1), (1, 0), (0, 0)]): wuv.data[li].uv = (u, v)
wat = bpy.data.objects.new('water', wme); bpy.context.collection.objects.link(wat)
# apron: huge flat quad around so the deep sea reaches every edge
aq = bpy.data.meshes.new('apron')
E_ = x1 = X0 + N
vv = [(-ext, ext), (ext, ext), (ext, -ext), (-ext, -ext), (x0, -x0), (x1, -x0), (x1, -x1), (x0, -x1)]
aq.from_pydata([(a, b, 0) for a, b in vv], [], [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
auv = aq.uv_layers.new(name='UVMap')
for li in range(len(aq.loops)): auv.data[li].uv = (0.5, 0.5)
apr = bpy.data.objects.new('apron', aq); bpy.context.collection.objects.link(apr)

def water_mat(name, inside=True):
    m = MB(name); co = m.coord('Object'); uvc = m.coord('UV')
    dt = m.n('TexImage'); dt.image = load('depth.png', True); dt.extension = 'EXTEND'; m.link(uvc, dt.inputs['Vector'])
    ft = m.n('TexImage'); ft.image = load('foam.png', True); ft.extension = 'EXTEND'; m.link(uvc, ft.inputs['Vector'])
    ds = m.n('SeparateColor'); m.link(dt.outputs['Color'], ds.inputs[0]); dep = m.math('MULTIPLY', ds.outputs[0], DMAX)
    fs = m.n('SeparateColor'); m.link(ft.outputs['Color'], fs.inputs[0]); foam = fs.outputs[0]
    if not inside:
        dep = m.math('ADD', 3.0, 0.0)
        foam = m.math('MULTIPLY', foam, 0.0)
    # big swells tint
    sw = m.noise(m.mapping(co, (0.35, 0.35, 0.35)), 1.0, 3, 0.5, 0.3)
    dd = m.math('ADD', dep, m.math('MULTIPLY', m.math('SUBTRACT', sw, 0.5), 0.35))
    colr = m.ramp(dd, [(0.00, (0.26, 0.80, 0.70)), (0.30, (0.08, 0.66, 0.68)), (0.9, (0.06, 0.50, 0.60)), (1.8, (0.03, 0.34, 0.47)), (3.0, (0.02, 0.22, 0.34))], 'LINEAR')
    kk = float(os.environ.get('TK', '3.2'))
    alpha = m.math('SUBTRACT', 1.0, m.math('POWER', 2.71828, m.math('MULTIPLY', dep, -kk)))
    alpha = m.math('MAXIMUM', m.math('MULTIPLY', alpha, 0.985), 0.0)
    if inside:
        ct = m.n('TexImage'); ct.image = load('color.png'); ct.extension = 'EXTEND'; m.link(uvc, ct.inputs['Vector'])
        bed = m.mix(0.0, (0.55, 0.75, 0.78, 1), (0.55, 0.75, 0.78, 1)) if False else None
        bedc = m.n('MixRGB', blend_type='MULTIPLY'); bedc.inputs['Fac'].default_value = 1.0; m.link(ct.outputs['Color'], bedc.inputs[1]); bedc.inputs[2].default_value = (0.36, 0.70, 0.70, 1)
        a2 = m.math('ADD', m.math('MULTIPLY', alpha, 0.72), 0.22)
        seen = m.mix(a2, bedc.outputs[0], colr)
    else:
        seen = colr
    foam = m.math('MULTIPLY', foam, 0.78)
    seen = m.mix(foam, seen, (0.97, 0.97, 0.93, 1))
    # ripples: two stretched noise layers -> bump
    r1 = m.noise(m.mapping(co, (1.4, 1.4, 1.4)), 1.0, 3, 0.5)
    r2 = m.noise(m.mapping(co, (7, 3.2, 7), rot=(0, 0, 0.7)), 1.0, 2, 0.5)
    ripple = m.math('ADD', r1, m.math('MULTIPLY', r2, 0.5))
    bmp = m.bump(ripple, 0.30, 0.2) if not os.environ.get('NOBUMP') else None
    bs = m.bsdf
    bs.inputs['Roughness'].default_value = 0.10
    m.set('Base Color', seen)
    m.set('Roughness', m.fmap(foam, 0, 1, 0.10, 0.6))
    m.set('Specular IOR Level', 0.9); m.set('IOR', 1.333)
    m.set('Subsurface Weight', 0.0)
    if bmp is not None: m.link(bmp, bs.inputs['Normal'])
    m.set('Emission Color', seen); m.set('Emission Strength', 0.22)
    m.nt.links.new(bs.outputs[0], m.out.inputs[0])
    return m.m
wat.data.materials.append(water_mat('water'))
apr.data.materials.append(water_mat('apron', inside=False))

# ---------------------------------------------------------------- render
os.makedirs(os.path.join(WORK, 'raw'), exist_ok=True)
sc.render.filepath = os.path.join(WORK, 'raw', os.environ.get('TNAME', 'terrain') + '.png')
sc.render.image_settings.color_mode = 'RGB'
if os.environ.get('TCROP'):    # quick test crop: x0,y0,x1,y1 in 1x pixels
    a, b, c_, d_ = [int(v) for v in os.environ['TCROP'].split(',')]
    sc.render.use_border = True; sc.render.use_crop_to_border = False
    sc.render.border_min_x = a / 1920; sc.render.border_max_x = c_ / 1920
    sc.render.border_min_y = 1 - d_ / 1080; sc.render.border_max_y = 1 - b / 1080
import time; t = time.time()
bpy.ops.render.render(write_still=True)
print('TERRAIN RENDER SECONDS', time.time() - t)
