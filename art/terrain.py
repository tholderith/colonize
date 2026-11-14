"""Neon Foundry terrain: periodic numpy textures -> 132x68 iso tiles (anchor [66,66]). All variants of a type share the same
periodic base field (identical edges) and add variant-specific detail only in the tile interior, so tiles seam perfectly."""
import numpy as np, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "public", "assets")
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

NZ = {}; CUR = [0]
def noise(name, seed, beta=2.0):
    key = (name, CUR[0])
    if key not in NZ: NZ[key] = pnoise(seed + 131 * CUR[0], beta)
    return NZ[key]


WALL = 14   # seawall height in px: water tiles are drawn WALL px lower than the land plane; the wall face fills the gap.
def grid(extra=0):
    W, H = TW * SSF, (TH + extra) * SSF
    px, py = np.meshgrid((np.arange(W) + 0.5) / SSF, (np.arange(H) + 0.5) / SSF)
    X = (((px - AX) / 64.0) + ((py - (AY - 64)) / 32.0)) / 2.0
    Y = (((py - (AY - 64)) / 32.0) - ((px - AX) / 64.0)) / 2.0
    return X, Y, px, py

def save(rgb, al, name, sub='tiles'):
    arr = np.concatenate([np.clip(rgb, 0, 1), al[..., None]], -1).astype('float32')
    pm = arr.copy(); pm[..., :3] *= pm[..., 3:4]; H = pm.shape[0] // SSF
    ch = [np.asarray(Image.fromarray(np.ascontiguousarray(pm[..., c]), 'F').resize((TW, H), Image.LANCZOS)) for c in range(4)]
    pm = np.stack(ch, -1).clip(0, 1); a = pm[..., 3:4]
    col = np.clip(np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0), 0, 1); a = np.clip(a * 1.6, 0, 1)
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    Image.fromarray((np.concatenate([col, a], -1) * 255 + 0.5).astype('uint8'), 'RGBA').save(os.path.join(OUT, sub, name + '.png'))
    return H

def diamond_mask(X, Y, ov=(0.04, 0.04, 0.04, 0.04)):
    """ov = overscan per edge (N,E,S,W) in tile units; X grows E, Y grows S."""
    n, e, s, w = ov
    return ((X >= -w) & (X <= 1 + e) & (Y >= -n) & (Y <= 1 + s)).astype('float32')
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


def land_rgb(X, Y, px, py):
    n1 = noise('g1', 31, 2.0); n2 = noise('g2', 32, 0.7); n3 = noise('g3', 33, 3.2); n4 = noise('g4', 34, 1.4)
    h = bil(n2, X * 2, Y * 2) * 0.5 + bil(n4, X, Y) * 0.4
    conc = hexc('#3a3d38'); mo = hexc('#37592b'); mo2 = hexc('#6a8434'); dead = hexc('#453b29')
    sh = X.shape + (3,); B = lambda c: np.broadcast_to(c, sh).copy()
    m = 0.5 + (smooth(-0.4, 0.8, bil(n3, X, Y)) - 0.5) * 0.8; m2 = 0.5 + (smooth(0.0, 1.3, bil(n1, X, Y + 0.2)) - 0.5)
    col = mixc(B(conc), mixc(B(mo), B(dead), m2 * 0.7), m)
    col = mixc(col, B(mo2), smooth(0.7, 1.6, bil(n2, X + 0.5, Y)) * 0.35 * m)
    col *= (0.75 + 0.6 * shade(h, X, Y, 6)[..., None]) * (0.9 + 0.1 * bil(n2, X * 3, Y * 3)[..., None])
    rng = np.random.default_rng(500)
    for _ in range(4):   # dim bioluminescent speckle
        cx, cy = rng.uniform(0.2, 0.8, 2); d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        col += np.exp(-(d / 0.012) ** 2)[..., None] * hexc('#3cffb0') * 0.45 + np.exp(-(d / 0.06) ** 2)[..., None] * hexc('#20a080') * 0.05
    return col

def land():
    X, Y, px, py = grid(); save(land_rgb(X, Y, px, py), diamond_mask(X, Y), 'land'); return 'land'

def road():
    """M0 revision: lighter cool steel plating + bright amber studs/dashes + dark tile-edge bevel => reads clearly on dark moss."""
    X, Y, px, py = grid()
    big = noise('r3', 13, 3.0); fine = noise('r2', 12, 0.9); base = noise('r1', 11, 2.2)
    h = bil(fine, X, Y) * 0.5 + bil(base, X, Y) * 0.3
    col = np.broadcast_to(hexc('#6b7485'), X.shape + (3,)).copy()
    col = col * (0.88 + 0.12 * bil(big, X, Y)[..., None] + 0.04 * bil(fine, X * 2, Y * 2)[..., None])
    col *= (0.85 + 0.3 * shade(h, X, Y, 6)[..., None])
    cu = np.abs(((X * 2) % 1.0) - 0.5); cv = np.abs(((Y * 2) % 1.0) - 0.5)
    seam = (np.minimum(0.5 - cu, 0.5 - cv) < 0.012).astype('float32'); col = col * (1 - 0.4 * seam[..., None])
    rv = ((((X * 2) % 1.0 - 0.07) ** 2 + ((Y * 2) % 1.0 - 0.07) ** 2) < 0.0007).astype('float32'); col += rv[..., None] * 0.12
    e = np.minimum(np.minimum(X, 1 - X), np.minimum(Y, 1 - Y)); col *= (1 - 0.45 * smooth(0.05, 0.0, e))[..., None]   # dark edge bevel
    for ax in (0, 1):    # broken yellow dashes along both axes
        t = X if ax == 0 else Y; o = Y if ax == 0 else X
        dash = (np.abs(o - 0.5) < 0.022) & (((t * 4) % 1.0) < 0.55) & (((t * 4) % 1.0) > 0.1) & (np.abs(t - 0.5) > 0.12)
        col = np.where(dash[..., None], hexc('#f0c030'), col)
    for (cx, cy) in ((0.5, 0.5), (0.0, 0.5), (1.0, 0.5), (0.5, 0.0), (0.5, 1.0)):
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        col += np.exp(-(d / 0.04) ** 2)[..., None] * hexc('#ffc040') * 1.2 + np.exp(-(d / 0.08) ** 2)[..., None] * hexc('#ff8a10') * 0.12
    save(col, diamond_mask(X, Y), 'road'); return 'road'

def water(kind):
    deep = kind == 'deep'; CUR[0] = 40 if deep else 0
    # water is drawn WALL px lower than the land plane: shift the lattice so the diamond sits at rows [WALL, WALL+64)
    X, Y, px, py = grid(0); pad = WALL * SSF
    n1 = noise('w1', 41, 2.0); n2 = noise('w2', 42, 1.0); n3 = noise('w3', 43, 3.0); ph = noise('w4', 44, 2.6)
    c0 = hexc('#07121d') if deep else hexc('#12323c'); c1 = hexc('#0c2536') if deep else hexc('#235a64')
    sh = X.shape + (3,)
    t = 0.5 + (smooth(-1.0, 1.4, bil(n3, X * 2, Y * 2)) - 0.5) * 0.6
    col = mixc(np.broadcast_to(c0, sh).copy(), np.broadcast_to(c1, sh).copy(), t)
    p = bil(n1, X * 2, Y * 2) * 2.0 + bil(n2, X * 2, Y * 2); rip = 0.5 + 0.5 * np.sin(p * 5.0)
    col *= (0.88 + 0.22 * rip[..., None] ** 2)
    irid = 0.5 + 0.5 * np.cos(2 * np.pi * (bil(ph, X, Y)[..., None] * 0.35 + np.array([0.0, 0.33, 0.67], 'float32')))
    col += irid * (smooth(0.2, 1.6, bil(n3, X * 2 + 0.4, Y * 2 + 0.1)) * (0.5 + 0.5 * rip))[..., None] * 0.06
    rng = np.random.default_rng(900 + deep); cols = [hexc('#22eaff'), hexc('#ff2ea6'), hexc('#ffa622')]; inter = interior(X, Y, 0.2)
    for _ in range(3):
        cx = rng.uniform(25, 105); cy = rng.uniform(14, 52); w = rng.uniform(5, 16)
        col += (np.exp(-(((px - cx) / w) ** 2 + ((py - cy) / 0.9) ** 2)) * 0.25)[..., None] * cols[rng.integers(0, 3)] * inter[..., None]
    full = np.zeros((X.shape[0] + pad, X.shape[1], 3), 'float32'); al = np.zeros(full.shape[:2], 'float32')
    full[pad:] = col; al[pad:] = diamond_mask(X, Y, (0.03,) * 4)
    save(full, al, 'deep_water' if deep else 'shallow_water')

def wall_tex(t, d, face):
    """concrete seawall: t = along-edge coordinate in tile units (periodic, period 1), d = depth px 0..WALL."""
    nn = pnoise(80 + face, 2.0, 256); a = bil(nn, t % 1.0, d / 40.0 % 1.0)
    base = hexc('#6a6c70') if face == 0 else hexc('#5a6068')
    col = base * (0.85 + 0.1 * a[..., None])
    col = col * np.array([1.12, 0.98, 0.84], 'float32') if face == 0 else col * np.array([0.84, 0.97, 1.15], 'float32')   # sodium on E face, moon on S face
    joint = (np.abs(((t * 4) % 1.0) - 0.0) < 0.012) | (np.abs(((t * 4) % 1.0) - 1.0) < 0.012)
    col = np.where(joint[..., None], col * 0.6, col)
    col *= (1.0 - 0.45 * smooth(WALL * 0.45, WALL, d))[..., None]  # darken toward waterline
    kerb = smooth(5.0, 0.0, d)                      # lit kerb: cyan light spilling down from the lip
    col += kerb[..., None] * hexc('#22eaff') * 0.55
    col = np.where((d > WALL - 1.6)[..., None], col * 0.5 + hexc('#38a0b0') * 0.35, col)   # wet foam line at the water
    return col

def shore(mask):
    """mask bits: N=1 E=2 S=4 W=8 (1 = that neighbour is water)."""
    X, Y, px, py = grid(WALL)
    base = land_rgb(X, Y, px, py)
    ov = tuple(0.0 if mask & b else 0.04 for b in (1, 2, 4, 8))
    top = diamond_mask(X, Y, ov); col = base.copy(); al = top.copy()
    kw = 0.05    # lit kerb strip on the top face along every water-facing edge
    for bit, dist in ((1, Y), (2, 1 - X), (4, 1 - Y), (8, X)):
        if mask & bit:
            lip = smooth(kw, 0.0, dist); core = smooth(0.016, 0.0, dist)
            col = col * (1 - 0.35 * lip[..., None]) + core[..., None] * hexc('#9af4ff') * 0.9 + lip[..., None] * hexc('#22eaff') * 0.18
    cx, cy = AX, AY - 32
    if mask & 2:   # E wall face: below the E->S edge
        Ye = 1 - (px - cx) / 64.0; d = py - (cy + 32 * Ye); m = (px >= cx) & (px <= cx + 64) & (d >= 0) & (d < WALL)
        wc = wall_tex(np.clip(Ye, 0, 1), np.clip(d, 0, WALL), 0); col = np.where(m[..., None], wc, col); al = np.maximum(al, m.astype('float32'))
    if mask & 4:   # S wall face: below the S->W edge
        Xs = 1 - (cx - px) / 64.0; d = py - (cy + 32 * Xs); m = (px >= cx - 64) & (px <= cx) & (d >= 0) & (d < WALL)
        wc = wall_tex(np.clip(Xs, 0, 1), np.clip(d, 0, WALL), 1); col = np.where(m[..., None], wc, col); al = np.maximum(al, m.astype('float32'))
    save(col, al, 'shore_%d' % mask)

if __name__ == '__main__':
    land(); road(); water('deep'); water('shallow')
    for k in range(16): shore(k)
    print('terrain done')
