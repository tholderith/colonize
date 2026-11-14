"""Raw Blender passes -> palette-quantised, binary-alpha, 2x NEAREST sprites. Usage: python3 post.py [prefixes]"""
import json, os, sys, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PAL, nearest, floyd, BAYER8
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WORK = os.environ.get("R98WORK", "/tmp/retro98_work"); SS = 2
def lanczos_premul(a, size):
    rgb = a[..., :3] * a[..., 3:4]; arr = np.concatenate([rgb, a[..., 3:4]], -1)
    ch = [np.asarray(Image.fromarray(arr[..., c].copy(), 'F').resize(size, Image.LANCZOS)) for c in range(4)]
    arr = np.stack(ch, -1).clip(0, 1); al = arr[..., 3:4]
    return np.where(al > 1e-4, arr[..., :3] / np.maximum(al, 1e-4), 0).clip(0, 1), al[..., 0]
def sat(c, k=1.22):
    g = c.mean(-1, keepdims=True); return np.clip(g + (c - g) * k, 0, 1)
def load(meta):
    n = meta['name']; W, H = meta['W'], meta['H']; Wh, Hh = W // SS, H // SS
    A = np.asarray(Image.open(f"{WORK}/raw/{n}_obj.png").convert('RGBA')).astype('float32') / 255
    col, al = lanczos_premul(A, (Wh, Hh)); op = al >= 0.5
    sh = np.zeros((Hh, Wh), bool)
    if meta.get('shadow', True):
        B = np.asarray(Image.open(f"{WORK}/raw/{n}_shd.png").convert('RGBA')).astype('float32') / 255
        s = np.where(A[..., 3] < 0.5, B[..., 3], 0).reshape(Hh, SS, Wh, SS).mean((1, 3))
        thr = (BAYER8[np.mgrid[0:Hh, 0:Wh][0] % 8, np.mgrid[0:Hh, 0:Wh][1] % 8] + 0.5)          # 0..1 ordered threshold
        # solid core where shadow is strong, Bayer-stippled penumbra
        sh = ((s > 0.40) | ((s > 0.12) & (s / 0.40 > thr * 0.95 + 0.05))) & ~op
    sx, sy = W // 2 // SS, (H // 2 + meta['off']) // SS      # footprint south-corner in half-res canvas
    return col, op, sh, (sx, sy)
def run(only):
    metas = [json.load(open(f)) for f in sorted(glob.glob(f"{WORK}/raw/*.json"))]
    metas = [m for m in metas if not only or any(m['name'].startswith(o) for o in only)]
    groups = {}
    for m in metas:
        n = m['name']; key = n.rsplit('_', 1)[0] if n.rsplit('_', 1)[-1].isdigit() else n; groups.setdefault(key, []).append(m)
    mp = f"{HERE}/sprites_meta.json"; meta_out = json.load(open(mp)) if os.path.exists(mp) else {}
    for key, ms in groups.items():
        data = []; box = None
        for m in ms:
            col, op, sh, (sx, sy) = load(m); any_ = op | sh; ys, xs = np.where(any_)
            b = (xs.min() - sx, ys.min() - sy, xs.max() + 1 - sx, ys.max() + 1 - sy)
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
            data.append((m, col, op, sh, sx, sy))
        files = []
        for m, col, op, sh, sx, sy in sorted(data, key=lambda d: d[0]['name']):
            sl = (slice(sy + box[1], sy + box[3]), slice(sx + box[0], sx + box[2]))
            c = sat(col[sl]) * 255; o = op[sl]; s = sh[sl]
            q = floyd(c, o); img = np.zeros(o.shape + (4,), np.uint8); img[..., :3] = q; img[..., 3] = o * 255
            scol = PAL[int(nearest(np.array(tuple(int(m['shadow_col'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)), float)))] if m.get('shadow_col') else (0, 0, 0)
            img[s, :3] = scol; img[s, 3] = 255
            im = Image.fromarray(img, 'RGBA').resize((img.shape[1] * 2, img.shape[0] * 2), Image.NEAREST)
            fn = m['name'] + '.png'; im.save(f"{OUT}/{fn}"); files.append(fn)
        meta_out[key] = dict(files=files, anchor=[int(-box[0] * 2), int(-box[1] * 2)], flat=bool(ms[0].get('flat')))
    json.dump(meta_out, open(mp, 'w'), indent=1); print('post done', list(groups))
if __name__ == '__main__': run(sys.argv[1:])
