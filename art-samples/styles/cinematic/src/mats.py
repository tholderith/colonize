"""Procedural PBR material library (Cycles)."""
from common import *

def _lin(c): return srgb(c)

def plaster(tint=(0.80, 0.75, 0.64), grime_h=0.11, name='plaster'):
    key = f'{name}{tint}{grime_h}'
    def mk():
        mb = MB(key); co = mb.coord('Object')
        n1 = mb.noise(co, 9, 5, 0.6, 0.3); n2 = mb.noise(co, 80, 3, 0.5)
        t = tuple(tint)
        a = tuple(v * 0.88 for v in t); b = tuple(min(1, v * 1.04) for v in t)
        base = mb.mix(mb.fmap(n1, 0.35, 0.65), a, b)
        z = mb.sepz(co)['Z']
        gz = mb.fmap(z, 0.0, grime_h, 1.0, 0.0)
        gn = mb.fmap(mb.noise(co, 22, 4, 0.55, 0.4), 0.35, 0.7, 0.35, 1.2)
        gm = mb.math('MULTIPLY', gz, gn, True)
        # vertical rain streaks
        st = mb.noise(mb.mapping(co, (35, 35, 3)), 1.0, 3, 0.5)
        stm = mb.fmap(st, 0.45, 0.75, 0.0, 0.18)
        col = mb.mix(gm, base, (0.30, 0.26, 0.20))
        col = mb.mix(stm, col, (0.38, 0.34, 0.28))
        # algae/moss low
        mg = mb.math('MULTIPLY', gz, mb.fmap(mb.noise(co, 40, 4), 0.55, 0.8), True)
        col = mb.mix(mb.math('MULTIPLY', mg, 0.5), col, (0.26, 0.33, 0.17))
        bump = mb.bump(mb.math('ADD', n2, mb.noise(co, 14, 3, 0.5)), 0.35, 0.004)
        return mb.done(col, 0.92, bump)
    return M(key, mk)

def timber(tint=(0.30, 0.22, 0.15), name='timber'):
    key = f'{name}{tint}'
    def mk():
        mb = MB(key); co = mb.coord('Object')
        g = mb.noise(mb.mapping(co, (90, 90, 14)), 1.0, 4, 0.55, 0.6)
        g2 = mb.noise(co, 8, 3, 0.5)
        t = tint
        col = mb.mix(mb.fmap(g, 0.3, 0.7), tuple(v * 0.7 for v in t), tuple(min(1, v * 1.25) for v in t))
        col = mb.mix(mb.fmap(g2, 0.4, 0.7, 0, 0.35), col, (0.55, 0.52, 0.46))   # grey weathering
        bump = mb.bump(g, 0.5, 0.004)
        return mb.done(col, 0.78, bump)
    return M(key, mk)

def planks(tint=(0.36, 0.28, 0.20), vertical=True, bw=0.045, name='planks', gap=0.04, rough=0.85):
    key = f'{name}{tint}{vertical}{bw}'
    def mk():
        mb = MB(key); uv = mb.coord('UV'); co = mb.coord('Object')
        if vertical: c, f = mb.brick(uv, tint, tuple(v * 0.8 for v in tint), (0.04, 0.03, 0.02), 1, bw, 2.0, gap * 0.5, offset=0.0)
        else: c, f = mb.brick(uv, tint, tuple(v * 0.8 for v in tint), (0.04, 0.03, 0.02), 1, 2.0, bw, gap * 0.5, offset=0.0)
        gr = mb.noise(mb.mapping(co, (80, 80, 12)), 1.0, 4, 0.55, 0.5)
        col = mb.mix(mb.fmap(gr, 0.35, 0.65, 0, 0.5), c, (0.50, 0.47, 0.42))
        col = mb.mix(mb.fmap(mb.noise(co, 6, 3), 0.4, 0.7, 0, 0.5), col, tuple(v * 0.6 for v in tint))
        bump = mb.bump(mb.math('ADD', f, mb.math('MULTIPLY', gr, 0.3)), 0.6, 0.004)
        return mb.done(col, rough, bump)
    return M(key, mk)

def clay_tile(name='clay'):
    def mk():
        mb = MB(name); uv = mb.coord('UV'); co = mb.coord('Object')
        c, f = mb.brick(uv, (0.70, 0.31, 0.17), (0.82, 0.41, 0.23), (0.16, 0.08, 0.06), 1, 0.052, 0.040, 0.0055, offset=0.5)
        n = mb.noise(co, 25, 4, 0.55)
        col = mb.mix(mb.fmap(n, 0.35, 0.65, 0, 0.5), c, (0.50, 0.24, 0.14))
        # weathering / lichen / moss patches
        mn = mb.fmap(mb.noise(co, 11, 5, 0.6, 0.2), 0.58, 0.78, 0, 0.45)
        col = mb.mix(mn, col, (0.30, 0.34, 0.18))
        sooty = mb.fmap(mb.noise(co, 30, 3), 0.55, 0.85, 0, 0.25)
        col = mb.mix(sooty, col, (0.16, 0.13, 0.12))
        rid = mb.noise(mb.mapping(uv, (1, 1, 1)), 90, 2, 0.5)
        bump = mb.bump(mb.math('ADD', f, mb.math('MULTIPLY', rid, 0.2)), 1.4, 0.006)
        return mb.done(col, 0.75, bump)
    return M(name, mk)

def slate_shingle(name='shingle', tint=(0.30, 0.27, 0.24)):
    def mk():
        mb = MB(name + str(tint)); uv = mb.coord('UV'); co = mb.coord('Object')
        c, f = mb.brick(uv, tint, tuple(v * 1.35 for v in tint), (0.05, 0.045, 0.04), 1, 0.045, 0.034, 0.003, offset=0.5)
        n = mb.noise(co, 18, 4, 0.55)
        col = mb.mix(mb.fmap(n, 0.3, 0.7, 0, 0.5), c, tuple(v * 0.7 for v in tint))
        mn = mb.fmap(mb.noise(co, 9, 5, 0.6, 0.2), 0.55, 0.75, 0, 0.7)
        col = mb.mix(mn, col, (0.28, 0.32, 0.18))
        bump = mb.bump(f, 0.8, 0.004)
        return mb.done(col, 0.7, bump)
    return M(name + str(tint), mk)

def thatch(name='thatch'):
    def mk():
        mb = MB(name); uv = mb.coord('UV'); co = mb.coord('Object')
        st = mb.noise(mb.mapping(uv, (120, 11, 1)), 1.0, 3, 0.55, 0.3)
        st2 = mb.noise(mb.mapping(uv, (260, 26, 1)), 1.0, 2, 0.5)
        crs = mb.noise(mb.mapping(uv, (2, 9, 1)), 1.0, 2, 0.5)
        col = mb.ramp(mb.math('ADD', st, mb.math('MULTIPLY', st2, 0.5)), [(0.2, (0.32, 0.25, 0.14)), (0.55, (0.55, 0.45, 0.26)), (0.9, (0.68, 0.58, 0.36))])
        mn = mb.fmap(mb.noise(co, 8, 5, 0.6, 0.3), 0.50, 0.72, 0, 0.9)
        col = mb.mix(mn, col, (0.24, 0.30, 0.13))
        dirt = mb.fmap(mb.noise(co, 14, 3), 0.4, 0.8, 0, 0.4)
        col = mb.mix(dirt, col, (0.20, 0.16, 0.10))
        bump = mb.bump(mb.math('ADD', st, mb.math('MULTIPLY', crs, 0.8)), 1.0, 0.012)
        return mb.done(col, 0.97, bump)
    return M(name, mk)

def masonry(name='masonry', light=False, big=False):
    key = f'{name}{light}{big}'
    def mk():
        mb = MB(key); uv = mb.coord('UV'); co = mb.coord('Object')
        bw, bh = (0.13, 0.065) if not big else (0.18, 0.085)
        if light: cA, cB, mo = (0.62, 0.58, 0.50), (0.74, 0.70, 0.60), (0.72, 0.68, 0.60)
        else: cA, cB, mo = (0.36, 0.34, 0.30), (0.52, 0.48, 0.41), (0.50, 0.47, 0.40)
        c, f = mb.brick(uv, cA, cB, mo, 1, bw, bh, 0.006, offset=0.5)
        n = mb.noise(co, 30, 5, 0.6, 0.2)
        col = mb.mix(mb.fmap(n, 0.3, 0.7, 0, 0.4), c, (0.25, 0.23, 0.20))
        z = mb.sepz(co)['Z']
        mg = mb.math('MULTIPLY', mb.fmap(z, 0.0, 0.2, 1, 0), mb.fmap(mb.noise(co, 25, 4), 0.45, 0.7, 0, 1))
        col = mb.mix(mb.math('MULTIPLY', mg, 0.6), col, (0.25, 0.32, 0.16))
        bump = mb.bump(mb.math('ADD', f, mb.math('MULTIPLY', mb.noise(co, 60, 4), 0.6)), 1.0, 0.006)
        return mb.done(col, 0.9, bump)
    return M(key, mk)

def brickwork(name='brick'):
    def mk():
        mb = MB(name); uv = mb.coord('UV'); co = mb.coord('Object')
        c, f = mb.brick(uv, (0.40, 0.17, 0.11), (0.56, 0.25, 0.16), (0.55, 0.52, 0.46), 1, 0.07, 0.032, 0.005, offset=0.5)
        col = mb.mix(mb.fmap(mb.noise(co, 30, 4), 0.35, 0.7, 0, 0.5), c, (0.18, 0.14, 0.12))
        bump = mb.bump(f, 0.8, 0.004)
        return mb.done(col, 0.9, bump)
    return M(name, mk)

def glass(name='glass', warm=0.0):
    def mk():
        mb = MB(name)
        mb.bsdf.inputs['Base Color'].default_value = srgb((0.03, 0.05, 0.07))
        mb.set('Roughness', 0.04); mb.bsdf.inputs['Specular IOR Level'].default_value = 1.0
        mb.set('IOR', 1.5)
        if warm: 
            mb.set('Emission Color', srgb((1.0, 0.65, 0.3))); mb.set('Emission Strength', warm)
        return mb.m
    return M(name + str(warm), mk)

def solid(name, color, rough=0.8, metal=0.0, **kw):
    def mk():
        mb = MB(name); mb.set('Base Color', srgb(color) if not (isinstance(color, tuple) and len(color) == 4) else color)
        mb.set('Roughness', rough); mb.set('Metallic', metal)
        for k, v in kw.items(): mb.set(k.replace('_', ' '), v)
        return mb.m
    return M(name + str(color), mk)

def painted(name, color, rough=0.7):
    """lightly weathered painted wood"""
    key = name + str(color)
    def mk():
        mb = MB(key); co = mb.coord('Object')
        n = mb.noise(co, 40, 4)
        col = mb.mix(mb.fmap(n, 0.35, 0.7, 0, 0.5), color, tuple(v * 0.6 for v in color))
        wear = mb.fmap(mb.noise(co, 70, 3), 0.55, 0.8, 0, 0.5)
        col = mb.mix(wear, col, (0.45, 0.40, 0.33))
        return mb.done(col, rough, mb.bump(n, 0.3, 0.003))
    return M(key, mk)

def iron(name='iron'):
    def mk():
        mb = MB(name); co = mb.coord('Object')
        mb.set('Base Color', srgb((0.12, 0.11, 0.10))); mb.set('Metallic', 0.8); mb.set('Roughness', 0.5)
        return mb.m
    return M(name, mk)

def bark(tint=(0.20, 0.16, 0.12), name='bark'):
    key = name + str(tint)
    def mk():
        mb = MB(key); co = mb.coord('Object')
        n = mb.noise(mb.mapping(co, (45, 45, 7)), 1.0, 5, 0.6, 0.4)
        col = mb.mix(mb.fmap(n, 0.3, 0.75), tuple(v * 0.6 for v in tint), tuple(v * 1.5 for v in tint))
        col = mb.mix(mb.fmap(mb.noise(co, 6, 3), 0.55, 0.8, 0, 0.5), col, (0.26, 0.31, 0.16))
        return mb.done(col, 0.95, mb.bump(n, 1.0, 0.012))
    return M(key, mk)

def foliage(name, dark, light, yellow=0.0, scale=1.0, ao=True, trans=0.0):
    key = f'{name}{dark}{light}{yellow}'
    def mk():
        mb = MB(key); co = mb.coord('Object')
        n = mb.noise(co, 14, 4, 0.6)
        n2 = mb.noise(co, 140, 3, 0.5)
        z = mb.sepz(co)['Z']
        h = mb.fmap(z, 0.2, 1.5, 0.0, 1.0)
        t = mb.math('ADD', mb.math('MULTIPLY', n, 0.7), mb.math('MULTIPLY', h, 0.45))
        col = mb.ramp(t, [(0.15, dark), (0.5, tuple((a + b) / 2 for a, b in zip(dark, light))), (0.85, light)])
        if yellow:
            ym = mb.fmap(mb.noise(co, 5, 3, 0.5, 0.2), 0.55, 0.8, 0, yellow)
            col = mb.mix(ym, col, (0.55, 0.52, 0.18))
        col = mb.mix(mb.fmap(n2, 0.3, 0.7, 0.0, 0.25), col, (0.05, 0.08, 0.03))
        if ao:
            aon = mb.n('AmbientOcclusion', samples=4); aon.inputs['Distance'].default_value = 0.22
            aon.inputs['Color'].default_value = (1, 1, 1, 1)
            col = mb.mix(1.0, (0, 0, 0, 1), col)  # placeholder
            m = mb.n('MixRGB', blend_type='MULTIPLY'); m.inputs['Fac'].default_value = 0.9
            mb.link(col, m.inputs[1]); mb.link(aon.outputs['AO'], m.inputs[2]); col = m.outputs[0]
        bump = mb.bump(n2, 0.8, 0.01)
        mb.done(col, 0.62, bump)
        mb.bsdf.inputs['Specular IOR Level'].default_value = 0.3
        if trans: 
            mb.bsdf.inputs['Subsurface Weight'].default_value = trans
            mb.bsdf.inputs['Subsurface Radius'].default_value = (0.05, 0.08, 0.03)
        return mb.m
    return M(key, mk)

def cloth(name='sail', tint=(0.84, 0.78, 0.64), panel=0.06, translucency=0.35):
    key = name + str(tint)
    def mk():
        mb = MB(key); uv = mb.coord('UV'); co = mb.coord('Object')
        w1 = mb.noise(mb.mapping(co, (300, 300, 300)), 1.0, 2, 0.6)
        n = mb.noise(co, 6, 4, 0.5)
        col = mb.mix(mb.fmap(n, 0.3, 0.7, 0, 0.4), tint, tuple(v * 0.7 for v in tint))
        col = mb.mix(mb.fmap(mb.noise(co, 25, 3), 0.55, 0.8, 0, 0.35), col, (0.38, 0.30, 0.20))   # stains
        c, f = mb.brick(uv, (1, 1, 1), (1, 1, 1), (0.55, 0.52, 0.46), 1, 3.0, panel, 0.004, offset=0.0)
        col = mb.mix(mb.fmap(f, 0, 1), (0.30, 0.27, 0.22), col)
        bump = mb.bump(mb.math('ADD', w1, mb.math('MULTIPLY', f, 1.0)), 0.5, 0.004)
        mb.done(col, 0.9, bump)
        tr = mb.n('BsdfTranslucent'); mb.link(col, tr.inputs['Color'])
        mx = mb.n('MixShader'); mx.inputs['Fac'].default_value = translucency
        mb.nt.links.new(mb.bsdf.outputs[0], mx.inputs[1]); mb.nt.links.new(tr.outputs[0], mx.inputs[2])
        mb.nt.links.new(mx.outputs[0], mb.out.inputs[0])
        return mb.m
    return M(key, mk)

def rope(name='rope'):
    return solid(name, (0.20, 0.16, 0.11), 0.95)

def dirt_decal(name='yard', color=(0.38, 0.30, 0.21), inner=0.55, outer=1.0):
    key = name + str(color)
    def mk():
        mb = MB(key); g = mb.coord('Generated'); co = mb.coord('Object')
        sub = mb.n('VectorMath', operation='SUBTRACT'); mb.link(g, sub.inputs[0]); sub.inputs[1].default_value = (0.5, 0.5, 0)
        ln = mb.n('VectorMath', operation='LENGTH'); mb.link(sub.outputs[0], ln.inputs[0])
        r = mb.math('MULTIPLY', ln.outputs['Value'], 2.0)
        nz = mb.noise(co, 9, 4, 0.55, 0.2)
        r2 = mb.math('ADD', r, mb.math('MULTIPLY', mb.math('SUBTRACT', nz, 0.5), 0.55))
        alpha = mb.fmap(r2, outer, inner, 0.0, 0.92)
        n3 = mb.noise(co, 60, 4)
        col = mb.mix(mb.fmap(mb.noise(co, 16, 4), 0.3, 0.7), color, tuple(v * 1.35 for v in color))
        col = mb.mix(mb.fmap(n3, 0.3, 0.7, 0, 0.4), col, (0.30, 0.27, 0.20))
        bump = mb.bump(n3, 0.7, 0.004)
        mb.bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        mb.link(col, mb.bsdf.inputs['Base Color']); mb.set('Roughness', 0.97); mb.link(bump, mb.bsdf.inputs['Normal'])
        tr = mb.n('BsdfTransparent'); mx = mb.n('MixShader')
        mb.link(alpha, mx.inputs['Fac']); mb.nt.links.new(tr.outputs[0], mx.inputs[1]); mb.nt.links.new(mb.bsdf.outputs[0], mx.inputs[2])
        mb.nt.links.new(mx.outputs[0], mb.out.inputs[0])
        return mb.m
    return M(key, mk)

def alpha_mat(name, color, noise_scale=20, outer=1.0, inner=0.3, strength=0.9, rough=0.5, emission=0.0, mask_noise=0.45):
    """radial/edge-faded translucent surface using Generated coords (for foam, etc)."""
    key = name
    def mk():
        mb = MB(key); g = mb.coord('Generated'); co = mb.coord('Object')
        nz = mb.noise(co, noise_scale, 4, 0.55, 0.2)
        a = mb.math('MULTIPLY', mb.fmap(nz, 1 - mask_noise, mask_noise + 0.2, 0, 1), strength)
        mb.bsdf.inputs['Base Color'].default_value = srgb(color); mb.set('Roughness', rough)
        tr = mb.n('BsdfTransparent'); mx = mb.n('MixShader')
        mb.link(a, mx.inputs['Fac']); mb.nt.links.new(tr.outputs[0], mx.inputs[1]); mb.nt.links.new(mb.bsdf.outputs[0], mx.inputs[2])
        mb.nt.links.new(mx.outputs[0], mb.out.inputs[0])
        return mb.m
    return M(key, mk)
