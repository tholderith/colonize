"""System-python post-process: crop raw Blender renders (2x) to alpha bbox (+footprint diamond), premultiplied Lanczos
downsample to 1x, write final sprite PNGs and sprites_meta.json (anchors)."""
import json, os, sys, glob, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WORK = os.environ.get("RWORK", "/tmp/realistic_work"); SS = 2

def premul_resize(im, size):
    a = np.asarray(im).astype('float32') / 255.0
    rgb = a[..., :3] * a[..., 3:4]
    arr = np.concatenate([rgb, a[..., 3:4]], -1)
    ch = [np.asarray(Image.fromarray(arr[..., c].copy(), 'F').resize(size, Image.LANCZOS)) for c in range(4)]
    arr = np.stack(ch, -1).clip(0, 1); al = arr[..., 3:4]
    col = np.where(al > 1e-4, arr[..., :3] / np.maximum(al, 1e-4), 0).clip(0, 1)
    return Image.fromarray((np.concatenate([col, al], -1) * 255 + 0.5).astype('uint8'), 'RGBA')

def bbox_rel(meta):
    n = meta['name']; fw, fh, W, H = meta['fw'], meta['fh'], meta['W'], meta['H']
    im = Image.open(os.path.join(WORK, 'raw', n + '.png')).convert('RGBA')
    cx, cy = W // 2, H // 2 + meta.get('off', 0)
    a = im.split()[3].point(lambda v: 255 if v > 5 else 0)
    l, t, r, b = a.getbbox() or (cx - 4, cy - 4, cx + 4, cy + 4)
    if meta.get('terrain'):
        l, t, r, b = cx - 66 * SS, cy - 66 * SS, cx + 66 * SS, cy + 2 * SS
    elif meta.get('diamond', True):
        l = min(l, cx - 64 * SS * fh); r = max(r, cx + 64 * SS * fw); b = max(b, cy)
        t = min(t, cy - 32 * SS * (fw + fh))
    p = 0 if meta.get('terrain') else 2 * SS
    return im, (l - cx - p, t - cy - p, r - cx + p, b - cy + p), (cx, cy)

def group_of(n):
    parts = n.rsplit('_', 1)
    return parts[0] if len(parts) == 2 and parts[1].isdigit() else n

def run(only):
    metas = []
    for f in sorted(glob.glob(os.path.join(WORK, 'raw', '*.json'))):
        m = json.load(open(f))
        if only and not any(m['name'].startswith(o) for o in only): continue
        metas.append(m)
    boxes = {}; ims = {}
    for m in metas:
        im, bx, c = bbox_rel(m); boxes[m['name']] = bx; ims[m['name']] = (im, c, m)
    groups = {}
    for n, bx in boxes.items():
        g = group_of(n); u = groups.get(g)
        groups[g] = bx if u is None else (min(u[0], bx[0]), min(u[1], bx[1]), max(u[2], bx[2]), max(u[3], bx[3]))
    mp = os.path.join(OUT, 'src', 'sprites_meta.json')
    nm = json.load(open(mp)) if os.path.exists(mp) else {}
    for n, (im, (cx, cy), m) in ims.items():
        l, t, r, b = groups[group_of(n)]
        l = -((-l) // SS) * SS; t = -((-t) // SS) * SS; r = -(-r // SS) * SS; b = -(-b // SS) * SS
        W, H = im.size
        if m.get('terrain'):
            yy, xx = np.mgrid[0:H, 0:W]
            msk = (np.abs(xx - cx) / (64.0 * SS) + np.abs(yy - (cy - 32.0 * SS)) / (32.0 * SS)) <= 1.05
            arr = np.asarray(im).copy(); arr[..., 3] = (arr[..., 3] * msk).astype(np.uint8); im = Image.fromarray(arr, 'RGBA')
        box = (cx + l, cy + t, cx + r, cy + b)
        crop = im.crop(box)
        crop = premul_resize(crop, (crop.width // SS, crop.height // SS))
        crop.save(os.path.join(OUT, n + '.png'))
        nm[n] = dict(size=list(crop.size), anchor=[-l // SS, -t // SS], flat=bool(m.get('flat')))
    json.dump(nm, open(mp, 'w'), indent=1)
    print('post done', len(nm))

if __name__ == '__main__':
    run(sys.argv[1:])
