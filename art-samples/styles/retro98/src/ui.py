"""UI overlays drawn at half-res with palette colours only, no font antialiasing (PIL fontmode '1'), then 2x NEAREST."""
import os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from palette import PAL, ramp, nearest
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = '/usr/share/fonts/truetype/dejavu/'
def C(name, t): return tuple(int(v) for v in PAL[int(nearest(ramp(name, t)))])
def S(i, tt=None): return C('ui_stone', i / 11)
def Wd(i): return C('wood', i / 13)
def Gd(i): return C('gold', i / 7)
FONT = lambda n, s: ImageFont.truetype(FD + n, s)

def text(d, xy, s, font, fill, shadow=None, anchor='la'):
    d.fontmode = '1'
    if shadow: d.text((xy[0] + 1, xy[1] + 1), s, font=font, fill=shadow, anchor=anchor)
    d.text(xy, s, font=font, fill=fill, anchor=anchor)
def bevel(d, box, face, light, dark, w=1, inset=False):
    x0, y0, x1, y1 = box; a, b = (dark, light) if inset else (light, dark)
    d.rectangle((x0, y0, x1, y1), fill=face)
    for i in range(w):
        d.line((x0 + i, y0 + i, x1 - i, y0 + i), fill=a); d.line((x0 + i, y0 + i, x0 + i, y1 - i), fill=a)
        d.line((x0 + i, y1 - i, x1 - i, y1 - i), fill=b); d.line((x1 - i, y0 + i, x1 - i, y1 - i), fill=b)
def grain(img, box, ramp_name, lo, hi, seed, horizontal=True, speck=0.0):
    """textured fill: streaky wood / speckled stone from palette ramp entries lo..hi"""
    r = random.Random(seed); x0, y0, x1, y1 = box; px = img.load(); n = {'wood': 14, 'ui_stone': 12}[ramp_name]
    base = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = (y if horizontal else x)
            if k not in base: base[k] = r.uniform(0, 1)
            v = base[k] * 0.6 + r.random() * 0.4 + (speck and r.uniform(-speck, speck))
            px[x, y] = C(ramp_name, (lo + (hi - lo) * v) / (n - 1))
def rivet(d, x, y):
    d.point((x, y), fill=Gd(5)); d.point((x + 1, y), fill=Gd(3)); d.point((x, y + 1), fill=Gd(3)); d.point((x + 1, y + 1), fill=Gd(1))
def gold_line(d, x0, y0, x1, y1):
    d.line((x0, y0, x1, y1), fill=Gd(5)); 
    if y0 == y1: d.line((x0, y0 + 1, x1, y1 + 1), fill=Gd(2))
    else: d.line((x0 + 1, y0, x1 + 1, y1), fill=Gd(2))

# ---- icons (12x12) -----------------------------------------------------------------------------------------------
def icon(img, kind, x, y):
    d = ImageDraw.Draw(img); K = lambda n, t: C(n, t)
    if kind == 'gold':
        d.ellipse((x, y, x + 11, y + 11), fill=Gd(4), outline=Gd(0)); d.ellipse((x + 2, y + 2, x + 9, y + 9), outline=Gd(2)); d.point((x + 3, y + 3), fill=Gd(7)); d.point((x + 4, y + 3), fill=Gd(6)); d.line((x + 5, y + 4, x + 5, y + 7), fill=Gd(2)); d.line((x + 6, y + 4, x + 6, y + 7), fill=Gd(2))
    elif kind == 'wood':
        for k, yy in enumerate((1, 5)):
            d.rectangle((x, y + yy + 1, x + 9, y + yy + 4), fill=Wd(7), outline=Wd(2)); d.ellipse((x + 7, y + yy, x + 11, y + yy + 5), fill=Wd(11), outline=Wd(3)); d.point((x + 9, y + yy + 2), fill=Wd(5))
        d.line((x + 1, y + 3, x + 6, y + 3), fill=Wd(9)); d.rectangle((x + 3, y + 8, x + 11, y + 11), fill=Wd(6), outline=Wd(2)); d.ellipse((x + 8, y + 7, x + 12, y + 11), fill=Wd(11), outline=Wd(3))
    elif kind == 'brick':
        for r, yy in enumerate((1, 5, 9)):
            off = 0 if r % 2 == 0 else 3
            for xx in (-3, 3, 9): 
                x0 = max(x, x + xx + off); x1 = min(x + 11, x + xx + off + 5)
                if x1 > x0: d.rectangle((x0, y + yy, x1, y + yy + 2), fill=C('brick', .5), outline=C('brick', .1)); d.line((x0, y + yy, x1, y + yy), fill=C('brick', 1))
    elif kind == 'tools':
        d.line((x + 2, y + 10, x + 8, y + 3), fill=Wd(6), width=2); d.rectangle((x + 5, y, x + 11, y + 3), fill=C('stone', .55), outline=C('stone', .1)); d.line((x + 6, y + 1, x + 10, y + 1), fill=C('stone', .95))
        d.line((x + 1, y + 2, x + 6, y + 10), fill=C('stone', .5), width=1); d.line((x, y + 1, x + 3, y + 1), fill=C('stone', .8))
    elif kind == 'food':
        d.line((x + 6, y + 11, x + 6, y + 2), fill=Gd(1))
        for i in range(4):
            d.ellipse((x + 2, y + i * 2 + 1, x + 5, y + i * 2 + 3), fill=Gd(5), outline=Gd(2)); d.ellipse((x + 7, y + i * 2 + 1, x + 10, y + i * 2 + 3), fill=Gd(5), outline=Gd(2))
        d.point((x + 6, y), fill=Gd(6))
    elif kind == 'cloth':
        d.polygon([(x, y + 3), (x + 9, y + 1), (x + 11, y + 4), (x + 11, y + 10), (x + 2, y + 11), (x, y + 9)], fill=C('blue', .55), outline=C('blue', 0))
        d.line((x + 1, y + 5, x + 10, y + 4), fill=C('blue', 1)); d.line((x + 1, y + 8, x + 10, y + 7), fill=C('blue', .8)); d.line((x + 2, y + 10, x + 10, y + 9), fill=C('blue', .25))
        d.point((x + 9, y + 2), fill=C('blue', 1))
    elif kind == 'pop':
        d.ellipse((x + 3, y, x + 8, y + 5), fill=C('skin', .7), outline=C('skin', .1)); d.rectangle((x + 4, y, x + 7, y + 1), fill=Wd(4))
        d.polygon([(x + 1, y + 11), (x + 2, y + 6), (x + 9, y + 6), (x + 10, y + 11)], fill=C('red', .55), outline=C('red', 0)); d.line((x + 3, y + 7, x + 8, y + 7), fill=C('red', 1))
    elif kind == 'bread':
        d.ellipse((x, y + 3, x + 11, y + 10), fill=C('ochre', .55), outline=C('ochre', 0))
        for i in (3, 6, 9): d.line((x + i - 1, y + 4, x + i, y + 6), fill=C('ochre', 1))
    elif kind == 'barrel':
        d.rectangle((x + 1, y + 1, x + 10, y + 10), fill=Wd(6), outline=Wd(2)); d.line((x + 1, y + 3, x + 10, y + 3), fill=C('stone', .2)); d.line((x + 1, y + 8, x + 10, y + 8), fill=C('stone', .2)); d.line((x + 3, y + 2, x + 3, y + 9), fill=Wd(9))

RES = [('gold', '1250'), ('wood', '342'), ('brick', '118'), ('tools', '24'), ('food', '530'), ('cloth', '76'), ('pop', '214')]
def topbar():
    W, H = 960, 36; img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img)
    grain(img, (0, 0, W - 1, H - 1), 'wood', 1.5, 6, 7)
    d.line((0, 0, W, 0), fill=Wd(10)); d.line((0, 1, W, 1), fill=Wd(8))
    d.rectangle((0, H - 5, W - 1, H - 1), fill=S(5)); d.line((0, H - 5, W, H - 5), fill=S(9)); d.line((0, H - 1, W, H - 1), fill=S(1)); d.line((0, H - 4, W, H - 4), fill=S(8))
    d.line((0, H - 6, W, H - 6), fill=Gd(5)); d.line((0, H - 7, W, H - 7), fill=Gd(2))
    fb = FONT('DejaVuSerif-Bold.ttf', 11); fs = FONT('DejaVuSerif-Italic.ttf', 10)
    # town plaque
    bevel(d, (6, 4, 150, 26), S(3), S(9), S(0)); bevel(d, (9, 7, 147, 23), Wd(2), Wd(5), Wd(0), inset=True)
    text(d, (78, 15), 'Port Halcyon', fb, Gd(6), C('night', 0), 'mm'); rivet(d, 7, 5); rivet(d, 142, 5); rivet(d, 7, 21); rivet(d, 142, 21)
    x = 166
    for k, (ic, v) in enumerate(RES):
        w = 68 if k else 72
        bevel(d, (x, 5, x + w, 26), S(4), S(10), S(0), inset=True); d.rectangle((x + 2, 7, x + w - 2, 24), fill=C('night', .12))
        d.line((x + 2, 7, x + w - 2, 7), fill=C('night', 0))
        bevel(d, (x + 3, 8, x + 18, 23), S(6), S(9), S(2), inset=False); icon(img, ic, x + 5, 10)
        text(d, (x + w - 5, 15), v, fb, S(11), C('night', 0), 'rm'); x += w + 5
    # date + pause
    bevel(d, (x + 6, 4, x + 152, 26), S(3), S(9), S(0)); d.rectangle((x + 9, 7, x + 149, 23), fill=C('night', .1))
    text(d, (x + 80, 15), 'Spring, A.D. 1612', fs, S(10), C('night', 0), 'mm')
    bx = x + 160
    for i, lab in enumerate(('II', '>', '>>')):
        bevel(d, (bx + i * 26, 5, bx + i * 26 + 22, 24), S(5), S(10), S(1), 2 if False else 1)
        if lab == 'II': d.rectangle((bx + 7, 10, bx + 9, 19), fill=Gd(5)); d.rectangle((bx + 13, 10, bx + 15, 19), fill=Gd(5))
        else:
            for j in range(len(lab)): d.polygon([(bx + i * 26 + 6 + j * 6, 10), (bx + i * 26 + 6 + j * 6, 19), (bx + i * 26 + 11 + j * 6, 14)], fill=Gd(5))
    print('topbar x end', bx + 3 * 26, 'of', W)
    img.resize((W * 2, H * 2), Image.NEAREST).convert('RGBA').save(f'{OUT}/ui_topbar.png')

def panel():
    W, H = 180, 150; img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img)
    grain(img, (0, 0, W - 1, H - 1), 'ui_stone', 3, 7, 3, False, .05)
    bevel(d, (0, 0, W - 1, H - 1), S(5), S(10), S(0), 2); d.rectangle((0, 0, W - 1, H - 1), outline=S(0))
    d.rectangle((6, 6, W - 7, H - 7), outline=Gd(2)); d.rectangle((5, 5, W - 6, H - 6), outline=Gd(5)); 
    for (x, y) in ((3, 3), (W - 6, 3), (3, H - 6), (W - 6, H - 6)): rivet(d, x, y)
    fb = FONT('DejaVuSerif-Bold.ttf', 11); fs = FONT('DejaVuSerif.ttf', 9); fi = FONT('DejaVuSerif-Italic.ttf', 9)
    # title banner (dark wood)
    grain(img, (10, 10, W - 11, 27), 'wood', 1, 5, 11); bevel(d, (10, 10, W - 11, 27), Wd(3), Wd(9), Wd(0), 1)
    img.paste(Image.new('RGB', (1, 1)), (0, 0)); grain(img, (11, 11, W - 12, 26), 'wood', 1, 5, 11)
    text(d, (W // 2, 19), 'Harbour Warehouse', fb, Gd(7), C('night', 0), 'mm')
    d.line((10, 30, W - 11, 30), fill=S(1)); d.line((10, 31, W - 11, 31), fill=S(10))
    text(d, (14, 34), 'Stock held in store:', fi, S(0))
    rows = [('wood', 'Timber', 342, .68), ('brick', 'Bricks', 118, .24), ('tools', 'Tools', 24, .08), ('food', 'Provisions', 530, 1.0), ('cloth', 'Cloth', 76, .3)]
    y = 46
    for ic, nm, v, fr in rows:
        d.rectangle((12, y, W - 13, y + 14), fill=C('night', .22)); d.line((12, y + 14, W - 13, y + 14), fill=S(10)); d.line((W - 13, y, W - 13, y + 14), fill=S(10)); d.line((12, y, W - 13, y), fill=C('night', 0))
        bevel(d, (14, y + 1, 27, y + 13), C('night', .1), S(8), S(0), 1, True); icon(img, ic, 15, y + 1) if False else None
        sub = Image.new('RGB', (12, 12)); icon(sub, ic, 0, 0); img.paste(sub, (15, y + 1))
        text(d, (32, y + 7), nm, fs, S(10), None, 'lm')
        bx0, bx1 = 92, 134; d.rectangle((bx0, y + 4, bx1, y + 10), fill=C('night', .1), outline=S(0))
        wfill = int((bx1 - bx0 - 2) * fr); 
        if wfill > 0:
            d.rectangle((bx0 + 1, y + 5, bx0 + 1 + wfill, y + 9), fill=C('grass', .55 if fr < 1 else .3) if fr < .9 else C('orange', .6)); d.line((bx0 + 1, y + 5, bx0 + 1 + wfill, y + 5), fill=C('grass', .85) if fr < .9 else C('orange', 1))
        text(d, (W - 16, y + 7), str(v), fb, Gd(6), None, 'rm'); y += 16
    d.line((10, y + 1, W - 11, y + 1), fill=S(1)); d.line((10, y + 2, W - 11, y + 2), fill=S(10))
    text(d, (14, y + 6), 'Capacity', fi, S(0)); text(d, (W - 14, y + 6), '1090 / 1500', fs, S(0), None, 'ra')
    img.resize((W * 2, H * 2), Image.NEAREST).convert('RGBA').save(f'{OUT}/ui_panel.png')
if __name__ == '__main__': topbar(); panel()
