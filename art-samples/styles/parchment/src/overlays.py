"""Full-screen overlays: chart ink (coast, contours, compass) and paper grain+vignette."""
import json, os
from art import *
from scipy.ndimage import gaussian_filter, distance_transform_edt

def top(x, y): return 960 + (x - y) * 64, -72 + (x + y) * 32

def chart_ink(layout, out):
    lay = json.load(open(layout))
    Wd, Hd = 1920, 1080; sc = 2
    m = Image.new("L", (Wd // sc, Hd // sc), 0); d = ImageDraw.Draw(m)
    ter = lay["terrain"]
    for y, row in enumerate(ter):
        for x, ch in enumerate(row):
            if ch in "BGR":
                tx, ty = top(x, y)
                d.polygon([(tx / sc, ty / sc), ((tx + 64) / sc, (ty + 32) / sc), (tx / sc, (ty + 64) / sc), ((tx - 64) / sc, (ty + 32) / sc)], fill=255)
    land = np.array(m) > 128
    rng = np.random.RandomState(5)
    f = gaussian_filter(land.astype(float), 5)
    nz = gaussian_filter(rng.randn(*land.shape), 9); nz = nz / nz.std()
    f2 = gaussian_filter(land.astype(float), 3)
    # signed distance (px, at half-res) with wobble
    dist = distance_transform_edt(~land) - distance_transform_edt(land)
    dist = gaussian_filter(dist, 3) + nz * 1.6
    # protect pier/ship areas
    prot = np.zeros(land.shape, bool)
    for o in lay["objects"]:
        if o["sprite"] in ("ship", "pier"):
            fw = 2 if o["sprite"] == "ship" else 1
            tx, ty = top(o["x"] + fw - 1, o["y"] + fw - 1)
            yy, xx = np.ogrid[:land.shape[0], :land.shape[1]]
            r = 150 if fw == 2 else 70
            prot |= ((xx * sc - tx) ** 2 + ((yy * sc - (ty - 20)) * 1.6) ** 2) < r * r
    def band(level, wpx):
        return (np.abs(dist - level) < wpx) & ~prot
    big = lambda a_: np.array(Image.fromarray((a_ * 255).astype("uint8")).resize((Wd, Hd), Image.BICUBIC)).astype(float) / 255
    rgba = np.zeros((Hd, Wd, 4), float)
    def paint(mask, col, alpha):
        mm = big(gaussian_filter(mask.astype(float), .7))
        a_ = mm * alpha
        for i in range(3): rgba[..., i] = rgba[..., i] * (1 - a_) + col[i] * a_ if False else np.where(a_ > rgba[..., 3], col[i], rgba[..., i])
        rgba[..., 3] = np.maximum(rgba[..., 3], a_)
    # shore wash (sand tint) just offshore, verdigris contour lines, then ink coast
    paint((dist > 0) & (dist < 7) & ~prot, (232, 214, 160), .35)
    for lvl, al, wd in ((12, .5, .8), (20, .4, .7), (30, .32, .7), (42, .24, .6)):
        # dashed contour: modulate by noise
        mk = band(lvl, wd) & (gaussian_filter(rng.randn(*land.shape), 2) > -.35)
        paint(mk, (70, 100, 92), al)
    paint(band(0.0, 1.1), INK, .92)
    paint(band(-3.0, .5) & (gaussian_filter(rng.randn(*land.shape), 1.5) > .3), INK2, .5)
    im = Image.fromarray(np.clip(rgba, 0, 255).astype("uint8"), "RGBA")
    # compass rose in the top-right water, hand drawn on a small supersampled canvas
    a = A(220, 220, (0, 0), 77)
    cx, cy, R = 110, 118, 70
    for k in range(32):
        t = k / 32 * 6.283; rr = R * (1.0 if k % 8 == 0 else .62 if k % 4 == 0 else .38)
        a.line([(cx, cy), (cx + math.sin(t) * rr, cy - math.cos(t) * rr)], .7, INK, .3, alpha=170)
    for k in range(4):
        t = k * 1.5708
        tip = (cx + math.sin(t) * R * 1.15, cy - math.cos(t) * R * 1.15)
        l = (cx + math.sin(t - .35) * R * .22, cy - math.cos(t - .35) * R * .22); rr_ = (cx + math.sin(t + .35) * R * .22, cy - math.cos(t + .35) * R * .22)
        a.poly([tip, l, (cx, cy)], (226, 206, 150) if k % 2 else INK, True, .9, grain=0)
        a.poly([tip, rr_, (cx, cy)], INK if k % 2 else (226, 206, 150), True, .9, grain=0)
    for rad, w_, al in ((.98, 1.1, 255), (.88, .6, 150)):
        pts = [(cx + math.cos(t / 60 * 6.283) * R * rad, cy + math.sin(t / 60 * 6.283) * R * rad) for t in range(61)]
        a.line(pts, w_, INK, .3, alpha=al)
    a.text((cx, cy - R * 1.15 - 12), "N", (18, True), INK, "mm")
    comp = a.im.resize((220, 220), Image.LANCZOS)
    im.alpha_composite(comp, (1630, 140))
    im.save(out)

def paper(out):
    Wd, Hd = 1920, 1080
    rng = np.random.RandomState(11)
    g = gaussian_filter(rng.randn(Hd, Wd), 1.0)
    fibre = gaussian_filter(rng.randn(Hd, Wd), (0.6, 6)) * 3
    blot = gaussian_filter(rng.randn(Hd // 4, Wd // 4), 18); blot = np.kron(blot / blot.std(), np.ones((4, 4)))[:Hd, :Wd]
    yy, xx = np.mgrid[:Hd, :Wd]
    v = ((xx - Wd / 2) / (Wd / 2)) ** 2 * .9 + ((yy - Hd / 2) / (Hd / 2)) ** 2 * .9
    vig = np.clip(v - .35, 0, 1) ** 1.3
    # dark (ink-brown) alpha: grain + stains + vignette
    alpha = np.abs(g) * 9 + np.abs(fibre) * 3 + np.clip(blot, 0, 3) * 5 + vig * 120
    img = np.zeros((Hd, Wd, 4), "uint8")
    img[..., 0], img[..., 1], img[..., 2] = 74, 50, 30
    img[..., 3] = np.clip(alpha, 0, 255).astype("uint8")
    # warm light haze (paper glow) as lighter specks
    Image.fromarray(img, "RGBA").save(out)
