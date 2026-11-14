"""Own 256-colour palette for 'Pre-rendered 98'. Built from hand-picked colour ramps (shadows lean violet/blue,
lights lean yellow, like hand-tuned 8-bit palettes). Exposes PAL (256x3 uint8), ramp(name,t), nearest(), quantize helpers."""
import numpy as np, os

def _interp(anchors, n):
    a = np.array(anchors, float); xs = np.linspace(0, 1, len(a)); t = np.linspace(0, 1, n)
    return [tuple(int(round(np.interp(ti, xs, a[:, c]))) for c in range(3)) for ti in t]

RAMPS = [  # name, count, anchors dark->light
 ("sea",      16, [(8,26,84),(16,66,160),(36,116,214),(96,176,240),(168,214,250)]),
 ("lagoon",   14, [(18,88,140),(36,150,184),(96,206,206),(190,240,226)]),
 ("foam",      4, [(200,228,244),(230,246,252),(255,255,255)]),
 ("grass",    18, [(20,56,30),(46,112,34),(92,160,44),(156,198,66),(212,224,108)]),
 ("leaf",     12, [(12,40,34),(28,88,40),(58,134,48),(112,172,60)]),
 ("sand",     12, [(112,84,60),(188,148,98),(232,206,150),(252,238,194)]),
 ("earth",    10, [(56,38,32),(108,76,50),(158,120,80),(198,162,112)]),
 ("wood",     14, [(34,20,18),(84,48,28),(140,88,46),(196,138,74),(234,190,114)]),
 ("tile",     10, [(66,16,22),(138,38,28),(196,68,38),(232,114,66)]),
 ("brick",     8, [(92,38,34),(158,74,52),(206,122,88)]),
 ("plaster",  10, [(86,84,112),(172,170,182),(232,224,208),(255,250,238)]),
 ("ochre",     8, [(112,68,32),(192,128,50),(234,184,92),(250,226,152)]),
 ("stone",    12, [(28,32,46),(84,88,102),(150,150,152),(210,208,198)]),
 ("slate",     6, [(34,44,66),(76,92,122),(132,152,174)]),
 ("thatch",    8, [(90,68,30),(150,120,50),(204,172,86),(238,216,134)]),
 ("gold",      8, [(110,68,12),(190,138,20),(240,200,50),(255,242,156)]),
 ("hay",      10, [(136,90,12),(212,158,26),(244,208,66),(255,238,134)]),
 ("skin",      6, [(110,58,42),(180,108,76),(228,166,122),(250,208,168)]),
 ("red",       5, [(112,18,30),(186,38,44),(240,96,84)]),
 ("blue",      5, [(18,36,108),(40,82,178),(112,152,230)]),
 ("teal",      4, [(14,76,70),(40,138,112)]),
 ("yellow",    4, [(198,156,28),(250,222,72)]),
 ("purple",    4, [(66,28,90),(132,72,152)]),
 ("orange",    5, [(160,64,20),(236,138,48)]),
 ("shadow",    6, [(22,36,30),(44,66,48),(64,92,62)]),
 ("night",     6, [(10,10,24),(36,34,62),(70,66,98)]),
 ("ui_stone", 12, [(26,22,24),(66,60,58),(118,110,100),(170,160,140),(218,208,182)]),
]
def build():
    cols = []
    for name, n, anc in RAMPS: cols += _interp(anc, n)
    cols += [(0,0,0),(255,255,255)]
    k = 256 - len(cols); assert k >= 0, len(cols)
    cols += _interp([(18,18,20),(120,120,126),(238,238,240)], k)   # neutral greys fill the rest
    return np.array(cols[:256], np.uint8)
PAL = build()
_idx = {}
o = 0
for name, n, _ in RAMPS: _idx[name] = (o, n); o += n
def ramp(name, t):
    """colour (float rgb 0..255) from named ramp at t in 0..1 (piecewise-linear between the palette entries)"""
    o, n = _idx[name]; seg = PAL[o:o+n].astype(float); t = np.clip(t, 0, 1) * (n - 1)
    i = np.minimum(t.astype(int), n - 2) if isinstance(t, np.ndarray) else min(int(t), n - 2)
    f = t - i
    if isinstance(t, np.ndarray): return seg[i] * (1 - f)[..., None] + seg[i + 1] * f[..., None]
    return seg[i] * (1 - f) + seg[i + 1] * f

W = np.array([0.30, 0.55, 0.15])  # luma-ish weights
def nearest(rgb):
    """rgb (...,3) float -> palette indices"""
    d = ((rgb[..., None, :] - PAL.astype(float)) ** 2 * W).sum(-1)
    return d.argmin(-1)

BAYER8 = np.array([[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
                   [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]) / 64.0 - 0.5
def ordered(rgb, spread=22):
    """ordered (Bayer 8x8) dither of an HxWx3 float image. Pattern is position-locked => tiles stay seamless."""
    H, Wd = rgb.shape[:2]
    b = np.tile(BAYER8, (H // 8 + 1, Wd // 8 + 1))[:H, :Wd, None] * spread
    return PAL[nearest(np.clip(rgb + b, 0, 255))]

def floyd(rgb, mask, strength=0.85):
    """serpentine Floyd-Steinberg on masked pixels only (error never leaks from/into transparent pixels)."""
    H, Wd = mask.shape; img = rgb.astype(float).copy(); out = np.zeros((H, Wd, 3), np.uint8)
    for y in range(H):
        xs = range(Wd) if y % 2 == 0 else range(Wd - 1, -1, -1); d = 1 if y % 2 == 0 else -1
        for x in xs:
            if not mask[y, x]: continue
            old = np.clip(img[y, x], 0, 255); i = nearest(old); new = PAL[i]; out[y, x] = new
            e = (old - new) * strength
            for dx, dy, w in ((d, 0, 7/16), (-d, 1, 3/16), (0, 1, 5/16), (d, 1, 1/16)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < Wd and yy < H and mask[yy, xx]: img[yy, xx] += e * w
    return out

if __name__ == '__main__':
    from PIL import Image
    im = Image.new('RGB', (16 * 16, 16 * 16))
    for i, c in enumerate(PAL): im.paste(tuple(int(v) for v in c), ((i % 16) * 16, (i // 16) * 16, (i % 16) * 16 + 16, (i // 16) * 16 + 16))
    im.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'palette_preview.png'))
