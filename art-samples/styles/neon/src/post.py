"""Post: add cheap bloom from emissive pixels, crop to group bbox (+footprint diamond), premultiplied Lanczos 2x->1x, write sprites + meta."""
import json, os, sys, glob
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WORK = os.environ.get("NWORK", "/tmp/neon_work"); SS = 2
GLOW = float(os.environ.get("NGLOW", "1.0"))

def blur(arr, r):
    from scipy.ndimage import gaussian_filter
    return np.stack([gaussian_filter(arr[..., c].astype('float32'), r, mode='constant') for c in range(arr.shape[2])], -1)

def add_bloom(im):
    a = np.asarray(im).astype('float32') / 255.0
    rgb, al = a[..., :3], a[..., 3:4]
    mx = rgb.max(-1, keepdims=True)
    m = np.clip((mx - 0.6) / 0.3, 0, 1) * np.clip(al * 1.5, 0, 1)
    # emitters: strong saturated or near-white; weight by saturation to keep warm grey highlights quieter
    src = rgb * m
    g = blur(src, 4) * 0.8 + blur(src, 14) * 0.9 + blur(src, 36) * 0.9
    g *= GLOW
    pm = rgb * al
    out = 1 - (1 - np.clip(pm, 0, 1)) * (1 - np.clip(g, 0, 1))     # screen blend, premultiplied
    ga = np.clip(g.max(-1, keepdims=True) * 1.1, 0, 1)
    al2 = 1 - (1 - al) * (1 - ga)
    col = np.where(al2 > 1e-4, out / np.maximum(al2, 1e-4), 0).clip(0, 1)
    return np.concatenate([col, al2], -1)

def premul_resize(arr, size):
    rgb = arr[..., :3] * arr[..., 3:4]
    p = np.concatenate([rgb, arr[..., 3:4]], -1)
    ch = [np.asarray(Image.fromarray(p[..., c].astype('float32').copy(), 'F').resize(size, Image.LANCZOS)) for c in range(4)]
    p = np.stack(ch, -1).clip(0, 1); al = p[..., 3:4]
    col = np.where(al > 1e-4, p[..., :3] / np.maximum(al, 1e-4), 0).clip(0, 1)
    return Image.fromarray((np.concatenate([col, al], -1) * 255 + 0.5).astype('uint8'), 'RGBA')

def group_of(n):
    p = n.rsplit('_', 1); return p[0] if len(p) == 2 and p[1].isdigit() else n

def run(only):
    metas = []
    for f in sorted(glob.glob(os.path.join(WORK, 'raw', '*.json'))):
        m = json.load(open(f))
        if only and not any(m['name'].startswith(o) for o in only): continue
        metas.append(m)
    data = {}; boxes = {}
    for m in metas:
        im = Image.open(os.path.join(WORK, 'raw', m['name'] + '.png')).convert('RGBA')
        arr = add_bloom(im); W, H = im.size; cx, cy = W // 2, H // 2 + m['off']
        a8 = (arr[..., 3] > 0.02)
        ys, xs = np.nonzero(a8)
        l, t, r, b = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        fw, fh = m['fw'], m['fh']
        l = min(l, cx - 64 * SS * fh - 4); r = max(r, cx + 64 * SS * fw + 4); b = max(b, cy + 2); t = min(t, cy - 32 * SS * (fw + fh) - 2)
        boxes[m['name']] = (l - cx, t - cy, r - cx, b - cy); data[m['name']] = (arr, (cx, cy), m)
    groups = {}
    for n, bx in boxes.items():
        g = group_of(n); u = groups.get(g)
        groups[g] = bx if u is None else (min(u[0], bx[0]), min(u[1], bx[1]), max(u[2], bx[2]), max(u[3], bx[3]))
    mp = os.path.join(HERE, 'sprites_meta.json')
    nm = json.load(open(mp)) if os.path.exists(mp) else {}
    for n, (arr, (cx, cy), m) in data.items():
        l, t, r, b = groups[group_of(n)]
        l = -((-l) // SS) * SS; t = -((-t) // SS) * SS; r = -(-r // SS) * SS; b = -(-b // SS) * SS
        H, W = arr.shape[:2]
        x0, y0, x1, y1 = cx + l, cy + t, cx + r, cy + b
        pad = np.zeros((y1 - y0, x1 - x0, 4), 'float32')
        sx0, sy0, sx1, sy1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
        pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = arr[sy0:sy1, sx0:sx1]
        im = premul_resize(pad, (pad.shape[1] // SS, pad.shape[0] // SS))
        im.save(os.path.join(OUT, n + '.png'))
        nm[n] = dict(size=list(im.size), anchor=[-l // SS, -t // SS], flat=bool(m.get('flat')))
    json.dump(nm, open(mp, 'w'), indent=1); print('post done', len(nm))

if __name__ == '__main__': run(sys.argv[1:])
