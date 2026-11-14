"""Resource icons (Blender, run via build.sh icons): one small rendered object per good, 3/4 ortho view, rim-lit, transparent bg.
Rendered at 256 px (WORK/icon_<good>.png); icons_post.py downsizes to 64 (<good>@2x.png) and 32 (<good>.png) in public/assets/ui/icons/."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from models import M, G
IC = os.path.join(OUT, "ui", "icons"); R = 256
def P(a, b, z=0.0, ang=math.radians(45)):   # screen-plane (right, up) coords -> Blender XYZ (right vector = (cos45, sin45))
    return (a * math.cos(ang), a * math.sin(ang), z + b)
def Mc(c, **k): return M(c, rust=0.0, soot=0.0, rough=k.pop('rough', 0.45), metal=k.pop('metal', 0.1), **k)

def credits():
    b = B('cr'); gold = Mc('#f2b830', metal=0.8, rough=0.3); dk = Mc('#9a6a10', metal=0.7, rough=0.35)
    for i in range(3): b.cyl(gold, (0, 0, 0.02 + i * 0.17), (0, 0, 0.17 + i * 0.17), 0.46, n=24, smooth=True); b.cyl(dk, (0, 0, 0.12 + i * 0.17), (0, 0, 0.16 + i * 0.17), 0.465, n=24)
    b.cyl(dk, (0, 0, 0.535), (0, 0, 0.55), 0.34, n=24); b.cyl(G('cyan', 7), (0, 0, 0.55), (0, 0, 0.57), 0.2, n=6)
    b.commit()
def biomass():
    b = B('bio'); tray = Mc('#3a4148', metal=0.5); rnd = random.Random(2)
    b.box(tray, (0, 0), (1.0, 0.75, 0.16), 0.0, rot=math.radians(0)); b.box(Mc('#1c2a1c'), (0, 0), (0.88, 0.63, 0.04), 0.14)
    for _ in range(14):
        x = rnd.uniform(-0.38, 0.38); y = rnd.uniform(-0.25, 0.25); b.sphere(Mc('#5fd13a', rough=0.7), (x, y, 0.24), rnd.uniform(0.09, 0.15), seg=8, rings=5, scale=(1, 1, 0.8))
    for _ in range(5): b.sphere(G('green', 4), (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.2, 0.2), 0.32), 0.03, seg=6, rings=4)
    b.commit()
def rations():
    b = B('rat'); pk = Mc('#d9b374', rough=0.7); st = Mc('#e8541c', rough=0.5)
    b.box(pk, (0, 0), (0.78, 0.52, 0.3), 0.0, rot=math.radians(20)); b.box(st, (0, 0), (0.8, 0.2, 0.31), 0.0, rot=math.radians(20))
    b.box(pk, (0.05, 0.02), (0.7, 0.46, 0.26), 0.3, rot=math.radians(-12)); b.box(Mc('#9ee06a'), (0.05, 0.02), (0.72, 0.16, 0.27), 0.3, rot=math.radians(-12))
    b.box(G('amber', 5), (0.05, 0.02), (0.3, 0.3, 0.02), 0.56, rot=math.radians(-12)); b.commit()
def scrap():
    b = B('scr'); rnd = random.Random(7); cols = ['#9aa2aa', '#c0622c', '#70787f', '#d98a3c']
    for i in range(11):
        a = rnd.uniform(0, 6.28); r = rnd.uniform(0, 0.32); z = 0.1 + 0.3 * (1 - r / 0.4) * rnd.uniform(0.3, 1)
        b.box(Mc(cols[i % 4], metal=0.6, rough=0.6), (r * math.cos(a), r * math.sin(a)), (rnd.uniform(0.28, 0.46), rnd.uniform(0.18, 0.34), rnd.uniform(0.12, 0.24)), z - 0.1, rot=rnd.uniform(0, 3))
    b.beam(Mc('#8d939a', metal=0.8), (-0.45, -0.1, 0.05), (0.1, 0.1, 0.68), 0.07); b.cyl(Mc('#55606a'), (0.3, -0.3, 0.02), (0.3, -0.3, 0.12), 0.2, n=12)
    b.sphere(G('hot', 8), (0.05, 0.12, 0.42), 0.07, seg=6, rings=4); b.commit()
def alloy():
    b = B('all'); m = Mc('#a9c4e0', metal=0.35, rough=0.3); top = Mc('#ffffff', metal=0.9, rough=0.2)
    def ingot(c, z, rot):
        x, y = c; L, W, H = 0.62, 0.3, 0.2; t = 0.06; R_ = Matrix.Rotation(rot, 3, 'Z')
        def p(a, b_, h, s): v = R_ @ Vector((a * (L / 2 - s), b_ * (W / 2 - s), 0)); return (x + v.x, y + v.y, z + h)
        lo = [p(-1, -1, 0, 0), p(1, -1, 0, 0), p(1, 1, 0, 0), p(-1, 1, 0, 0)]; hi = [p(-1, -1, H, t), p(1, -1, H, t), p(1, 1, H, t), p(-1, 1, H, t)]
        b.loft(m, [lo, hi])
    for i, y in enumerate((-0.32, 0, 0.32)): ingot((0, y - 0.0), 0.0, 0)
    for y in (-0.16, 0.16): ingot((0, y), 0.2, 0)
    ingot((0, 0), 0.4, 0); b.sphere(G('cyan', 3), (0, 0, 0.64), 0.03, seg=6, rings=4); b.commit()
def algae():
    b = B('alg'); b.cyl(G('cyan', 1.6), (0, 0, 0.1), (0, 0, 0.7), 0.26, n=20, caps=True)
    b.cyl(Mc('#8affd8', rough=0.1), (0, 0, 0.08), (0, 0, 0.13), 0.29, n=20); b.cyl(Mc('#2d343b', metal=0.6), (0, 0, 0.7), (0, 0, 0.88), 0.2, n=16)
    b.cyl(Mc('#8affd8', rough=0.1), (0, 0, 0.66), (0, 0, 0.72), 0.29, n=20)
    b.cyl(G('green', 6), (0, 0, 0.14), (0, 0, 0.5), 0.2, n=16); b.cyl(Mc('#c8fff0', rough=0.1), (0, 0, 0.5), (0, 0, 0.52), 0.265, n=20)
    rnd = random.Random(4)
    for _ in range(6): b.sphere(Mc('#d8fff4'), (rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), rnd.uniform(0.55, 0.62)), 0.035, seg=6, rings=4)
    b.commit()
def polymer():
    b = B('pol'); rnd = random.Random(3); bag = Mc('#b64ae0', rough=0.35, metal=0.0)
    b.sphere(bag, (0, 0, 0.3), 0.42, seg=14, rings=9, scale=(1.0, 0.8, 0.78)); b.sphere(Mc('#d58cf5', rough=0.3), (0, 0, 0.6), 0.2, seg=10, rings=6, scale=(0.9, 0.8, 0.8))
    b.cyl(Mc('#2d1a3a'), (0, 0, 0.62), (0, 0, 0.78), 0.07, 0.11, n=8); b.box(Mc('#ffe14d'), (0.32 * 0.7, -0.32 * 0.7), (0.02, 0.3, 0.2), 0.2, rot=-math.pi / 4)
    for _ in range(10):
        a = rnd.uniform(0, 6.28); r = rnd.uniform(0.38, 0.62); b.sphere(Mc('#e9b6ff', rough=0.2), (r * math.cos(a), r * math.sin(a), 0.05), 0.055, seg=6, rings=4)
    b.commit()
def goods():
    b = B('gd'); w = Mc('#e0a038', rough=0.6); dk = Mc('#6a3d12', rough=0.7)
    b.box(w, (0, 0), (0.8, 0.8, 0.7), 0.0)
    for s in (-1, 1):
        b.box(dk, (0, 0), (0.83, 0.1, 0.72), 0.0, rot=0) if False else None
    for a in (-0.3, 0.3):
        b.box(dk, (a, 0), (0.1, 0.84, 0.74), -0.01); b.box(dk, (0, a), (0.84, 0.1, 0.74), -0.01)
    b.box(Mc('#f0b84a'), (0, 0), (0.88, 0.88, 0.07), 0.66); b.box(G('cyan', 6), (0.405, 0), (0.012, 0.34, 0.2), 0.25); b.box(G('mag', 5), (0, -0.405), (0.3, 0.012, 0.2), 0.25)
    b.commit()
def laborers():
    b = B('lab'); coat = Mc('#f2c230', rough=0.5); dk = Mc('#b88a10', rough=0.5)
    b.cyl(coat, (0, 0, 0.02), (0, 0, 0.62), 0.34, 0.2, n=14); b.cyl(Mc('#2f3640'), (-0.08, 0, 0.0), (-0.08, 0, 0.12), 0.07, n=8)
    b.sphere(coat, (0, 0, 0.78), 0.23, seg=12, rings=8, scale=(1, 1, 1.0)); b.sphere(Mc('#d9a07a', rough=0.7), P(0.1, 0.0, 0.0, 0.0) if False else (0.1, -0.1, 0.77), 0.14, seg=10, rings=6)
    b.sphere(G('hot', 2), (0.19, -0.19, 0.77), 0.03, seg=6, rings=4); b.box(dk, (0, 0), (0.5, 0.06, 0.4), 0.2, rot=math.pi / 4); b.commit()
def technicians():
    b = B('tec'); coat = Mc('#2f6fd0', rough=0.5); w = Mc('#e9eef5', rough=0.4)
    b.cyl(coat, (0, 0, 0.02), (0, 0, 0.6), 0.3, 0.2, n=14); b.box(Mc('#1a2a44'), (0, 0), (0.4, 0.4, 0.06), 0.28)
    b.sphere(w, (0, 0, 0.78), 0.22, seg=12, rings=8)
    b.box(G('cyan', 9), (0.17, -0.17), (0.08, 0.3, 0.1), 0.76, rot=-math.pi / 4)
    b.box(Mc('#ff5a14'), (0, 0), (0.2, 0.2, 0.05), 0.99, rot=0.0); b.commit()
def power():
    b = B('pw'); pts = [(a * 0.62, bb * 0.62 - 0.05) for a, bb in [(0.0, 0.92), (-0.34, -0.02), (-0.04, -0.02), (-0.2, -0.92), (0.34, 0.16), (0.04, 0.16), (0.3, 0.92)]]
    for th, mat in ((0.1, G('amber', 3)), (-0.1, Mc('#7a3a10'))):
        b.face(mat, [P(a, bb + 0.5, 0, math.radians(45)) for a, bb in pts]) if th > 0 else None
    # extruded bolt: front/back plates + side walls along camera-facing normal (+x,-y)/sqrt2 toward camera
    n = Vector((0.707, -0.707, 0)) * 0.09; front = [Vector(P(a, bb + 0.5)) + n for a, bb in pts]; back = [Vector(P(a, bb + 0.5)) - n for a, bb in pts]
    b2 = B('pw2'); b2.face(G('amber', 3.5), front); b2.face(Mc('#6a3a10'), back[::-1])
    for i in range(len(pts)): j = (i + 1) % len(pts); b2.face(G('hot', 3), [front[i], back[i], back[j], front[j]])
    b2.commit()
ICONS = ['credits', 'biomass', 'rations', 'scrap', 'alloy', 'algae', 'polymer', 'goods', 'laborers', 'technicians', 'power']

if __name__ == '__main__':
    a = args(); names = a[0].split(',') if a else ICONS; spp = int(os.environ.get("NSPP", "40"))
    for n in names:
        reset(); setup_render(spp, R, R); make_camera((0, 0, 0.5), R, R, 0); bpy.context.scene.camera.data.ortho_scale = 1.45
        sun('rimstrong', (-0.6, 0.8, 0), 25, 3.5, (0.5, 0.85, 1.0), shadow=False, angle=3)
        bpy.context.scene.view_settings.view_transform = 'Standard'; bpy.context.scene.view_settings.look = 'None'; bpy.context.scene.view_settings.exposure = 0.0
        globals()[n]()
        tmp = os.path.join(WORK, 'icon_%s.png' % n); bpy.context.scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        print('ICON', n, flush=True)
