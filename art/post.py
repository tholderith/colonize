"""Post: base sprite + split additive glow layer.
 base  : <name>.png            lit render, emissives off, premultiplied Lanczos 2x->1x
 glow  : <name>__glow.png      emission-only render -> small bloom blur -> RGBA with alpha = peak luminance, rgb = colour/alpha
                               (so rgb*alpha reproduces the emission; draw with ADD blend / premultiply rgb by alpha).
Both are cropped with an identical box (union of base alpha, glow, and the footprint diamond) so one anchor serves both."""
import json, os, sys, glob
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "public", "assets")
WORK = os.environ.get("NWORK", "/tmp/colonize_art_work"); SS = 2
GAIN = float(os.environ.get("NGLOW", "1.0"))
SUB = os.path.join(OUT, "buildings")

def blur(a, s): return np.stack([gaussian_filter(a[..., c], s, mode='constant') for c in range(a.shape[2])], -1)

def load(p):
    a = np.asarray(Image.open(p).convert('RGBA')).astype('float32') / 255.0
    return a

def make_glow(a):
    """a: straight RGBA from Blender (emission on black). -> premultiplied emission with slight bloom (float RGB)."""
    pm = a[..., :3] * a[..., 3:4]
    g = pm * 0.8 + blur(pm, 3.0) * 0.7 + blur(pm, 9.0) * 0.45
    return g * GAIN

def premul_resize(pm, size):
    ch = [np.asarray(Image.fromarray(np.ascontiguousarray(pm[..., c]), 'F').resize(size, Image.LANCZOS)) for c in range(pm.shape[2])]
    return np.stack(ch, -1)

def run(only):
    os.makedirs(SUB, exist_ok=True)
    meta = {}
    for f in sorted(glob.glob(os.path.join(WORK, 'raw', '*.json'))):
        m = json.load(open(f))
        if only and m['name'] not in only: continue
        base = load(os.path.join(WORK, 'raw', m['name'] + '.png')); gl = make_glow(load(os.path.join(WORK, 'raw', m['name'] + '__glow.png')))
        W, H = base.shape[1], base.shape[0]; cx, cy = W // 2, H // 2 + m['off']; fw, fh = m['fw'], m['fh']
        sel = (base[..., 3] > 0.02) | (gl.max(-1) > 0.03)
        ys, xs = np.nonzero(sel)
        l, t, r, b = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        l = min(l, cx - 64 * SS * fh - 4); r = max(r, cx + 64 * SS * fw + 4); b = max(b, cy + 2); t = min(t, cy - 32 * SS * (fw + fh) - 2)
        l, t = -((-(l - cx)) // SS) * SS, -((-(t - cy)) // SS) * SS; r, b = -(-(r - cx) // SS) * SS, -(-(b - cy) // SS) * SS
        x0, y0, x1, y1 = cx + l, cy + t, cx + r, cy + b
        def crop(arr):
            pad = np.zeros((y1 - y0, x1 - x0, arr.shape[2]), 'float32')
            sx0, sy0, sx1, sy1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
            pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = arr[sy0:sy1, sx0:sx1]; return pad
        sz = ((x1 - x0) // SS, (y1 - y0) // SS)
        bp = crop(np.concatenate([base[..., :3] * base[..., 3:4], base[..., 3:4]], -1))
        bp = premul_resize(bp, sz).clip(0, 1); al = bp[..., 3:4]
        col = np.where(al > 1e-4, bp[..., :3] / np.maximum(al, 1e-4), 0).clip(0, 1)
        Image.fromarray((np.concatenate([col, al], -1) * 255 + 0.5).astype('uint8'), 'RGBA').save(os.path.join(SUB, m['name'] + '.png'))
        gp = premul_resize(crop(gl), sz).clip(0, 1); ga = gp.max(-1, keepdims=True)
        gc = np.where(ga > 1e-4, gp / np.maximum(ga, 1e-4), 0).clip(0, 1)
        Image.fromarray((np.concatenate([gc, ga], -1) * 255 + 0.5).astype('uint8'), 'RGBA').save(os.path.join(SUB, m['name'] + '_glow.png'))
        meta[m['name']] = dict(file='buildings/%s.png' % m['name'], glow='buildings/%s_glow.png' % m['name'], anchor=[-l // SS, -t // SS], size=list(sz), footprint=[fw, fh])
    mp = os.path.join(HERE, 'out', 'buildings_meta.json'); os.makedirs(os.path.dirname(mp), exist_ok=True)
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    old.update(meta); json.dump(old, open(mp, 'w'), indent=1); print('post done', sorted(meta))

if __name__ == '__main__': run(sys.argv[1:])
