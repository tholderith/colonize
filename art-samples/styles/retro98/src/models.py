"""Original model library for 'Pre-rendered 98'. All builders take ctr=(x,y) of the footprint centre (Blender coords)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blib import *

class F:
    def __init__(s, c, rot=0.0): s.c = c; s.rot = rot; s.R = Matrix.Rotation(rot, 3, 'Z')
    def w(s, x, y, z=0):
        v = s.R @ Vector((x, y, 0)); return (s.c[0] + v.x, s.c[1] + v.y, z)
def M():
    d = dict(white=mat('#efe6d2', 'flat', .6, .2), glass=mat('#1d2740', 'flat', .15, .9), wood=mat('#7a4a28', 'plank', .5, .3, scale=1),
             dwood=mat('#4c2c1a', 'plank', .55, .25), trim=mat('#5a3a22', 'flat', .5, .3), stone=mat('#9a968c', 'stone', .6, .25, var=.5),
             gold=mat('#e0b030', 'flat', .25, .9), iron=mat('#2a2a30', 'flat', .4, .8), rope=mat('#b89a62', 'flat', .8, .1))
    return d
def window(g, f, side, t, z, sx, sy, w=.1, h=.14, frame=None, glass=None, shut=None):
    m = M(); frame = frame or m['white']; glass = glass or m['glass']
    if side in ('+y', '-y'):
        yy = (sy / 2 + .004) * (1 if side == '+y' else -1); g.box(frame, f.w(t, yy), (w + .03, .012, h + .03), z - .015, f.rot)
        g.box(glass, f.w(t, yy * 1.012), (w, .012, h), z, f.rot)
        if shut:
            for k in (-1, 1): g.box(shut, f.w(t + k * (w / 2 + .05), yy * 1.01), (.05, .012, h + .02), z - .01, f.rot)
    else:
        xx = (sx / 2 + .004) * (1 if side == '+x' else -1); g.box(frame, f.w(xx, t), (.012, w + .03, h + .03), z - .015, f.rot)
        g.box(glass, f.w(xx * 1.012, t), (.012, w, h), z, f.rot)
        if shut:
            for k in (-1, 1): g.box(shut, f.w(xx * 1.01, t + k * (w / 2 + .05)), (.012, .05, h + .02), z - .01, f.rot)
def door(g, f, side, t, sx, sy, mdoor, w=.12, h=.22):
    if side in ('+y', '-y'):
        yy = (sy / 2 + .005) * (1 if side == '+y' else -1); g.box(mdoor, f.w(t, yy), (w, .014, h), .03, f.rot)
    else:
        xx = (sx / 2 + .005) * (1 if side == '+x' else -1); g.box(mdoor, f.w(xx, t), (.014, w, h), .03, f.rot)
def barrel(g, c, r=.05, h=.09, col='#8a5a2e'):
    mw = mat(col, 'plank', .5, .4, scale=.6); mi = mat('#2a2a30', 'flat', .4, .8)
    g.cyl(mw, (c[0], c[1], 0), (c[0], c[1], h), r, r, 10); g.cyl(mw, (c[0], c[1], h * .3), (c[0], c[1], h * .7), r * 1.1, r * 1.1, 10, cap=False)
    for z in (.2, .78): g.cyl(mi, (c[0], c[1], h * z), (c[0], c[1], h * z + .012), r * 1.1, r * 1.1, 10, cap=False)
def crate(g, c, s=.08, rot=0, col='#a8743c'):
    g.box(mat(col, 'plank', .6, .3), c, (s, s, s), 0, rot)
def sack(g, c, r=.045, col='#d8c8a0'):
    g.sph(mat(col, 'noise', .9, .1, var=.1), (c[0], c[1], r * .8), r, 8, 5, (1, 1, .9))
def laundry(g, p0, p1, z=.3):
    m = M()
    for p in (p0, p1): g.cyl(m['trim'], (p[0], p[1], 0), (p[0], p[1], z + .03), .008, .008, 6)
    g.beam(m['rope'], (p0[0], p0[1], z), (p1[0], p1[1], z), .006)
    cols = ['#f0f0f0', '#c83030', '#3060c0', '#f0d040', '#f0f0f0']
    d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0)); L = d.length; d.normalize(); rot = math.atan2(d.y, d.x)
    for i, cc in enumerate(cols[:4]):
        t = (i + .6) / 4.6; q = (p0[0] + d.x * L * t, p0[1] + d.y * L * t)
        g.box(mat(cc, 'flat', .9, .05), q, (.07 if i % 2 else .05, .01, .09 if i != 2 else .06), z - (.09 if i != 2 else .06), rot)
def fence(g, p0, p1, h=.1, n=None, col='#8a6038'):
    m = mat(col, 'plank', .6, .2); d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0)); L = d.length; n = n or max(2, int(L / .09)); dn = d.normalized()
    for i in range(n + 1):
        q = (p0[0] + dn.x * L * i / n, p0[1] + dn.y * L * i / n); g.box(m, q, (.02, .02, h), 0, 0)
    for z in (.3, .7): g.beam(m, (p0[0], p0[1], h * z), (p1[0], p1[1], h * z), .014)

# ------------------------------------------------------------------ houses
HOUSES = [
  dict(wall='#f2e8d4', wk='noise', roof='#c8502c', rk='tile', sx=.62, sy=.46, wh=.26, rd=.26, rot=0, shut='#2c5aa8', chim=1, laundry=1),
  dict(wall='#e8b45c', wk='noise', roof='#7a8ca8', rk='tile', sx=.5, sy=.44, wh=.3, rd=.3, rot=math.pi / 2, shut='#a83030', chim=1, beams=1, bar=1),
  dict(wall='#ece2cc', wk='noise', roof='#c8a458', rk='rows', sx=.68, sy=.46, wh=.24, rd=.3, rot=0, shut='#2f7a50', chim=1, stone=1, flower=1),
  dict(wall='#d8d0c0', wk='brick', roof='#a8401c', rk='tile', sx=.46, sy=.42, wh=.42, rd=.26, rot=math.pi / 2, shut='#3a3a50', chim=1, floors=2),
]
def build_house(k):
    P = HOUSES[k]
    def build(ctr):
        g = G('h'); m = M(); f = F((ctr[0] - .02, ctr[1] + .05), P['rot']); sx, sy, wh, rd = P['sx'], P['sy'], P['wh'], P['rd']
        mw = mat(P['wall'], P['wk'], .75, .15, scale=1, var=.5, col2=hexmul(P['wall'], .82)); mr = mat(P['roof'], P['rk'], .5, .45, scale=1, col2=hexmul(P['roof'], .78))
        g.box(mat('#8a867c', 'stone', .7, .2), f.w(0, 0), (sx + .05, sy + .05, .045), 0, f.rot)
        if P.get('stone'): g.box(m['stone'], f.w(0, 0), (sx + .01, sy + .01, .1), .045, f.rot)
        g.box(mw, f.w(0, 0), (sx, sy, wh), .045, f.rot)
        z0 = .045 + wh; g.roof(mr, mw, f.c, (sx, sy), z0, rd, f.rot, (.06, .07), medge=mat(hexmul(P['roof'], .55), 'flat', .6, .2))
        # ridge cap
        g.box(mat(hexmul(P['roof'], .8), 'flat', .5, .5), f.w(0, 0), (sx + .12, .035, .03), z0 + rd - .005, f.rot)
        if P.get('beams'):
            for t in (-.2, 0, .2):
                g.box(m['dwood'], f.w(t, -sy / 2 - .003), (.025, .008, wh), .045, f.rot); g.box(m['dwood'], f.w(sx / 2 + .003, t * .8), (.008, .025, wh), .045, f.rot)
            g.box(m['dwood'], f.w(0, -sy / 2 - .003), (sx, .008, .025), .045 + wh * .5, f.rot)
        # windows / door
        shut = mat(P['shut'], 'flat', .6, .3); zf = [.13] if P.get('floors') != 2 else [.1, .3]
        for z in zf:
            window(g, f, '-y', sx * .27, .045 + z, sx, sy, shut=shut); window(g, f, '-y', -sx * .27, .045 + z, sx, sy, shut=shut) if z != zf[0] or P.get('floors') == 2 else None
            window(g, f, '+x', 0, .045 + z + (.0 if P.get('floors') == 2 else .02), sx, sy, shut=shut)
        door(g, f, '-y', 0 if P.get('floors') != 2 else -sx * .27, sx, sy, m['dwood']) if P.get('floors') == 2 else door(g, f, '-y', -sx * .12, sx, sy, m['dwood'])
        # gable attic window
        g.box(m['glass'], f.w(sx / 2 + .004, 0), (.012, .07, .08), z0 + .06, f.rot)
        if P.get('chim'):
            g.box(mat('#9a6a58', 'brick', .8, .1), f.w(-sx * .28, sy * .12), (.07, .07, rd * 1.1), z0 + .02, f.rot)
            g.box(mat('#3a2e2a', 'flat'), f.w(-sx * .28, sy * .12), (.085, .085, .02), z0 + .02 + rd * 1.1, f.rot)
        if P.get('flower'):
            g.box(m['wood'], f.w(sx * .27, -sy / 2 - .02), (.14, .03, .03), .045 + .1, f.rot)
            for i in range(4): g.sph(mat(['#e04050', '#f0e050', '#ff9ab0', '#ffffff'][i], 'flat'), f.w(sx * .27 - .05 + i * .033, -sy / 2 - .02, .045 + .15), .018, 5, 4)
        if P.get('laundry'): laundry(g, (ctr[0] + .32, ctr[1] - .05), (ctr[0] + .32, ctr[1] - .4), .27)
        if P.get('bar'): barrel(g, (ctr[0] + .36, ctr[1] - .3)); barrel(g, (ctr[0] + .36, ctr[1] - .4), .045, .08)
        if k == 2: crate(g, (ctr[0] + .38, ctr[1] - .3), .09, .3); sack(g, (ctr[0] + .33, ctr[1] - .4))
        if k == 3: g.box(m['wood'], f.w(0, -sy / 2 - .035), (.09, .05, .012), .045 + .02, f.rot)
        g.commit(smooth=False)
    return build

def build_farmhouse(ctr):
    g = G('f'); m = M(); f = F((ctr[0] - .05, ctr[1] + .05), 0)
    mw = mat('#f0e2c0', 'noise', .8, .1, col2='#d6c4a0'); mr = mat('#b0462a', 'tile', .5, .4, col2='#8a3420'); mb = mat('#8a5a34', 'plank', .7, .2)
    g.box(mat('#8a867c', 'stone', .7), f.w(0, 0), (.82, .5, .045), 0)
    g.box(mw, f.w(.0, 0), (.8, .44, .27), .045); g.roof(mr, mw, f.c, (.8, .44), .315, .3, 0, (.07, .08), medge=mat('#5a2418', 'flat'))
    g.box(mb, f.w(.62, .0), (.38, .42, .2), 0); g.roof(mat('#c8a458', 'rows', .9, .1, col2='#a08040'), mb, f.w(.62, 0), (.38, .42), .2, .16, 0, (.04, .06))
    for t in (-.22, .08): window(g, f, '-y', t, .15, .8, .44, shut=mat('#2f7a50', 'flat'))
    door(g, f, '-y', .28, .8, .44, m['dwood'], .13, .21)
    g.box(m['dwood'], (f.c[0] + .62, f.c[1] - .212, .0), (.2, .012, .15), 0)   # barn door
    g.box(mat('#9a6a58', 'brick', .8), f.w(-.26, .1), (.08, .08, .4), .3)
    # haystack + fence + barrels
    mh = mat('#e8c048', 'rows', .9, .08, col2='#b88c20', scale=.5)
    g.cyl(mh, (ctr[0] + .32, ctr[1] - .33, 0), (ctr[0] + .32, ctr[1] - .33, .13), .13, .1, 12); g.cyl(mh, (ctr[0] + .32, ctr[1] - .33, .13), (ctr[0] + .32, ctr[1] - .33, .24), .1, 0, 12)
    fence(g, (ctr[0] - .45, ctr[1] - .43), (ctr[0] + .05, ctr[1] - .43)); barrel(g, (ctr[0] - .3, ctr[1] - .33))
    g.commit()

def build_lumber(ctr):
    g = G('l'); m = M(); f = F((ctr[0] - .12, ctr[1] + .12), 0)
    mw = mat('#8a5a32', 'plank', .7, .15, scale=.9); mr = mat('#6a4a2a', 'rows', .9, .1, col2='#4a321c', scale=.8)
    g.box(mw, f.w(0, 0), (.5, .38, .24), 0); g.roof(mr, mw, f.c, (.5, .38), .24, .2, 0, (.06, .07), medge=m['dwood'])
    window(g, f, '-y', .14, .09, .5, .38, .09, .11, m['dwood']); door(g, f, '-y', -.12, .5, .38, m['dwood'], .12, .19)
    g.box(mat('#8a867c', 'stone', .7), f.w(-.18, .1), (.07, .07, .4), .2)
    # log pile (stack of horizontal logs along Y)
    ml = mat('#9a6a3a', 'noise', .7, .1, scale=.3, col2='#6a4426'); mend = mat('#e0b878', 'flat', .8, .1)
    for i, (a, z) in enumerate([(0, .03), (1, .03), (2, .03), (3, .03), (.5, .085), (1.5, .085), (2.5, .085), (1, .14), (2, .14), (1.5, .19)]):
        x0 = ctr[0] + .28 + (a - 1.5) * .0; yy = ctr[1] - .02 - a * .075
        g.cyl(ml, (ctr[0] + .22, yy, z), (ctr[0] + .22 + .0, yy, z), .035, .035, 8, cap=False) if False else None
        g.cyl(ml, (ctr[0] + .14, yy, z + .0), (ctr[0] + .42, yy, z), .036, .036, 8, cap=False); 
        g.face(mend, [(ctr[0] + .42 + .0005, yy + math.cos(2 * math.pi * k / 8) * .035, z + math.sin(2 * math.pi * k / 8) * .035) for k in range(8)])
    # stump + axe, sawhorse, loose logs
    g.cyl(mat('#a87a48', 'noise', .8, col2='#7a5430', scale=.3), (ctr[0] + .18, ctr[1] - .4, 0), (ctr[0] + .18, ctr[1] - .4, .08), .06, .065, 10)
    g.cyl(mend, (ctr[0] + .18, ctr[1] - .4, .081), (ctr[0] + .18, ctr[1] - .4, .082), .058, .058, 10)
    g.beam(m['dwood'], (ctr[0] + .16, ctr[1] - .4, .1), (ctr[0] + .08, ctr[1] - .38, .17), .012); g.box(m['iron'], (ctr[0] + .17, ctr[1] - .4), (.03, .015, .035), .09, .5)
    g.cyl(ml, (ctr[0] - .05, ctr[1] - .47, .03), (ctr[0] + .08, ctr[1] - .43, .03), .03, .03, 8)
    g.commit()

def build_chapel(ctr):
    g = G('c'); m = M(); f = F((ctr[0] - .12, ctr[1] + .05), 0)
    mw = mat('#ece6d8', 'stone', .7, .15, scale=1.3, var=.25, col2='#c9c2b0'); mr = mat('#5a6e8c', 'tile', .45, .5, col2='#44586f')
    g.box(mat('#8a867c', 'stone', .7), f.w(0, 0), (1.18, .7, .06), 0)
    g.box(mw, f.w(-.12, 0), (.96, .6, .32), .06); g.roof(mr, mw, f.w(-.12, 0), (.96, .6), .38, .34, 0, (.07, .09), medge=mat('#33445c', 'flat'))
    # apse-like buttresses & tall windows
    arch = mat('#2a3a60', 'flat', .2, .9); fr = mat('#f0eadc', 'flat')
    for t in (-.3, -.1, .1, .3): 
        window(g, f, '-y', t - .12 + .0, .14, 1.18 - .22, .6, .07, .2, fr, arch)
        g.box(mw, f.w(t - .12 + .05, -.33), (.04, .06, .28), .06, 0)
    # tower (front, +x)
    tc = f.w(.58, 0); g.box(mw, tc, (.4, .4, .62), .06); g.box(mat('#d9d0bc', 'stone', .7, col2='#b0a890'), tc, (.43, .43, .05), .6)
    g.hip(mat('#3f5878', 'tile', .4, .6, col2='#2e4460'), tc, (.4, .4), .68, .5, 0, .04)
    # belfry opening and clock
    g.box(arch, (tc[0] + .2, tc[1], 0), (.012, .15, .2), .42); g.box(arch, (tc[0], tc[1] - .2, 0), (.15, .012, .2), .42)
    g.box(m['gold'], (tc[0] + .202, tc[1], 0), (.01, .12, .12), .45 + .0 * 0) if False else None
    g.cyl(m['gold'], (tc[0] + .205, tc[1], .26), (tc[0] + .21, tc[1], .26), .05, .05, 12)
    g.cyl(m['gold'], (tc[0], tc[1] - .205, .26), (tc[0], tc[1] - .21, .26), .05, .05, 12) if False else None
    # door
    g.box(mat('#4a2c1a', 'plank'), (tc[0] + .201, tc[1], 0), (.012, .14, .22), .06); g.box(fr, (tc[0] + .199, tc[1], 0), (.012, .18, .06), .28)
    # spire + cross
    g.cyl(m['gold'], (tc[0], tc[1], 1.18), (tc[0], tc[1], 1.34), .01, .01, 6); g.box(m['gold'], (tc[0], tc[1], 0), (.012, .08, .015), 1.28, 0); g.box(m['gold'], (tc[0], tc[1], 0), (.08, .012, .015), 1.28, 0) if False else None
    # churchyard wall + gravestones
    ms = mat('#a8a296', 'stone', .7, col2='#7a766a', scale=.5)
    g.box(ms, (ctr[0] + .75, ctr[1] - .3), (.03, .8, .07), 0); g.box(ms, (ctr[0] - .1, ctr[1] - .7), (1.4, .03, .07), 0, 0)
    for i, (x, y) in enumerate([(.28, -.52), (.5, -.55), (.0, -.5), (.62, -.2)]):
        g.box(mat('#bdb8aa', 'flat', .7), (ctr[0] + x - .1, ctr[1] + y - .1), (.05, .02, .09), 0, .2 * i); 
    g.commit()

def build_warehouse(ctr):
    g = G('w'); m = M(); f = F((ctr[0] - .14, ctr[1] + .12), 0)
    mb = mat('#b2623e', 'brick', .8, .15, scale=1, col2='#9a5236'); mr = mat('#a2502c', 'tile', .6, .2, col2='#7e3a20'); mt = mat('#5a3a22', 'plank', .6)
    g.box(mat('#8a867c', 'stone', .7), f.w(0, 0), (1.5, .92, .05), 0)
    g.box(mb, f.w(0, 0), (1.44, .86, .34), .05); g.box(mat('#d8cba8', 'noise', .8, .1), f.w(0, 0), (1.46, .88, .12), .39)   # plaster upper band
    g.roof(mr, mat('#d8cba8', 'noise'), f.c, (1.44, .88), .51, .4, 0, (.08, .1), medge=mat('#4a2e1c', 'flat'))
    for t in (-.45, 0, .45): g.box(m['dwood'], f.w(t, -.442), (.03, .01, .48), .05)
    for z in (.2,): g.box(m['dwood'], f.w(0, -.442), (1.44, .01, .03), .39)
    # big doors
    for t in (-.36, .36):
        g.box(mat('#6a4020', 'plank', .6, .2), f.w(t, -.442), (.3, .02, .3), .05); g.box(mat('#241812', 'flat'), f.w(t, -.45), (.01, .022, .3), .05) if False else None
        g.box(mat('#2a1c14', 'flat'), f.w(t, -.446), (.01, .026, .3), .05)
    g.box(mat('#6a4020', 'plank'), f.w(.724, 0), (.02, .32, .32), .05)
    for t in (-.26, .26): window(g, f, '+x', t, .36, 1.44, .86, .09, .1, m['white'], m['glass'])
    for t in (.0,): window(g, f, '-y', t, .34, 1.44, .86, .08, .1)
    # loading awning
    g.roof(mat('#d8402c', 'rows', .8, .1, col2='#a82c20', scale=.4), mat('#d8402c'), f.w(.0, -.62), (.7, .0001 + .2), .26, .05, 0, (.0, .02))
    for t in (-.35, .35): g.cyl(m['wood'], f.w(t, -.7, 0), f.w(t, -.7, .24), .015, .015, 6)
    # hoist crane at gable
    g.beam(m['dwood'], f.w(.74, .3, .5), f.w(1.0, .3, .5), .035); g.beam(m['dwood'], f.w(.74, .3, .3), f.w(.97, .3, .5), .02)
    g.beam(m['rope'], f.w(.97, .3, .5), f.w(.97, .3, .35), .007); crate(g, f.w(.97, .3)[:2], .09, 0, '#b8844a') if False else g.box(mat('#b8844a', 'plank'), f.w(.97, .3), (.09, .09, .09), .26)
    # cargo
    for p in ((.0, -.74), (.12, -.78), (.3, -.74)): barrel(g, f.w(*p)[:2])
    barrel(g, f.w(.2, -.76)[:2], .045, .08)
    g.box(mat('#b8844a', 'plank'), f.w(-.45, -.76), (.12, .1, .1), 0); g.box(mat('#c09050', 'plank'), f.w(-.45, -.76), (.1, .09, .09), .1)
    sack(g, f.w(-.65, -.74)[:2]); sack(g, f.w(-.58, -.8)[:2]); sack(g, f.w(-.6, -.68)[:2], .04)
    # pennant
    g.cyl(m['wood'], f.w(-.7, 0, .51 + .4), f.w(-.7, 0, .51 + .62), .008, .008, 6)
    g.face(mat('#d8402c', 'flat'), [f.w(-.7, 0, .51 + .62), f.w(-.7, 0, .51 + .56), f.w(-.58, .0, .51 + .58)])
    g.commit()

def build_wheat(ctr):
    g = G('wh'); r = random.Random(4)
    g.face(mat('#6a4a30', 'speck', .9, .05, col2='#4a321e'), [(ctr[0] - .93, ctr[1] - .93, .004), (ctr[0] + .93, ctr[1] - .93, .004), (ctr[0] + .93, ctr[1] + .93, .004), (ctr[0] - .93, ctr[1] + .93, .004)][::-1])
    cols = ['#e8c040', '#d8a830', '#f0d058', '#c89a28']
    for i in range(10):
        y = ctr[1] - .8 + i * .178
        m = mat(cols[i % 4], 'rows', .8, .15, col2=hexmul(cols[i % 4], .72), scale=.5)
        g.box(m, (ctr[0], y), (1.62, .1, .1), .0, 0, taper=.85)
    # a few stalks tufts + poppies
    for i in range(10): 
        x = ctr[0] + r.uniform(-.75, .75); y = ctr[1] + r.uniform(-.75, .75)
        g.sph(mat('#e04030', 'flat'), (x, y, .115), .016, 5, 4)
    g.commit()

def build_pier(ctr):
    g = G('p'); m = M(); mp = mat('#a2723e', 'plank', .6, .3, scale=.5, col2='#6e4826'); mpile = mat('#5e3c22', 'noise', .7, .2, scale=.3)
    cx, cy = ctr
    g.box(mp, (cx, cy), (1.0, .36, .035), .13)
    for t in (-.32, 0, .32): g.box(m['dwood'], (cx + t, cy), (.04, .44, .03), .1)
    for x in (-.42, -.14, .14, .42):
        for s in (-1, 1):
            g.cyl(mpile, (cx + x, cy + s * .2, -.02), (cx + x, cy + s * .2, .2), .03, .03, 8)
    g.beam(m['dwood'], (cx - .5, cy - .2, .22), (cx + .5, cy - .2, .22), .02); 
    g.cyl(m['iron'], (cx + .42, cy + .14, .16), (cx + .42, cy + .14, .26), .03, .026, 8)
    g.cyl(m['rope'], (cx + .0, cy - .1, .165), (cx + .0, cy - .1, .185), .06, .06, 10) ; g.cyl(m['rope'], (cx + .0, cy - .1, .185), (cx + .0, cy - .1, .2), .04, .04, 10)
    barrel(g, (cx - .3, cy + .08)); 
    g.commit()
    # foam rings round piles
    mf = mat('#e8f6fc', 'flat', .9, .0)
    g2 = G('foam')
    for x in (-.42, -.14, .14, .42):
        for s in (-1, 1):
            g2.cyl(mf, (cx + x, cy + s * .2, .003), (cx + x, cy + s * .2, .004), .065, .065, 10)
    g2.commit()

def build_cart(ctr):
    g = G('ct'); m = M(); cx, cy = ctr[0] - .05, ctr[1] + .02
    wd = mat('#8a5a32', 'plank', .6, .2); wh = mat('#5a361e', 'flat', .5, .3)
    g.box(wd, (cx - .12, cy), (.3, .2, .035), .09); g.roof(mat('#d84a30', 'rows', .8, .1, col2='#a02c1e', scale=.3), mat('#d84a30'), (cx - .14, cy), (.26, .18), .2, .08, 0, (.02, .02)) if False else None; 
    for s in (-1, 1): g.box(wd, (cx - .12, cy + s * .1), (.3, .015, .07), .1)
    g.box(wd, (cx - .27, cy), (.015, .2, .07), .1)
    for s in (-1, 1):
        g.cyl(wh, (cx - .1, cy + s * .125, .09), (cx - .1, cy + s * .14, .09), .09, .09, 12); g.cyl(m['iron'], (cx - .1, cy + s * .13, .09), (cx - .1, cy + s * .15, .09), .025, .025, 8)
    sack(g, (cx - .2, cy - .02), .05); sack(g, (cx - .12, cy + .04), .05); barrel(g, (cx - .06, cy - .04), .05, .1) 
    g.beam(wd, (cx + .02, cy - .03, .1), (cx + .26, cy - .03, .13), .02); g.beam(wd, (cx + .02, cy + .03, .1), (cx + .26, cy + .03, .13), .02)
    # ox
    mo = mat('#e0d0b0', 'noise', .8, .1, col2='#a8744a', scale=.12, var=.9); ox = cx + .36
    g.box(mo, (ox, cy), (.26, .13, .12), .08, 0, taper=.92)
    for dx in (-.09, .09):
        for s in (-1, 1): g.cyl(mo, (ox + dx, cy + s * .045, 0), (ox + dx, cy + s * .045, .09), .022, .018, 6)
    g.box(mo, (ox + .17, cy), (.11, .09, .09), .12, 0); g.box(mat('#e8d8b8', 'flat'), (ox + .225, cy), (.02, .08, .05), .12)
    for s in (-1, 1): g.beam(mat('#e8e0c8', 'flat'), (ox + .17, cy + s * .045, .2), (ox + .19, cy + s * .08, .26), .014)
    g.beam(mo, (ox - .13, cy, .15), (ox - .17, cy + .01, .08), .015)
    g.beam(wd, (ox + .05, cy - .08, .2), (ox + .05, cy + .08, .2), .02)
    g.commit()

def build_colonist(k):
    P = [dict(cloth='#2c5aa8', hat='#4a3020', hk='brim', pants='#5a4030', sack=1), dict(cloth='#b83030', hat='#2a2a30', hk='cap', pants='#3a3a48', tool=1),
         dict(cloth='#3a8a58', hat='#d8c8a0', hk='brim', pants='#6a5038', skirt=0), dict(cloth='#d8a030', hat='#f0f0e8', hk='coif', pants='#7a3a50', skirt=1)][k]
    def build(ctr):
        g = G('c'); cx, cy = ctr[0] + (.0), ctr[1] + .0; ms = mat('#e4aa7c', 'flat', .6, .2); mc = mat(P['cloth'], 'flat', .8, .1); mp = mat(P['pants'], 'flat', .8, .1)
        if P.get('skirt'): g.cyl(mc, (cx, cy, .0), (cx, cy, .17), .1, .05, 10)
        else:
            for s in (-1, 1): g.box(mp, (cx, cy + s * .028), (.055, .05, .17), 0)
        g.box(mc, (cx, cy), (.09, .15, .15), .17 if not P.get('skirt') else .15, 0, taper=.9)
        for s in (-1, 1): g.box(mc, (cx, cy + s * .095), (.045, .04, .13), .17, 0)
        g.sph(ms, (cx, cy, .36), .058, 8, 6)
        hm = mat(P['hat'], 'flat', .7, .2)
        if P['hk'] == 'brim': g.cyl(hm, (cx, cy, .395), (cx, cy, .405), .1, .1, 12); g.cyl(hm, (cx, cy, .4), (cx, cy, .46), .052, .045, 10)
        elif P['hk'] == 'cap': g.sph(hm, (cx, cy, .39), .062, 8, 5, (1, 1, .7))
        else: g.sph(hm, (cx, cy, .385), .066, 8, 5, (1.05, 1.1, .8))
        if P.get('sack'): g.sph(mat('#d8c8a0', 'noise', .9), (cx - .03, cy + .02, .3), .07, 8, 5, (1, 1, 1.1))
        if P.get('tool'): g.beam(mat('#6a4a2a', 'flat'), (cx + .05, cy - .1, .02), (cx + .02, cy - .1, .46), .015); g.box(mat('#8a8a90', 'flat', .3, .9), (cx + .02, cy - .1), (.05, .01, .06), .4)
        g.commit(smooth=False)
    return build

def build_tree(k):
    def build(ctr):
        g = G('t'); r = random.Random(k * 11 + 3); cx, cy = ctr[0], ctr[1]; mt = mat('#6a4428', 'noise', .8, .15, col2='#4a2c1a', scale=.2)
        if k == 0:
            g.cyl(mt, (cx, cy, 0), (cx, cy, .35), .06, .04, 8); ml = mat('#4a9a3a', 'noise', .8, .2, col2='#2a6a30', scale=.35, var=.5)
            for (x, y, z, rr) in [(0, 0, .55, .26), (.12, .06, .72, .2), (-.1, -.08, .74, .19), (0, .0, .9, .15)]: g.sph(ml, (cx + x, cy + y, z), rr, 10, 7, (1, 1, .9), .1, r)
        elif k == 1:
            g.cyl(mt, (cx, cy, 0), (cx, cy, .45), .07, .045, 8); ml = mat('#2f7a34', 'noise', .8, .2, col2='#1c5028', scale=.4, var=.5)
            for (x, y, z, rr) in [(0, 0, .62, .3), (.14, -.08, .86, .23), (-.12, .08, .9, .22), (0, 0, 1.08, .2), (.0, -.15, .64, .2)]: g.sph(ml, (cx + x, cy + y, z), rr, 10, 7, (1, 1, .95), .12, r)
        elif k == 2:
            g.cyl(mt, (cx, cy, 0), (cx, cy, .2), .045, .035, 8); ml = mat('#1f6a3c', 'noise', .8, .15, col2='#0f4428', scale=.3, var=.4)
            for i, (z, rr, h) in enumerate([(.14, .3, .32), (.34, .25, .3), (.54, .2, .28), (.74, .14, .26)]): g.cyl(ml, (cx, cy, z), (cx, cy, z + h), rr, .0, 11)
        else:
            mb = mat('#ece8dc', 'noise', .7, .2, col2='#6a6258', scale=.1); g.cyl(mb, (cx, cy, 0), (cx, cy, .5), .04, .03, 8); ml = mat('#a8c848', 'noise', .8, .2, col2='#6aa038', scale=.3, var=.5)
            for (x, y, z, rr) in [(0, 0, .66, .22), (.1, .05, .85, .17), (-.08, -.06, .82, .16), (0, 0, .98, .12), (.12, -.1, .6, .14)]: g.sph(ml, (cx + x, cy + y, z), rr, 9, 6, (.9, .9, 1.05), .12, r)
        g.commit(smooth=True)
    return build

def build_rock(k):
    def build(ctr):
        g = G('r'); r = random.Random(k + 5); cx, cy = ctr[0], ctr[1]; ms = mat('#8e8c88', 'stone', .65, .3, scale=.5, var=.6, col2='#6e6c6c')
        parts = [(0, 0, .09, .2, (1.2, 1, .8)), (.2, .08, .06, .12, (1, 1.1, .8)), (-.17, -.1, .045, .09, (1, 1, .9))] if k == 0 else [(0, 0, .12, .24, (1, 1.1, .85)), (.19, -.1, .06, .13, (1.2, 1, .8))]
        for (x, y, z, rr, sc) in parts: g.sph(ms, (cx + x, cy + y, z), rr, 8, 6, sc, .12, r)
        g.sph(mat('#5a8a3a', 'noise', .9, .1, scale=.2), (cx - .02, cy + .02, parts[0][2] + .09), .1, 8, 5, (1, 1, .35))
        for i in range(5): g.sph(mat('#3a7a3a', 'flat'), (cx + r.uniform(-.28, .28), cy + r.uniform(-.28, .28), .02), .02, 4, 3, (1, 1, 1.5))
        g.commit(smooth=True)
    return build

def build_windmill(ctr):
    g = G('m'); m = M(); cx, cy = ctr[0], ctr[1]
    ms = mat('#e8dcc4', 'brick', .8, .1, scale=1.2, col2='#cfc2a6'); 
    g.cyl(mat('#8a867c', 'stone', .7), (cx, cy, 0), (cx, cy, .06), .3, .3, 12)
    g.cyl(ms, (cx, cy, .06), (cx, cy, .9), .26, .18, 12)
    g.box(m['dwood'], (cx + .17, cy - .17), (.015, .1, .2), .06, math.pi / 4) if False else None
    g.cyl(mat('#7a4a28', 'rows', .6, .3, col2='#4a2c1a', scale=.5), (cx, cy, .9), (cx, cy, 1.0), .2, .21, 12)
    g.cyl(mat('#a8402a', 'tile', .5, .4, col2='#7a2c1c', scale=.6), (cx, cy, 1.0), (cx, cy, 1.24), .22, .0, 12)
    # windows & door
    d = (math.cos(-.6), math.sin(-.6)); 
    for z, a in ((.5, -.35), (.7, -.55)):
        aa = a; g.box(m['glass'], (cx + math.cos(aa) * .205, cy + math.sin(aa) * .205), (.012, .06, .09), z, aa)
    aa = -.9; g.box(m['dwood'], (cx + math.cos(aa) * .265, cy + math.sin(aa) * .265), (.014, .12, .2), .06, aa)
    # sails: axis pointing toward camera-right
    ax = Vector((math.cos(-.62), math.sin(-.62), 0)); hub = Vector((cx, cy, 1.04)) + ax * .26
    g.cyl(m['dwood'], (cx, cy, 1.04), tuple(hub + ax * .04), .035, .045, 8)
    side = Vector((-ax.y, ax.x, 0)); msail = mat('#efe6cc', 'flat', .9, .05); mfr = mat('#6a4428', 'flat', .6, .2)
    for i in range(4):
        a = i * math.pi / 2 + .35; dirv = side * math.cos(a) + Vector((0, 0, 1)) * math.sin(a); nrm = Vector((0, 0, 1)).cross(side).normalized() if False else ax
        p0 = hub + dirv * .1; p1 = hub + dirv * .66
        g.beam(mfr, tuple(p0), tuple(p1), .03)
        perp = nrm.cross(dirv).normalized() if False else ax.cross(dirv).normalized()
        q = [p0 + perp * .02, p1 + perp * .02, p1 + perp * .17, p0 + perp * .17]
        g.face(mat('#efe6cc', 'flat', .9, .05), [tuple(v) for v in q])
        g.face(mat('#efe6cc', 'flat', .9, .05), [tuple(v) for v in q][::-1])
        for tt in (.3, .55, .8): 
            pm = p0 + (p1 - p0) * tt; g.beam(mfr, tuple(pm + perp * .02), tuple(pm + perp * .17), .018)
        g.beam(mfr, tuple(p0 + perp * .17), tuple(p1 + perp * .17), .018)
    g.commit(smooth=False)

def build_ship(ctr):
    g = G('s'); m = M(); cx, cy = ctr; r = random.Random(2)
    mh = mat('#5a3420', 'plank', .5, .5, scale=.8, col2='#3e2214'); mst = mat('#d8a830', 'flat', .45, .6); mdk = mat('#b08050', 'plank', .6, .2, scale=.6, col2='#7a5430')
    mrail = mat('#8a5a34', 'plank', .5, .3)
    N = 16; L = 1.76; Wd = .27; prof = 6
    def hw(t): return Wd * (1 - ((t - .38) / .62) ** 2 if t > .38 else 1 - ((.38 - t) / .38) ** 2 * .5)
    def zt(t): return .17 + .13 * (1 - t) ** 2 + .12 * t ** 3
    def sec(t, s, side):
        x = cx - L / 2 + L * t; w = hw(t); zb = .01; z = zb + (zt(t) - zb) * s ** 1.25
        wx = w * (.62 + .38 * math.sin(s * math.pi / 2)) * (1 - .07 * max(0, s - .75) / .25)
        return (x, cy + side * wx, z)
    for side in (-1, 1):
        for i in range(N):
            t0, t1 = i / N, (i + 1) / N
            for j in range(prof):
                s0, s1 = j / prof, (j + 1) / prof; mm = mst if j == prof - 2 else (mrail if j == prof - 1 else mh)
                q = [sec(t0, s0, side), sec(t1, s0, side), sec(t1, s1, side), sec(t0, s1, side)]
                g.face(mm, q, flip=(side == 1))
    # transom
    for j in range(prof):
        s0, s1 = j / prof, (j + 1) / prof; g.face(mst if j == prof - 2 else mh, [sec(0, s0, -1), sec(0, s0, 1), sec(0, s1, 1), sec(0, s1, -1)], flip=True)
    # deck
    pts = [sec(i / N, 1, -1) for i in range(N + 1)] + [sec(i / N, 1, 1) for i in range(N, -1, -1)]
    g.face(mdk, [(p[0], p[1], p[2] - .02) for p in pts], flip=True)
    # aft castle, fore castle
    g.box(mh, (cx - .66, cy), (.5, .46, .2), .2); g.box(mdk, (cx - .66, cy), (.5, .46, .015), .4)
    g.box(mst, (cx - .66, cy - .233), (.5, .01, .03), .3, 0); g.box(m['glass'], (cx - .66, cy - .236), (.36, .012, .06), .24)
    for dx in (-.15, .0, .15): g.box(m['gold'], (cx - .66 + dx, cy - .238), (.04, .012, .05), .24)
    g.box(mh, (cx - .9, cy), (.14, .4, .16), .2) if False else None
    g.box(mh, (cx + .58, cy), (.3, .32, .1), .27); g.box(mdk, (cx + .58, cy), (.3, .32, .012), .37)
    # bowsprit
    g.beam(mrail, (cx + .8, cy, .38), (cx + 1.05, cy, .5), .03)
    # masts
    def mast(x, h, yards):
        g.cyl(mrail, (x, cy, .2), (x, cy, h), .026, .018, 8)
        g.cyl(mrail, (x, cy, h * .72), (x, cy, h * .72 + .02), .06, .06, 8)
        for (z, wd, hh, band) in yards:
            sx = wd; nx, nz = 6, 5
            g.beam(mrail, (x, cy - sx / 2 - .03, z + hh), (x, cy + sx / 2 + .03, z + hh), .018)
            for i in range(nx):
                for j in range(nz):
                    def P(i_, j_): 
                        u = i_ / nx; v = j_ / nz; return (x + .1 * math.sin(u * math.pi) * math.sin(v * math.pi * .9 + .15) + .02, cy - sx / 2 + sx * u, z + hh - hh * v)
                    mm = mat('#d6322a', 'flat', .85, .05) if band and j == 2 else mat('#f0e6c8', 'noise', .9, .05, col2='#d0c4a0', scale=.4)
                    g.face(mm, [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)]); g.face(mm, [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)][::-1])
        g.face(mat('#d8a830', 'flat'), [(x, cy, h), (x, cy, h - .09), (x - .22, cy + .02, h - .045)])
    mast(cx - .02, 1.45, [(.45, .42, .5, True), (1.0, .32, .38, False)])
    mast(cx + .55, 1.1, [(.55, .3, .4, False)])
    mast(cx - .68, .95, [(.62, .24, .26, False)])
    # shrouds
    for s in (-1, 1): g.beam(m['rope'], (cx - .02, cy + s * .24, .3), (cx - .02, cy + s * .04, 1.0), .006); g.beam(m['rope'], (cx + .55, cy + s * .2, .34), (cx + .55, cy + s * .03, .8), .006)
    g.beam(m['rope'], (cx - .02, cy, 1.43), (cx + 1.04, cy, .5), .006); g.beam(m['rope'], (cx - .02, cy, 1.43), (cx - .68, cy, .93), .006)
    # barrels & cargo on deck
    barrel(g, (cx + .2, cy - .05), .05, .09); barrel(g, (cx + .3, cy + .08), .045, .08); g.box(mat('#b8844a', 'plank'), (cx + .26, cy - .12), (.09, .09, .08), .24)
    g.commit(smooth=False)
    # waterline foam ring
    gg = G('foam'); mf = mat('#eef8fc', 'flat', .9, 0)
    pts = [(cx - L / 2 + L * i / N, cy - hw(i / N) * .6 - .05) for i in range(N + 1)] + [(cx - L / 2 + L * i / N, cy + hw(i / N) * .6 + .05) for i in range(N, -1, -1)]
    gg.face(mf, [(p[0], p[1], .004) for p in pts][::-1]); gg.commit()
