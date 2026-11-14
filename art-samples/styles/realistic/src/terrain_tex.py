"""System python: build lattice-periodic procedural terrain textures (colour + height) so that the
sprite for index k = (7x+13y) % N continues seamlessly into its neighbours (see SPEC variant rule)."""
import numpy as np, os, sys, json
from PIL import Image
WORK = os.environ.get("RWORK", "/tmp/realistic_work")
N = 16
R = 400             # texture px for (1+2*OV) tile units
OV = 0.06

def lattice():
    c = [(dx, dy) for dx in range(-N, N + 1) for dy in range(-N, N + 1) if (dx, dy) != (0, 0) and (7 * dx + 13 * dy) % N == 0]
    c.sort(key=lambda v: v[0] ** 2 + v[1] ** 2)
    b1 = c[0]
    for v in c[1:]:
        if abs(b1[0] * v[1] - b1[1] * v[0]) == N: b2 = v; break
    B = np.array([[b1[0], b2[0]], [b1[1], b2[1]]], float)
    D = np.linalg.inv(B).T            # columns = dual basis
    return D
D = lattice()

class Field:
    """random Fourier field, periodic over the lattice; band [fmin,fmax] cycles per tile"""
    def __init__(self, seed, fmin, fmax, K=260, power=1.0, aniso=None):
        rng = np.random.default_rng(seed)
        M = int(fmax * 6) + 4
        mm, nn = np.meshgrid(np.arange(-M, M + 1), np.arange(-M, M + 1))
        k = D[:, 0][None, None, :] * mm[..., None] + D[:, 1][None, None, :] * nn[..., None]
        mag = np.hypot(k[..., 0], k[..., 1])
        sel = (mag >= fmin) & (mag <= fmax)
        ks = k[sel]; mg = mag[sel]
        if aniso is not None:     # (dir angle, stretch): favour waves travelling along a direction
            ang = np.arctan2(ks[:, 1], ks[:, 0]); w = np.exp(np.cos(2 * (ang - aniso[0])) * aniso[1])
            p = w / w.sum()
        else:
            p = np.ones(len(ks)) / len(ks)
        idx = rng.choice(len(ks), size=min(K, len(ks)), replace=False, p=p)
        self.k = ks[idx]; mg = mg[idx]
        self.a = mg ** (-power); self.ph = rng.uniform(0, 2 * np.pi, len(idx))
        self.a = self.a / np.sqrt((self.a ** 2).sum() / 2)       # unit std
    def __call__(self, X, Y):
        """X (1D, game x), Y (1D game y) -> 2D array [len(Y), len(X)]"""
        ex = np.exp(2j * np.pi * np.outer(X, self.k[:, 0]))            # (nx,K)
        ey = np.exp(2j * np.pi * np.outer(Y, self.k[:, 1])) * (self.a * np.exp(1j * self.ph))[None, :]
        return (ey @ ex.T).real

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def lerp(a, b, t): return a + (b - a) * t[..., None]

def rgb(h): 
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) / 255 for i in (0, 2, 4)])

def tile_origin(k):
    for s in range(0, 40):
        for x0 in range(0, s + 1):
            y0 = s - x0
            if (7 * x0 + 13 * y0) % N == k: return x0 + 100, y0 + 100      # offset away from 0 (no effect on periodic)
    raise SystemExit("no origin")

# ------------------------------------------------------------------ terrain types
class Types:
    def __init__(s):
        s.g_low = Field(1, 0.4, 2.2, 120, 1.2); s.g_mid = Field(2, 3, 12, 220, 1.0); s.g_hi = Field(3, 18, 60, 500, 0.4)
        s.g_blade = Field(30, 40, 90, 700, 0.1)
        s.s_low = Field(4, 0.4, 2.5, 120, 1.2); s.s_mid = Field(5, 3, 10, 160, 1.0); s.s_hi = Field(6, 25, 70, 500, 0.3)
        s.s_rip = Field(7, 3.5, 9, 120, 0.3, aniso=(0.5, 3.0))
        s.r_low = Field(8, 0.5, 2.5, 120, 1.2); s.r_mid = Field(9, 3, 12, 200, 1.0); s.r_hi = Field(10, 20, 80, 600, 0.3)
        s.w_low = Field(11, 0.5, 2.2, 120, 1.3); s.w_mid = Field(12, 2, 7, 220, 1.0, aniso=(0.7, 1.8)); s.w_hi = Field(13, 8, 26, 450, 0.8)
        s.sh_low = Field(14, 0.5, 2.0, 120, 1.3); s.sh_mid = Field(15, 2, 6, 220, 1.0); s.sh_hi = Field(16, 6, 18, 450, 0.8)
        s.sh_cau = Field(17, 3, 9, 300, 0.2); s.sh_bed = Field(18, 6, 30, 400, 0.6)

    def grass(s, X, Y):
        lo = s.g_low(X, Y); mid = s.g_mid(X, Y); hi = s.g_hi(X, Y); bl = s.g_blade(X, Y)
        t = np.clip(0.5 + 0.20 * lo + 0.10 * mid, 0, 1)
        dark, light, dry = rgb('#36481f'), rgb('#6d8034'), rgb('#8c8744')
        col = lerp(dark, light, t)
        dryf = smoothstep(0.55, 1.4, lo * 0.7 + mid * 0.5 - 0.1)
        col = lerp(col, dry, dryf * 0.5)
        hh = 0.5 + 0.20 * mid + 0.55 * hi + 0.35 * bl
        ao = np.clip(0.55 + 0.9 * (hh - 0.3), 0.35, 1.35)
        col = col * ao[..., None]
        # tiny clover / daisy specks
        spk = smoothstep(2.35, 2.9, hi + 0.5 * bl)
        col = lerp(col, rgb('#b8b27a'), spk * 0.55)
        # bare soil patches
        soil = smoothstep(1.3, 1.9, mid * 0.6 - lo * 0.9 + hi * 0.15)
        col = lerp(col, rgb('#5c4a33'), soil * 0.35)
        return col.clip(0, 1), hh

    def sand(s, X, Y):
        lo = s.s_low(X, Y); mid = s.s_mid(X, Y); hi = s.s_hi(X, Y); rp = s.s_rip(X, Y)
        t = np.clip(0.5 + 0.2 * lo + 0.12 * mid, 0, 1)
        col = lerp(rgb('#c0a674'), rgb('#e3cb94'), t)
        wet = smoothstep(0.2, 1.3, lo * 0.9 + mid * 0.35)
        col = lerp(col, rgb('#9a8358'), wet * 0.38)
        grains = 0.9 + 0.12 * hi
        col = col * grains[..., None]
        peb = smoothstep(2.4, 3.1, hi + 0.6 * mid)
        col = lerp(col, rgb('#6e6659'), peb * 0.6)
        hh = 0.5 + 0.18 * rp + 0.06 * hi + 0.25 * peb
        col = col * (0.88 + 0.12 * np.clip(rp, -1.5, 1.5)[..., None] * 0.6 + 0.0)
        return col.clip(0, 1), hh

    def road(s, X, Y):
        lo = s.r_low(X, Y); mid = s.r_mid(X, Y); hi = s.r_hi(X, Y)
        t = np.clip(0.5 + 0.22 * lo + 0.15 * mid, 0, 1)
        col = lerp(rgb('#6f5436'), rgb('#a28560'), t)
        peb = smoothstep(1.7, 2.4, hi + 0.6 * mid)
        stone = lerp(rgb('#847560'), rgb('#b8ab8f'), np.clip(0.5 + 0.3 * mid, 0, 1))
        col = lerp(col, stone, peb * 0.85)
        mud = smoothstep(0.4, 1.4, -lo * 0.8 - mid * 0.4)
        col = lerp(col, rgb('#5a4630'), mud * 0.25)
        col = col * (0.88 + 0.1 * hi)[..., None]
        # dusty grass fringes
        gr = smoothstep(1.2, 2.0, lo * 0.5 + hi * 0.3 - mid * 0.3)
        col = lerp(col, rgb('#53603a'), gr * 0.35)
        hh = 0.45 + 0.12 * mid + 0.1 * hi + 0.5 * peb
        return col.clip(0, 1), hh

    def deep(s, X, Y):
        lo = s.w_low(X, Y); mid = s.w_mid(X, Y); hi = s.w_hi(X, Y)
        hh = 0.5 + 0.55 * lo + 0.5 * mid + 0.18 * hi
        t = np.clip(0.5 + 0.18 * lo + 0.12 * mid, 0, 1)
        col = lerp(rgb('#04262c'), rgb('#0a4349'), t)
        crest = smoothstep(1.4, 2.4, mid + 0.6 * hi)
        col = lerp(col, rgb('#6fa3a6'), crest * 0.22)
        return col.clip(0, 1), hh

    def shallow(s, X, Y):
        lo = s.sh_low(X, Y); mid = s.sh_mid(X, Y); hi = s.sh_hi(X, Y); cau = s.sh_cau(X, Y); bed = s.sh_bed(X, Y)
        depth = np.clip(0.5 + 0.16 * lo + 0.08 * mid, 0, 1)
        bedcol = lerp(rgb('#c8b88a'), rgb('#9a9272'), np.clip(0.5 + 0.2 * bed, 0, 1))
        cc = np.clip(1.0 - np.abs(np.sin(np.pi * (cau * 0.5 + 0.75))), 0, 1) ** 4
        bedcol = bedcol * (0.82 + 0.6 * cc)[..., None]
        water = lerp(rgb('#128a8a'), rgb('#0a5560'), depth)
        a = 0.66 + 0.28 * depth
        col = lerp(bedcol, water, a)
        hh = 0.5 + 0.3 * mid + 0.4 * hi + 0.15 * lo
        return col.clip(0, 1), hh

def main(only=None):
    os.makedirs(os.path.join(WORK, 'tex'), exist_ok=True)
    T = Types()
    xs0 = np.linspace(-OV, 1 + OV, R)
    for typ in ['grass', 'sand', 'road', 'deep', 'shallow']:
        if only and typ not in only: continue
        for k in range(N):
            x0, y0 = tile_origin(k)
            X = x0 + xs0
            Y = (y0 + 1 + OV) - np.linspace(0, 1 + 2 * OV, R)     # row 0 = top of image = +Blender Y = smaller game y... see terrain.py
            Y = (y0 + 1 + OV) - np.linspace(0, 1 + 2 * OV, R)     # image row j -> game y decreasing (blender +Y up)
            col, h = getattr(T, typ)(X, Y)
            col8 = (col * 255 + 0.5).astype(np.uint8)
            Image.fromarray(col8[::-1], 'RGB').save(os.path.join(WORK, 'tex', f'{typ}_{k}_c.png'))      # flipped: Blender image origin bottom-left
            h = np.clip(h, 0, 1)
            Image.fromarray((h[::-1] * 65535).astype(np.uint16)).save(os.path.join(WORK, 'tex', f'{typ}_{k}_h.png'))
        print('tex', typ, flush=True)
if __name__ == '__main__':
    main(sys.argv[1:])
