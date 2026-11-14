from art import *

LEATHER = (92, 60, 40); LEATHER_D = (62, 40, 28); GOLD = (196, 158, 84); WAX = (146, 52, 44)

def icon(kind, size=34, seed=3):
    """ink-and-wash resource icon on transparent bg"""
    a = A(size, size, (size // 2, size), seed); s = size / 34
    c = lambda x, y: (x * s, y * s)
    if kind == "gold":
        a.ellipse(c(17, 17), 12 * s, 12 * s, (222, 184, 90), True, 1.3); a.ellipse(c(17, 17), 8 * s, 8 * s, (232, 200, 112), True, .8)
        a.line([c(17, 11), c(17, 23)], 1.3); a.line([c(13, 14), c(21, 14)], 1); a.line([c(13, 20), c(21, 20)], 1)
    elif kind == "wood":
        for k, (x, y) in enumerate([(9, 22), (9, 13), (9, 6)]):
            a.poly([c(x, y), c(x + 17, y), c(x + 17, y + 7), c(x, y + 7)], (180, 136, 90), w=1.1)
            a.ellipse(c(x + 17, y + 3.5), 3 * s, 3.5 * s, (222, 190, 140), True, .8)
            a.line([c(x + 3, y + 3), c(x + 12, y + 3)], .6, INK2)
    elif kind == "bricks":
        for r in range(3):
            for k in range(2 + (r % 2)):
                x = 5 + k * 11 - (5 if r % 2 else 0) + (5 if r % 2 else 0); x = 4 + k * 11 + (5 if r % 2 == 0 else 0)
                y = 22 - r * 8
                if x + 10 <= 31: a.poly([c(x, y), c(x + 10, y), c(x + 10, y + 7), c(x, y + 7)], (190, 100, 72), w=1.0)
    elif kind == "tools":
        a.line([c(8, 28), c(22, 9)], 2.6, (130, 92, 60), 0.2)
        a.poly([c(15, 6), c(27, 8), c(26, 14), c(19, 14)], (170, 172, 168), w=1.1)
        a.line([c(26, 28), c(11, 10)], 2.2, (130, 92, 60), 0.2)
        a.poly([c(5, 8), c(12, 5), c(15, 10), c(8, 12)], (170, 172, 168), w=1.0)
    elif kind == "food":
        for dx in (-5, 0, 5):
            a.line([c(17 + dx * .3, 29), c(17 + dx, 8)], 1.2, (120, 90, 44))
            for j in range(4):
                y = 8 + j * 4; a.poly([c(17 + dx - 3, y + 3), c(17 + dx, y - 1), c(17 + dx + 3, y + 3)], (222, 188, 100), w=.7, grain=0)
        a.line([c(10, 22), c(24, 22)], 1.8, WAX, .2)
    elif kind == "cloth":
        a.poly([c(5, 9), c(29, 9), c(29, 27), c(5, 27)], (150, 160, 190), w=1.1)
        a.hatch([c(5, 9), c(29, 9), c(29, 27), c(5, 27)], 0, 3, alpha=90)
        a.ellipse(c(5, 18), 3 * s, 9 * s, (190, 196, 214), True, 1.0)
        a.line([c(10, 9), c(10, 27)], .6, INK2)
    elif kind == "pop":
        a.poly([c(8, 30), c(26, 30), c(22, 17), c(12, 17)], (150, 78, 64), w=1.1)
        a.ellipse(c(17, 11), 5 * s, 5.5 * s, (232, 200, 160), True, 1.0)
        a.poly([c(9, 8), c(25, 8), c(21, 1), c(13, 1)], (96, 72, 54), w=1.0, grain=0)
    return a

def seal(a, c, r, text=None, col=WAX):
    pts = [(c[0] + (r + (1.2 if k % 2 else -.4)) * math.cos(k / 18 * 6.283), c[1] + (r + (1.2 if k % 2 else -.4)) * math.sin(k / 18 * 6.283)) for k in range(18)]
    a.poly(pts, col, True, 1.0, pool=.35, grain=8)
    a.ellipse(c, r * .66, r * .66, shade(col, 1.12), True, .8)
    if text: a.text(c, text, (r * 1.1, True), (236, 210, 170), "mm")

def frame(a, w, h, bw=8):
    """leather border with gold line around parchment"""
    d = [(0, 0), (w, 0), (w, h), (0, h)]
    a.poly(d, LEATHER, False, grain=18)
    a.hatch(d, 3, 2.2, LEATHER_D, .6, 70)
    inner = [(bw, bw), (w - bw, bw), (w - bw, h - bw), (bw, h - bw)]
    a.poly(inner, (232, 214, 172), False, grain=16)
    # stains
    for _ in range(6):
        x, y = a.rng.uniform(bw + 20, w - bw - 20), a.rng.uniform(bw + 10, h - bw - 10)
        a.ellipse((x, y), a.rng.uniform(14, 40), a.rng.uniform(8, 18), (224, 204, 158), False)
    a.line(inner + [inner[0]], 1.5, INK, .5)
    g = [(bw - 3, bw - 3), (w - bw + 3, bw - 3), (w - bw + 3, h - bw + 3), (bw - 3, h - bw + 3)]
    a.line(g + [g[0]], 1.4, GOLD, .3)
    return inner

STOCK = [("gold", "Gold", 2480), ("wood", "Timber", 143), ("bricks", "Bricks", 62), ("tools", "Tools", 38), ("food", "Provisions", 215), ("cloth", "Cloth", 27), ("pop", "Settlers", 118)]

def topbar(out):
    W_, H_ = 1920, 72
    a = A(W_, H_, (0, 0), 61)
    frame(a, W_, H_, 6)
    # fade bottom shadow
    a.line([(0, H_ - 1), (W_, H_ - 1)], 2, LEATHER_D, 0, alpha=255)
    cell = 190; x0 = 30
    for i, (k, nm, v) in enumerate(STOCK):
        x = x0 + i * (cell + 8)
        cart_ = [(x, 12), (x + cell, 12), (x + cell, 58), (x, 58)]
        a.poly(cart_, (226, 206, 160), True, 1.1, pool=.12)
        a.line([(x + 4, 16), (x + cell - 4, 16), (x + cell - 4, 54), (x + 4, 54), (x + 4, 16)], .6, INK2, .2, alpha=140)
        ic = icon(k, 34, 4 + i)
        seal_c = (x + 28, 35)
        a.ellipse(seal_c, 21, 21, (210, 186, 136), True, 1.0)
        a.im.alpha_composite(ic.im.resize((34 * S, 34 * S)), (int((seal_c[0] - 17) * S), int((seal_c[1] - 17) * S)))
        a.text((x + 56, 24), nm, (11, False, True), INK2)
        a.text((x + 56, 38), f"{v:,}", (19, True), INK)
        if k != "pop":
            a.text((x + cell - 12, 38), "+" + str([12, 4, 1, 0, 6, 1][i]) + "/m" if i < 6 else "", (10, False, True), (84, 110, 70), "ra")
    # year cartouche at right
    x = W_ - 330
    c = [(x, 10), (W_ - 28, 10), (W_ - 28, 62), (x, 62)]
    a.poly(c, (214, 190, 140), True, 1.2)
    a.line([(x + 5, 15), (W_ - 33, 15), (W_ - 33, 57), (x + 5, 57), (x + 5, 15)], .6, INK2, alpha=150)
    a.text(((x + W_ - 28) / 2, 28), "Year 1627", (19, True), INK, "mm")
    a.text(((x + W_ - 28) / 2, 47), "Spring  -  Day 12", (12, False, True), INK2, "mm")
    seal(a, (x - 10, 36), 17, "II")
    a.save(out)

def panel(out):
    W_, H_ = 360, 300
    a = A(W_, H_, (0, 0), 62)
    inner = frame(a, W_, H_, 9)
    # title banner
    ban = [(22, 22), (W_ - 22, 22), (W_ - 34, 50), (W_ - 22, 78 - 28 + 28 - 0), (22, 78)]
    ban = [(20, 20), (W_ - 20, 20), (W_ - 32, 38), (W_ - 20, 56), (20, 56), (32, 38)]
    a.poly(ban, (194, 150, 100), True, 1.3, pool=.3)
    a.text((W_ / 2, 38), "Harbour Warehouse", (19, True), (252, 238, 206), "mm")
    a.text((W_ / 2, 66), "Port Sorrel  -  stock on hand", (11, False, True), INK2, "mm")
    y = 84
    rows = [("wood", "Timber", 143, 400), ("bricks", "Bricks", 62, 400), ("tools", "Tools", 38, 200), ("food", "Provisions", 215, 400), ("cloth", "Cloth", 27, 200)]
    for k, nm, v, cap in rows:
        ic = icon(k, 30, 9)
        a.im.alpha_composite(ic.im.resize((30 * S, 30 * S)), (28 * S, int((y - 2) * S)))
        a.text((70, y + 15), nm, (14, True), INK, "lm")
        bx0, bx1 = 168, 296
        a.poly([(bx0, y + 8), (bx1, y + 8), (bx1, y + 21), (bx0, y + 21)], (214, 192, 146), True, .9, pool=0, grain=0)
        f = bx0 + (bx1 - bx0) * v / cap
        a.poly([(bx0 + 1, y + 9), (f, y + 9), (f, y + 20), (bx0 + 1, y + 20)], (120, 150, 126) if v / cap > .2 else (176, 100, 76), False, pool=.2, grain=0)
        a.hatch([(bx0 + 1, y + 9), (f, y + 9), (f, y + 20), (bx0 + 1, y + 20)], 60, 2.4, alpha=90)
        a.text((W_ - 28, y + 15), str(v), (14, True), INK, "rm")
        a.line([(28, y + 30), (W_ - 28, y + 30)], .5, INK2, .4, alpha=110)
        y += 34
    a.text((28, 262), "Workers: 6/8   Upkeep: 12 gold", (11, False, True), INK2, "lm")
    seal(a, (W_ - 44, 266), 18, "W")
    a.save(out)
