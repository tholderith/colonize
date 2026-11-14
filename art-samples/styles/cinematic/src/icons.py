"""Resource icons rendered in Blender/Cycles (procedural), 128x128 RGBA each -> $CWORK/icons/*.png"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import mats as MT
from wb import W

SPP = int(os.environ.get('ISPP', '48'))
SZ = 256
OUTD = os.path.join(WORK, 'icons'); os.makedirs(OUTD, exist_ok=True)

def gold_mat():
    mb = MB('gold'); co = mb.coord('Object')
    mb.set('Base Color', srgb((0.95, 0.70, 0.22))); mb.set('Metallic', 1.0); mb.set('Roughness', 0.28)
    return mb.m
def mat_col(name, c, rough=0.5, metal=0.0): return MT.solid(name, c, rough, metal)

def ringed_end(name='endgrain'):
    def mk():
        mb = MB(name); g = mb.coord('Object')
        # concentric rings around Z axis of the object-space? use world radial from log axis not available -> use Wave
        wv = mb.n('TexWave', wave_type='RINGS', rings_direction='Z'); wv.inputs['Scale'].default_value = 28; wv.inputs['Distortion'].default_value = 1.2
        mb.link(g, wv.inputs['Vector'])
        col = mb.ramp(wv.outputs['Fac'], [(0.0, (0.80, 0.62, 0.40)), (1.0, (0.55, 0.38, 0.22))])
        return mb.done(col, 0.8)
    return M(name, mk)

def build(kind, w):
    rng = random.Random(4)
    if kind == 'gold':
        g = gold_mat()
        for (cx, cy, n) in ((-0.22, -0.1, 4), (0.20, -0.14, 3), (0.0, 0.2, 5)):
            for k in range(n):
                w.cyl(g, (cx, cy, 0.05 * k), (cx, cy, 0.05 * k + 0.045), 0.20, 0.20, 28)
                w.cyl(g, (cx, cy, 0.05 * k + 0.044), (cx, cy, 0.05 * k + 0.052), 0.165, 0.165, 28, capmat=g)
        w.cyl(g, (0.45, 0.3, 0.0), (0.45, 0.3, 0.04), 0.13, 0.13, 20) if False else None
    elif kind == 'wood':
        bk = MT.bark((0.30, 0.20, 0.13)); end = ringed_end()
        def log(x, z, r=0.17, L=0.62):
            w.cyl(bk, (x, -L / 2, z), (x, L / 2, z), r, r, 18, cap0=True, cap1=False, capmat=end)
            w.cyl(bk, (x, L / 2 - 0.001, z), (x, L / 2, z), r * 0.98, r * 0.98, 18, cap0=False, cap1=True, capmat=end)
        for i in range(3): log(-0.34 + i * 0.34, 0.17)
        for i in range(2): log(-0.17 + i * 0.34, 0.17 + 0.29)
        log(0.0, 0.17 + 0.58 - 0.0, 0.15) if False else None
    elif kind == 'bricks':
        bm = MT.solid('brickred', (0.62, 0.22, 0.12), 0.85)
        bm2 = MT.solid('brickred2', (0.72, 0.30, 0.16), 0.85)
        for row in range(3):
            for i in range(2 if row % 2 == 0 else 2):
                x = -0.22 + i * 0.44 + (0.11 if row % 2 else 0.0)
                w.box(bm if (row + i) % 2 else bm2, x, 0.0, (0.40, 0.20, 0.12), row * 0.125, rot=rng.uniform(-0.03, 0.03))
        w.box(bm2, 0.0, 0.0, (0.40, 0.20, 0.12), 0.375, rot=0.05)
    elif kind == 'tools':
        wood = MT.solid('handle', (0.45, 0.30, 0.17), 0.7); steel = MT.solid('steel', (0.62, 0.64, 0.68), 0.35, 1.0)
        def tool(rot, head):
            ctr = (0, 0, 0.1)
            a = rot
            ux, uy = math.cos(a), math.sin(a)
            w.beam(wood, (-ux * 0.5, -uy * 0.5, 0.1), (ux * 0.5, uy * 0.5, 0.1), 0.07, 0.07)
            hx, hy = ux * 0.36, uy * 0.36
            if head == 'hammer':
                w.box(steel, hx, hy, (0.30, 0.13, 0.13), 0.035, rot=a + math.pi / 2)
            else:
                # pick: curved double-pointed head
                for t in (-1, 0, 1):
                    pass
                w.box(steel, hx, hy, (0.50, 0.07, 0.08), 0.06, rot=a + math.pi / 2)
                for s in (-1, 1):
                    px = hx + (-uy) * s * 0.28; py = hy + ux * s * 0.28
                    w.box(steel, px, py, (0.12, 0.05, 0.06), 0.04, rot=a + math.pi / 2 + s * 0.4)
        tool(math.radians(40), 'hammer'); tool(math.radians(140), 'pick')
    elif kind == 'food':
        stalk = MT.solid('stalk', (0.72, 0.58, 0.28), 0.6); grainm = MT.solid('grain', (0.88, 0.70, 0.28), 0.5)
        tie = MT.solid('tie', (0.55, 0.28, 0.20), 0.8)
        n = 15
        for i in range(n):
            a = (i / n) * 2 * math.pi + rng.uniform(-0.2, 0.2); sp = 0.05 + 0.20 * (i % 3) / 2
            bx, by = 0.05 * math.cos(a), 0.05 * math.sin(a)
            tx, ty, tz = bx + sp * 1.2 * math.cos(a), by + sp * 1.2 * math.sin(a), 0.78 + 0.1 * rng.random()
            w.cyl(stalk, (bx, by, 0.0), (tx, ty, tz), 0.012, 0.008, 5)
            for k in range(7):
                t = k / 6.0; px = tx + (bx - tx) * 0.0 + 0.0;
                for s in (-1, 1):
                    gx = tx - sp * 0.0 + s * 0.017 * -math.sin(a); gy = ty + s * 0.017 * math.cos(a)
                    w.sphere(grainm, (gx, gy, tz - k * 0.045), 0.024, seg=6, rings=4, scale=(1, 1, 1.9))
        w.cyl(tie, (0, 0, 0.25), (0, 0, 0.31), 0.085, 0.085, 14, cap0=False, cap1=False)
    elif kind == 'cloth':
        cols = [(0.28, 0.40, 0.62), (0.82, 0.70, 0.50), (0.60, 0.22, 0.20)]
        for i, c in enumerate(cols):
            cm = MT.cloth('bolt%d' % i, c, 0.03, 0.0)
            z = 0.17 + i * 0.30
            w.cyl(cm, (0, -0.38, z), (0, 0.38, z), 0.15, 0.15, 24, cap0=True, cap1=True)
            w.cyl(MT.solid('core%d' % i, (0.75, 0.62, 0.42), 0.8), (0, 0.38, z), (0, 0.395, z), 0.16, 0.16, 24, capmat=MT.solid('cap%d' % i, (0.84, 0.72, 0.52), 0.8))
            # flap hanging off
            w.box(cm, 0.0, -0.40, (0.01, 0.0, 0.0) if False else (0.0001, 0.0001, 0.0001), 0)
    elif kind == 'pop':
        skin = MT.solid('skin', (0.85, 0.66, 0.50), 0.6); coat = MT.solid('coat1', (0.62, 0.50, 0.34), 0.75); coat2 = MT.solid('coat2', (0.34, 0.42, 0.56), 0.75)
        hat = MT.solid('hat', (0.20, 0.15, 0.11), 0.8)
        for (x, y, s, cm) in ((-0.16, 0.0, 1.0, coat), (0.30, 0.22, 0.82, coat2)):
            w.sphere(cm, (x, y, 0.28 * s), 0.30 * s, seg=14, rings=10, scale=(1, 0.85, 1.05))
            w.sphere(skin, (x, y, 0.70 * s), 0.17 * s, seg=14, rings=10)
            w.cyl(hat, (x, y, 0.80 * s), (x, y, 0.86 * s), 0.23 * s, 0.22 * s, 18)
            w.cyl(hat, (x, y, 0.86 * s), (x, y, 1.0 * s), 0.13 * s, 0.12 * s, 18)

def render(kind, tilt=0):
    reset(); setup_render(SPP, SZ * 2, SZ * 2, light=False)
    sc = bpy.context.scene
    wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True; bg = wd.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.75, 0.82, 0.95, 1); bg.inputs[1].default_value = 1.1
    make_sun(strength=4.2, elev=48)
    cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.ortho_scale = 1.5
    o = bpy.data.objects.new('c', cam); bpy.context.collection.objects.link(o)
    o.rotation_euler = Euler((math.radians(58), 0, math.radians(30)), 'XYZ')
    fwd = o.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    ctr = Vector((0, 0, 0.35 if kind not in ('food', 'pop') else 0.45))
    o.location = ctr - fwd * 20; sc.camera = o
    w = W((0, 0), kind); build(kind, w); objs = w.commit()
    for ob in objs:
        for p in ob.data.polygons: p.use_smooth = True
    # catcher plane for soft contact shadow
    add_catcher(0, 0, 6)
    sc.render.filepath = os.path.join(OUTD, kind + '.png'); bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    for k in ('gold', 'wood', 'bricks', 'tools', 'food', 'cloth', 'pop'):
        render(k); print('ICON', k, flush=True)
