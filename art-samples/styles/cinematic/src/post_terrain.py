"""Downsample the 2x terrain render (premultiplied-free RGB Lanczos), bloom + grade, dither -> terrain_full.png.
Also writes the simple per-tile fallback sprites (deep/shallow/sand/grass/road) that the underlay covers."""
import os, sys, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import grade, bloom
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WORK = os.environ.get('CWORK', '/tmp/cin_work')

def run(name='terrain'):
    im = Image.open(os.path.join(WORK, 'raw', name + '.png')).convert('RGB').resize((1920, 1080), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255.0
    a = bloom(a)
    a = grade(a)
    rng = np.random.default_rng(5)
    a = a + (rng.random(a.shape, dtype=np.float32) - 0.5) / 255.0 * 1.6     # dither against banding
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, 'terrain_full.png'))

def tiles():
    cols = dict(deep_water=(8, 52, 78), shallow_water=(34, 150, 150), sand=(214, 192, 144), grass=(80, 118, 44), road=(120, 92, 60))
    m = np.mgrid[0:64, 0:128]
    yy, xx = m
    msk = (np.abs(xx - 63.5) / 64.0 + np.abs(yy - 31.5) / 32.0) <= 1.0
    for k, c in cols.items():
        arr = np.zeros((64, 128, 4), np.uint8); arr[..., :3] = c; arr[..., 3] = msk * 255
        Image.fromarray(arr, 'RGBA').save(os.path.join(OUT, 'tile_' + k + '.png'))

if __name__ == '__main__':
    tiles(); run(sys.argv[1] if len(sys.argv) > 1 else 'terrain')
