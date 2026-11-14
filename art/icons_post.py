"""Downsize WORK/icon_<good>.png (256 px) -> public/assets/ui/icons/<good>.png (32) and <good>@2x.png (64), premultiplied Lanczos."""
import os, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "public", "assets", "ui", "icons")
WORK = os.environ.get("NWORK", "/tmp/colonize_art_work"); os.makedirs(OUT, exist_ok=True)
def down(a, n):
    pm = np.concatenate([a[..., :3] * a[..., 3:4], a[..., 3:4]], -1)
    pm = np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(pm[..., c]), 'F').resize((n, n), Image.LANCZOS)) for c in range(4)], -1).clip(0, 1)
    al = pm[..., 3:4]; col = np.where(al > 1e-4, pm[..., :3] / np.maximum(al, 1e-4), 0).clip(0, 1)
    return Image.fromarray((np.concatenate([col, al], -1) * 255 + 0.5).astype('uint8'), 'RGBA')


for f in sorted(glob.glob(os.path.join(WORK, 'icon_*.png'))):
    n = os.path.basename(f)[5:-4]; a = np.asarray(Image.open(f).convert('RGBA')).astype('float32') / 255
    down(a, 64).save(os.path.join(OUT, n + '@2x.png')); down(a, 32).save(os.path.join(OUT, n + '.png'))
print('icons post done')
