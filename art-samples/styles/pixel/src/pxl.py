"""Pixel helpers: native-res sprite canvas, iso boxes/roofs, outline, shadow, upscale."""
import random
from PIL import Image, ImageDraw
from palette import *

SCALE = 2  # native px -> final px (nearest)

def hsh(*a):
    return random.Random(hash(a) & 0xffffffff)

class Spr:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        s.d = ImageDraw.Draw(s.im)
    def px(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h: s.im.putpixel((int(x), int(y)), tuple(c) + (255,))
    def poly(s, pts, c): s.d.polygon([(int(round(x)), int(round(y))) for x, y in pts], fill=tuple(c) + (255,))
    def line(s, a, b, c): s.d.line([(int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1])))], fill=tuple(c) + (255,))
    def rect(s, x0, y0, x1, y1, c): s.d.rectangle([x0, y0, x1, y1], fill=tuple(c) + (255,))
    def ell(s, x0, y0, x1, y1, c): s.d.ellipse([x0, y0, x1, y1], fill=tuple(c) + (255,))
    def blob(s, cx, cy, rx, ry, ramp_, hi=-1):
        """shaded ellipse: dark body, lighter upper-left crescent."""
        s.ell(cx - rx, cy - ry, cx + rx, cy + ry, ramp_[0])
        s.ell(cx - rx, cy - ry, cx + rx - 1, cy + ry - 1, ramp_[1])
        s.ell(cx - rx + 1, cy - ry + 1, cx + rx - 2, cy + ry - 2, ramp_[2])
        if len(ramp_) > 3 and rx > 3:
            s.ell(cx - rx + 1, cy - ry + 1, cx + rx - 4, cy + ry - 4, ramp_[3])

    def outline(s, col=INK, diag=False):
        src = s.im.copy(); P = src.load(); o = s.im.load()
        for y in range(s.h):
            for x in range(s.w):
                if P[x, y][3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < s.w and 0 <= ny < s.h and P[nx, ny][3] == 255:
                            o[x, y] = tuple(col) + (255,); break
    def shadow(s, cx, cy, hw, dx=5):
        """translucent footprint shadow under (composited beneath)."""
        sh = Image.new('RGBA', (s.w, s.h), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
        d.polygon([(cx + dx, cy - hw // 2), (cx + dx + hw, cy), (cx + dx, cy + hw // 2), (cx + dx - hw, cy)], fill=SHADOW_RGBA)
        sh.alpha_composite(s.im); s.im = sh; s.d = ImageDraw.Draw(s.im)
    def final(s):
        return s.im.resize((s.w * SCALE, s.h * SCALE), Image.NEAREST)

def M(name): return MAT[name]

# ---------------------------------------------------------------- iso boxes
def corners(cx, cy, hw, up=0):
    hh = hw // 2
    return (cx, cy - hh - up), (cx + hw, cy - up), (cx, cy + hh - up), (cx - hw, cy - up)  # T R B L

def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

def face(p0, p1, up, u0=0, u1=1, v0=0, v1=1):
    """sub-rect of vertical face from base edge p0->p1 rising `up` px."""
    a = lerp(p0, p1, u0); b = lerp(p0, p1, u1)
    return [(a[0], a[1] - up * v0), (b[0], b[1] - up * v0), (b[0], b[1] - up * v1), (a[0], a[1] - up * v1)]

def iso_box(s, cx, cy, hw, h, mat, top=None, texture='plank', lit=(2, 1), base=0):
    """mat ramp dark->light. left wall uses lit[0], right wall lit[1], top uses 3."""
    T, R, B, L = corners(cx, cy - base, hw)
    s.poly([L, B, (B[0], B[1] - h), (L[0], L[1] - h)], mat[lit[0]])
    s.poly([B, R, (R[0], R[1] - h), (B[0], B[1] - h)], mat[lit[1]])
    T2, R2, B2, L2 = corners(cx, cy - base, hw, h)
    s.poly([T2, R2, B2, L2], top or mat[3])
    # courses
    if texture:
        step = 3 if texture == 'plank' else 4
        for k in range(step, h, step):
            dk = mat[max(0, lit[0] - 1)]
            s.line((L[0] + 1, L[1] - k), (B[0] - 1, B[1] - k - 1), dk)
            s.line((B[0] + 1, B[1] - k), (R[0] - 1, R[1] - k + 1), mat[max(0, lit[1] - 1)])
            if texture == 'brick':
                for j in range(0, hw, 6):
                    ofs = (k // 4 % 2) * 3
                    xx = L[0] + 2 + j + ofs
                    if xx < B[0] - 1: s.px(xx, L[1] - k + (xx - L[0]) // 2 - 3, dk)
    # edges
    s.line((B[0], B[1]), (B[0], B[1] - h), mat[0])
    s.line((L2[0], L2[1]), (B2[0], B2[1]), mat[4])
    s.line((T2[0], T2[1]), (L2[0], L2[1]), mat[4])
    return T, R, B, L

def window(s, p0, p1, up, u, v, wmat=None, w=0.18, hgt=5):
    q = face(p0, p1, 1, u, u + w, 0, 1)
    a = lerp(p0, p1, u); b = lerp(p0, p1, u + w)
    y0 = v; y1 = v + hgt
    s.poly([(a[0], a[1] - y0), (b[0], b[1] - y0), (b[0], b[1] - y1), (a[0], a[1] - y1)], M('glass')[2])
    s.poly([(a[0], a[1] - y0 - 0), (a[0] + (b[0] - a[0]) / 2, a[1] + (b[1] - a[1]) / 2 - y0), (a[0] + (b[0] - a[0]) / 2, a[1] + (b[1] - a[1]) / 2 - y1), (a[0], a[1] - y1)], M('glass')[3])
    s.line((a[0], a[1] - y1 - 1), (b[0], b[1] - y1 - 1), wmat or M('timber')[4])
    s.line((a[0], a[1] - y0 + 1), (b[0], b[1] - y0 + 1), wmat or M('timber')[4])

def door(s, p0, p1, u, w=0.2, hgt=8, mat=None):
    mat = mat or M('timber')
    a = lerp(p0, p1, u); b = lerp(p0, p1, u + w)
    s.poly([(a[0], a[1]), (b[0], b[1]), (b[0], b[1] - hgt), (a[0], a[1] - hgt)], mat[1])
    s.poly([(a[0], a[1]), (a[0] + (b[0] - a[0]) / 2, a[1] + (b[1] - a[1]) / 2), (a[0] + (b[0] - a[0]) / 2, a[1] + (b[1] - a[1]) / 2 - hgt + 1), (a[0], a[1] - hgt + 1)], mat[2])
    s.px(b[0] - 1, b[1] - hgt // 2, M('gold')[3])

def gable_roof(s, cx, cy, hw, h, rh, mat, orient=0, over=2, wallmat=None, shade=(3, 2, 1)):
    """gabled roof atop box (h = wall height). rh = ridge rise."""
    T, R, B, L = corners(cx, cy, hw + over, h)
    T0, R0, B0, L0 = corners(cx, cy, hw, h)
    def up(p, k): return (p[0], p[1] - k)
    if orient == 0:
        r1 = up(lerp(L0, T0, .5), rh); r2 = up(lerp(B0, R0, .5), rh)
        # extend ridge slightly past gable
        # gable end (on right wall) filled with wall colour
        if wallmat: s.poly([B0, R0, r2], wallmat[1])
        s.poly([L, B, up(lerp(B, R, .5 - over / (hw * 2.5)), rh) if False else (r2[0] + over, r2[1] + over // 2 + 0), (r1[0] - over, r1[1] - over // 2)], mat[shade[0] - 1 if False else 3])
        # shingle lines
        A, Bq = (L[0], L[1]), (B[0], B[1])
        n = 0
        for k in range(1, rh + 2, 3):
            t = k / (rh + 2)
            a = lerp(L, (r1[0] - over, r1[1] - over // 2), t); b = lerp(B, (r2[0] + over, r2[1] + over // 2), t)
            s.line((a[0] + 1, a[1]), (b[0] - 1, b[1]), mat[2])
        s.line((r1[0] - over, r1[1] - over // 2), (r2[0] + over, r2[1] + over // 2), mat[4])
        s.line((L[0], L[1] + 1), (B[0], B[1] + 1), mat[0])
        s.line((B[0], B[1] + 1), (R[0], R[1] + 1), mat[0] if False else (wallmat[0] if wallmat else mat[0]))
        s.line((R0[0] + 1, R0[1]), (r2[0] + over, r2[1] + over // 2), mat[1])
        s.line((B0[0] + 0, B0[1]), (r2[0], r2[1]), mat[1])
        return r1, r2
    else:
        r1 = up(lerp(T0, R0, .5), rh); r2 = up(lerp(L0, B0, .5), rh)
        if wallmat: s.poly([L0, B0, r2], wallmat[2])
        s.poly([(r2[0] - over, r2[1] + over // 2), (r1[0] + over, r1[1] - over // 2), R, B], mat[2])
        for k in range(1, rh + 2, 3):
            t = k / (rh + 2)
            a = lerp(B, (r2[0] - over, r2[1] + over // 2), t); b = lerp(R, (r1[0] + over, r1[1] - over // 2), t)
            s.line((a[0] + 1, a[1]), (b[0] - 1, b[1]), mat[1])
        s.line((r1[0] + over, r1[1] - over // 2), (r2[0] - over, r2[1] + over // 2), mat[4])
        s.line((B[0], B[1] + 1), (R[0], R[1] + 1), mat[0])
        s.line((L0[0] - 1, L0[1]), (r2[0] - over, r2[1] + over // 2), mat[3])
        s.line((B0[0], B0[1]), (r2[0], r2[1]), mat[3])
        return r1, r2

def hip_roof(s, cx, cy, hw, h, rh, mat, over=2):
    T, R, B, L = corners(cx, cy, hw + over, h)
    ap = (cx, cy - h - rh - (hw // 2) // 2 * 0)
    s.poly([L, B, ap], mat[3]); s.poly([B, R, ap], mat[2])
    s.line(L, ap, mat[4]); s.line(B, ap, mat[1])
    s.line((L[0], L[1] + 1), (B[0], B[1] + 1), mat[0]); s.line((B[0], B[1] + 1), (R[0], R[1] + 1), mat[0])
    return ap

def chimney(s, x, y, hgt=7, mat=None):
    mat = mat or M('stone')
    s.rect(x, y - hgt, x + 3, y, mat[2]); s.rect(x + 2, y - hgt, x + 3, y, mat[1]); s.rect(x, y - hgt, x + 3, y - hgt, mat[4])
