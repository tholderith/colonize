"""Neon Foundry terrain: periodic numpy textures -> 132x68 iso tiles (anchor [66,66]). All variants of a type share the same
periodic base field (identical edges) and add variant-specific detail only in the tile interior, so tiles seam perfectly."""
import numpy as np, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
SSF = 2; TW, TH = 132, 68; AX, AY = 66, 66
N = 256   # periodic lattice resolution

def pnoise(seed, beta=2.0, n=N, kmin=1.0):
    """periodic 1/f^beta noise in [0,1] on an n x n lattice."""
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(n) * n
    kx, ky = np.meshgrid(f, f)
    k = np.sqrt(kx ** 2 + ky ** 2); k[0, 0] = 1
    spec = (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))) / (np.maximum(k, kmin) ** (beta / 1.0))
    spec[0, 0] = 0
    a = np.real(np.fft.ifft2(spec)); a = (a - a.mean()) / (a.std() + 1e-9)
    return a

def bil(a, u, v):
    """bilinear periodic sample of lattice a at u,v (unit coords, wrapped)."""
    n = a.shape[0]; x = (u % 1.0) * n; y = (v % 1.0) * n
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
    x0 %= n; y0 %= n; x1 = (x0 + 1) % n; y1 = (y0 + 1) % n
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy) + a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy)

def grid():
    W, H = TW * SSF, TH * SSF
    px, py = np.meshgrid((np.arange(W) + 0.5) / SSF, (np.arange(H) + 0.5) / SSF)
    X = (((px - AX) / 64.0) + ((py - (AY - 64)) / 32.0)) / 2.0
    Y = (((py - (AY - 64)) / 32.0) - ((px - AX) / 64.0)) / 2.0
    return X, Y, px, py

def smooth(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def interior(X, Y, m=0.14):
    ex = np.minimum(X, 1 - X); ey = np.minimum(Y, 1 - Y)
    return smooth(0.0, m, np.minimum(ex, ey))

def shade(h, X, Y, k=1.0):
    """bump lighting from height field via finite diff in tile coords; light from screen upper-left."""
    gx = np.gradient(h, axis=1); gy = np.gradient(h, axis=0)
    return np.clip(0.5 - (gx * 0.7 + gy * 0.7) * k, 0, 1)

def hexc(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)], 'float32')
def mixc(a, b, t): t = t[..., None]; return a * (1 - t) + b * t

NZ = {}
def noise(name, seed, beta=2.0):
    if name not in NZ: NZ[name] = pnoise(seed, beta)
    return NZ[name]

def finish(rgb, X, Y, name):
    W, H = rgb.shape[:2]
    msk = (np.abs(X - 0.5) + np.abs(Y - 0.5) <= 0.5 + 0.045)   # slight overscan
    al = msk.astype('float32')
    arr = np.concatenate([np.clip(rgb, 0, 1), al[..., None]], -1).astype('float32')
    # premultiplied downsample
    pm = arr.copy(); pm[..., :3] *= pm[..., 3:4]
    ch = [np.asarray(Image.fromarray(pm[..., c].copy(), 'F').resize((TW, TH), Image.LANCZOS)) for c in range(4)]
    pm = np.stack(ch, -1).clip(0, 1); a = pm[..., 3:4]
    col = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0)
    col = np.clip(col, 0, 1); a = np.clip(a * 1.6, 0, 1)
    Image.fromarray((np.concatenate([col, a], -1) * 255 + 0.5).astype('uint8'), 'RGBA').save(os.path.join(OUT, name + '.png'))

def streaks(px, py, seed, ncol, scale=0.35):
    """vertical (screen) neon reflection streaks: coloured, used inside puddles."""
    rng = np.random.default_rng(seed)
    out = np.zeros(px.shape + (3,), 'float32')
    cols = [hexc('#ff2ea6'), hexc('#22eaff'), hexc('#ffa622'), hexc('#7a5cff')]
    for i in range(ncol):
        cx = rng.uniform(10, 120); w = rng.uniform(1.2, 3.5); y0 = rng.uniform(0, 30); ln = rng.uniform(14, 40)
        c = cols[rng.integers(0, len(cols))]
        prof = np.exp(-((px - cx) / w) ** 2) * smooth(y0 - 4, y0 + 6, py) * (1 - smooth(y0 + ln * 0.5, y0 + ln, py))
        out += prof[..., None] * c * rng.uniform(0.4, 1.0)
    return out * scale

# ------------------------------------------------------------------ types
def asphalt(k):
    X, Y, px, py = grid()
    base = noise('r1', 11, 2.2); fine = noise('r2', 12, 0.9); big = noise('r3', 13, 3.0)
    h = bil(fine, X, Y) * 0.5 + bil(base, X, Y) * 0.3
    col = np.broadcast_to(hexc('#1d2026'), X.shape + (3,)).copy()
    col = col * (0.85 + 0.12 * bil(big, X, Y)[..., None] + 0.05 * bil(fine, X * 2, Y * 2)[..., None])
    col *= (0.82 + 0.35 * shade(h, X, Y, 6)[..., None])
    # steel plate seams every half tile + rivets (periodic, same for all variants)
    cu = np.abs(((X * 2) % 1.0) - 0.5); cv = np.abs(((Y * 2) % 1.0) - 0.5)
    seam = (np.minimum(0.5 - cu, 0.5 - cv) < 0.012).astype('float32')
    col = col * (1 - 0.35 * seam[..., None])
    rv = ((((X * 2) % 1.0 - 0.07) ** 2 + ((Y * 2) % 1.0 - 0.07) ** 2) < 0.0007).astype('float32')
    col += rv[..., None] * 0.07
    # lane studs: amber at tile centre + mid-edge (every tile, so any road direction reads)
    for (cx, cy) in ((0.5, 0.5), (0.0, 0.5), (1.0, 0.5), (0.5, 0.0), (0.5, 1.0)):
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        col += (np.exp(-(d / 0.028) ** 2))[..., None] * hexc('#ffb030') * 0.9
        col += (np.exp(-(d / 0.07) ** 2))[..., None] * hexc('#ff8a10') * 0.10
    # painted dashes along both axes through centre (broken yellow), faint
    for ax in (0, 1):
        t = X if ax == 0 else Y; o = Y if ax == 0 else X
        dash = (np.abs(o - 0.5) < 0.012) & (((t * 4) % 1.0) < 0.5) & (((t * 4) % 1.0) > 0.12) & (np.abs(t - 0.5) > 0.12)
        col = np.where(dash[..., None], col * 0.4 + hexc('#8a7418') * 0.6, col)
    # puddles (interior only; variant specific) with neon reflection
    pn = pnoise(100 + k, 2.4, 128)
    pud = smooth(0.8, 1.15, bil(pn, X, Y)) * interior(X, Y, 0.16) * (1 if k % 3 else 0.4)
    refl = streaks(px, py, 50 + k, 5)
    pcol = hexc('#0c1018') + refl + hexc('#2a3050') * 0.12 * (1 - smooth(0, 60, py - 10))[..., None] + hexc('#40507a') * 0.06
    col = mixc(col, pcol, pud * 0.85)
    finish(col, X, Y, f'road_{k}')

def concrete(k):  # 'sand' -> slag/concrete shore
    X, Y, px, py = grid()
    n1 = noise('s1', 21, 2.0); n2 = noise('s2', 22, 0.8); n3 = noise('s3', 23, 3.0)
    h = bil(n2, X * 2, Y * 2) * 0.4 + bil(n1, X, Y) * 0.4
    col = np.broadcast_to(hexc('#4b4d50'), X.shape + (3,)).copy()
    tone = 0.85 + 0.13 * bil(n3, X, Y) + 0.05 * bil(n2, X, Y)
    col = col * tone[..., None] * (0.8 + 0.4 * shade(h, X, Y, 5)[..., None])
    col = mixc(col, col * hexc('#c8a070') * 1.5, smooth(0.5, 1.4, bil(n1, X * 1.0 + 0.3, Y * 1.0)) * 0.25)    # rust bleed
    # expansion joints on tile edges (deliberate slab grid)
    ex = np.minimum(X, 1 - X); ey = np.minimum(Y, 1 - Y); e = np.minimum(ex, ey)
    col *= (1 - 0.55 * (e < 0.014))[..., None]; col += (0.05 * ((e >= 0.014) & (e < 0.03)))[..., None]
    # variant-specific: oil stains, hazard-paint scuffs, cracks
    rng = np.random.default_rng(300 + k)
    st = smooth(0.9, 1.5, bil(pnoise(400 + k, 2.4, 128), X, Y)) * interior(X, Y, 0.2)
    col = mixc(col, col * 0.35 + hexc('#0e1014') * 0.3, st * 0.8)
    if k % 4 == 1:
        ang = np.abs(((X + Y) * 7) % 1.0 - 0.5) < 0.25
        band = (np.abs(X - 0.5) < 0.30) & (np.abs(Y - 0.2) < 0.045) & ang
        col = np.where(band[..., None], hexc('#a98516') * 0.55, col)
    finish(col, X, Y, f'sand_{k}')

def moss(k):  # 'grass' -> scrubby dead ground / moss over concrete
    X, Y, px, py = grid()
    n1 = noise('g1', 31, 2.0); n2 = noise('g2', 32, 0.7); n3 = noise('g3', 33, 3.2); n4 = noise('g4', 34, 1.4)
    h = bil(n2, X * 2, Y * 2) * 0.5 + bil(n4, X, Y) * 0.4
    conc = hexc('#2b2e2c'); mo = hexc('#2f4a26'); mo2 = hexc('#566a2c'); dead = hexc('#3a3224')
    m = smooth(-0.4, 0.8, bil(n3, X, Y)); m2 = smooth(0.0, 1.3, bil(n1, X * 1.0, Y * 1.0 + 0.2))
    col = mixc(np.broadcast_to(conc, X.shape + (3,)).copy(), mixc(np.broadcast_to(mo, X.shape + (3,)).copy(), np.broadcast_to(dead, X.shape + (3,)).copy(), m2 * 0.7), m)
    col = mixc(col, np.broadcast_to(mo2, X.shape + (3,)).copy(), smooth(0.7, 1.6, bil(n2, X * 1.0 + 0.5, Y)) * 0.35 * m)
    col *= (0.7 + 0.6 * shade(h, X, Y, 6)[..., None]) * (0.9 + 0.1 * bil(n2, X * 3, Y * 3)[..., None])
    # dim bioluminescent speckle (variant specific interior)
    rng = np.random.default_rng(500 + k)
    for _ in range(6 if k % 2 else 3):
        cx, cy = rng.uniform(0.2, 0.8, 2); d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        col += np.exp(-(d / 0.012) ** 2)[..., None] * hexc('#3cffb0') * 0.45 + np.exp(-(d / 0.06) ** 2)[..., None] * hexc('#20a080') * 0.05
    # puddle patches
    pud = smooth(1.1, 1.5, bil(pnoise(600 + k, 2.4, 128), X, Y)) * interior(X, Y, 0.18) * (k % 2)
    col = mixc(col, hexc('#0b1118') + streaks(px, py, 700 + k, 3, 0.25) + hexc('#303a58') * 0.06, pud * 0.8)
    finish(col, X, Y, f'grass_{k}')

def sea(kind, k):
    X, Y, px, py = grid()
    n1 = noise('w1', 41, 2.0); n2 = noise('w2', 42, 1.0); n3 = noise('w3', 43, 3.0); ph = noise('w4', 44, 2.6)
    deep = kind == 'deep'
    c0 = hexc('#07121d') if deep else hexc('#0f2a33'); c1 = hexc('#0c2536') if deep else hexc('#1d4a52')
    t = smooth(-1.0, 1.4, bil(n3, X, Y)); col = mixc(np.broadcast_to(c0, X.shape + (3,)).copy(), np.broadcast_to(c1, X.shape + (3,)).copy(), t)
    # ripples: stretched along screen-x diagonal => sin of periodic phase field
    p = bil(n1, X, Y) * 3.0 + (X + Y) * 6.0 * np.pi * 0 + bil(n2, X * 2, Y * 2)
    rip = 0.5 + 0.5 * np.sin(p * 5.0)
    col *= (0.85 + 0.3 * rip[..., None] ** 2)
    # oily iridescent sheen (periodic phase)
    phase = bil(ph, X, Y) * 0.35
    irid = 0.5 + 0.5 * np.cos(2 * np.pi * (phase[..., None] + np.array([0.0, 0.33, 0.67], 'float32')))
    sh = smooth(0.2, 1.6, bil(n3, X * 1.0 + 0.4, Y * 1.0 + 0.1)) * (0.5 + 0.5 * rip)
    col += irid * sh[..., None] * (0.07 if deep else 0.06) * hexc('#ffffff')
    # specular glints of far neon, variant-specific interior
    rng = np.random.default_rng(900 + k + (50 if deep else 0))
    cols = [hexc('#22eaff'), hexc('#ff2ea6'), hexc('#ffa622')]
    inter = interior(X, Y, 0.2)
    for _ in range(2 + k % 3):
        cx = rng.uniform(25, 105); cy = rng.uniform(14, 52); w = rng.uniform(5, 16); hh = rng.uniform(0.6, 1.3); c = cols[rng.integers(0, 3)]
        gl = np.exp(-(((px - cx) / w) ** 2 + ((py - cy) / 0.9) ** 2)) * hh * 0.35
        col += gl[..., None] * c * inter[..., None]
    if k == 3:   # glowing buoy (centre of tile)
        for (bx, by, c, r) in ((0.5, 0.5, hexc('#ff3a2a') if deep else hexc('#45ff86'), 1.0),):
            d = np.sqrt((X - bx) ** 2 + (Y - by) ** 2)
            col += np.exp(-(d / 0.055) ** 2)[..., None] * c * 0.35 + np.exp(-(d / 0.016) ** 2)[..., None] * c * 1.6
            col *= (1 - 0.5 * np.exp(-((d - 0.06) / 0.03) ** 2)[..., None] * 0)
    if not deep:   # concrete shoal ripples / foam lines faintly
        col += (smooth(0.6, 1.3, bil(n2, X, Y * 1.0)) * 0.04)[..., None] * hexc('#5ac0b0')
    finish(col, X, Y, ('deep_' if deep else 'shallow_') + str(k))

if __name__ == '__main__':
    NV = 8
    for k in range(NV): asphalt(k); concrete(k); moss(k)
    for k in range(6): sea('deep', k); sea('shallow', k)
    print('terrain done')
