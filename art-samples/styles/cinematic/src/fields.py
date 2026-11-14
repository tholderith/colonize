"""Cinematic style - step 1 (numpy): turn scene/layout.json tile classes into CONTINUOUS world fields.

Everything is computed on a fine raster over world domain [X0, X0+N) in game-tile units (gx, gy continuous;
tile (x,y) covers [x,x+1]x[y,y+1]).  Outputs (to $CWORK/fields):
  color.png   8-bit sRGB albedo of the ground (land + seabed, caustics/seagrass baked in)
  depth.png   16-bit: water depth  (0..DMAX tiles-units) of the sea above the seabed (0 on land)
  foam.png    16-bit: shoreline foam / surf mask
  wet.png     16-bit: wet-sand mask (lowers roughness)
  height.f32  raw float32 heightfield (R x R) in blender units (z up), also used for the mesh
  info.json   domain info + building footprint list
"""
import json, os, numpy as np
from scipy import ndimage as ndi
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WORK = os.environ.get('CWORK', '/tmp/cin_work')
FD = os.path.join(WORK, 'fields'); os.makedirs(FD, exist_ok=True)

X0, N, R = -11.0, 42, 64          # domain origin (tiles), size (tiles), pixels per tile
S = N * R
DMAX = 3.0                          # depth encoded in depth.png (z-units)
rng = np.random.default_rng(1608)

lay = json.load(open(os.path.join(ROOT, 'scene', 'layout.json')))
W_, H_ = lay['width'], lay['height']
T = lay['terrain']

# ------------------------------------------------------------------ helpers
def fbm(scale, octaves=4, seed=0, gain=0.5, shape=(S, S)):
    """smooth value noise in [0,1]; scale = feature size in tiles"""
    r = np.random.default_rng(seed + 1000 * octaves)
    out = np.zeros(shape, np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        cells = max(2, int(N / scale * (2 ** o)) + 3)
        g = r.random((cells, cells)).astype(np.float32)
        z = ndi.zoom(g, (shape[0] / (cells - 1) * 1.0, shape[1] / (cells - 1) * 1.0), order=3, mode='reflect', grid_mode=False)
        z = z[:shape[0], :shape[1]]
        if z.shape != shape: z = np.pad(z, ((0, shape[0] - z.shape[0]), (0, shape[1] - z.shape[1])), mode='edge')
        out += z * amp; tot += amp; amp *= gain
    out /= tot
    out = (out - out.min()) / (out.max() - out.min() + 1e-9)
    return out
def grain(sigma, seed):
    r = np.random.default_rng(seed)
    g = ndi.gaussian_filter(r.standard_normal((S, S)).astype(np.float32), sigma)
    return g / (g.std() + 1e-9)
def sstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0, 1); return t * t * (3 - 2 * t)
def mix(a, b, t):
    t = t[..., None] if t.ndim == 2 else t
    return a * (1 - t) + b * t
def col(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.0

# ------------------------------------------------------------------ class raster (fine, nearest) + padding with deep sea
cls = np.full((N * 2, N * 2), 'D')   # we use 2 samples/tile only for the coarse class grid; rasterise later
def class_mask(chars):
    m = np.zeros((N, N), np.float32)
    for y in range(H_):
        for x in range(W_):
            if T[y][x] in chars:
                m[int(y - X0), int(x - X0)] = 1.0
    return m
def to_fine(m):    # N x N tile mask -> S x S, nearest
    return np.kron(m, np.ones((R, R), np.float32))

landT = class_mask('BGR'); grassT = class_mask('GR'); roadT = class_mask('R'); deepT = None
shalT = class_mask('S')
# the map border is "D"; beyond the map it's deep sea too (zeros are fine for land/grass)

# ------------------------------------------------------------------ coast: warp the tile mask so shapes ignore the grid
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
wx = (fbm(3.2, 3, 11) - 0.5) * 0.9 * R + (fbm(1.1, 2, 12) - 0.5) * 0.35 * R
wy = (fbm(3.2, 3, 21) - 0.5) * 0.9 * R + (fbm(1.1, 2, 22) - 0.5) * 0.35 * R
def warp_blur(m, sigma_tiles):
    f = ndi.gaussian_filter(to_fine(m), sigma_tiles * R)
    return ndi.map_coordinates(f, [yy + wy, xx + wx], order=1, mode='nearest')
Lb = warp_blur(landT, 0.62)
land = Lb > 0.47
# signed distance in tiles (+ land)
din = ndi.distance_transform_edt(land) / R
dout = ndi.distance_transform_edt(~land) / R
d = ndi.gaussian_filter((din - dout).astype(np.float32), 0.12 * R)
d += (fbm(0.9, 2, 31) - 0.5) * 0.06         # slight micro-wobble of the waterline

# grass vs sand weight (ragged organic boundary, with a scrub band)
Gb = warp_blur(grassT, 0.5)
n_ragged = fbm(0.7, 3, 41)
g = sstep(0.0, 1.0, (Gb - 0.42) * 3.2 + (n_ragged - 0.5) * 1.6 + 0.5)
scrub = sstep(0.05, 0.5, g) * (1 - sstep(0.5, 0.95, g))          # band where grass meets sand
Rb = warp_blur(roadT, 0.0) if False else None

# ------------------------------------------------------------------ height (blender z, game tile = 1 unit)
t_beach = sstep(0.0, 1.5, d)
hl = 0.012 + 0.052 * t_beach + 0.030 * sstep(1.2, 5.0, d)
hl += (fbm(2.2, 3, 51) - 0.5) * 0.050 * sstep(0.4, 2.5, d) + (fbm(0.6, 2, 52) - 0.5) * 0.010 * sstep(0.2, 1, d)
hl = hl * sstep(-0.02, 0.10, d)                                     # continuous to 0 at the waterline
ad = np.maximum(-d, 0)
shelf = 0.045 * np.sqrt(ad + 0.0001) * 1.0
depth_sea = 0.55 * sstep(0.0, 2.6, ad) ** 0.85 * 1.0 + 1.9 * sstep(1.4, 6.0, ad) + shelf * 0.6
depth_sea += (fbm(1.6, 3, 61) - 0.5) * 0.35 * sstep(0.5, 3, ad)       # sandbars / shoals
depth_sea = np.maximum(depth_sea, 0)
depth_sea = ndi.gaussian_filter(depth_sea, 0.06 * R)
h = np.where(d > 0, hl, -depth_sea).astype(np.float32)

# flatten building pads so sprites (rendered on z=0) sit properly
FOOT = {"warehouse": (2, 2), "wheat_field": (2, 2), "ship": (2, 2), "chapel": (2, 2)}
objs = lay['objects']
pad = np.zeros((S, S), np.float32)
for o in objs:
    if o['sprite'] in ('house', 'farmhouse', 'windmill', 'lumberjack', 'chapel', 'warehouse'):
        fw, fh = FOOT.get(o['sprite'], (1, 1))
        x0 = int((o['x'] - X0 - 0.15) * R); x1 = int((o['x'] + fw - X0 + 0.15) * R)
        y0 = int((o['y'] - X0 - 0.15) * R); y1 = int((o['y'] + fh - X0 + 0.15) * R)
        pad[y0:y1, x0:x1] = 1
padb = np.clip(ndi.gaussian_filter(pad, 0.18 * R) * 1.8, 0, 1)
h = h * (1 - padb) + 0.034 * padb * (d > 0.3)
h = np.where(d > 0, np.maximum(h, 0.0), h).astype(np.float32)

# ------------------------------------------------------------------ roads: polylines through road-tile centres, soft & worn
from PIL import ImageDraw
road_img = Image.new('F', (S, S), 0.0); rd = ImageDraw.Draw(road_img)
def tc(x, y): return ((x + 0.5 - X0) * R, (y + 0.5 - X0) * R)
rs = {(x, y) for y in range(H_) for x in range(W_) if T[y][x] == 'R'}
for (x, y) in rs:
    for dx, dy in ((1, 0), (0, 1)):
        if (x + dx, y + dy) in rs:
            rd.line([tc(x, y), tc(x + dx, y + dy)], fill=1.0, width=int(0.50 * R))
    a = tc(x, y); r = 0.25 * R
    rd.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=1.0)
# the road at x=15,y=11 runs on into the harbour pier: extend a short ramp
rd.line([tc(15, 11), ((16.0 - X0) * R, (11.5 - X0) * R)], fill=1.0, width=int(0.40 * R))
road0 = np.asarray(road_img)
# wobble edges
road_w = ndi.map_coordinates(road0, [yy + (fbm(1.0, 3, 71) - 0.5) * 0.28 * R, xx + (fbm(1.0, 3, 72) - 0.5) * 0.28 * R], order=1)
road_soft = ndi.gaussian_filter(road_w, 0.07 * R)
road_core = sstep(0.35, 0.72, road_soft)                           # packed dirt
road_worn = sstep(0.04, 0.45, ndi.gaussian_filter(road_w, 0.28 * R))  # wider trampled halo
# only on land
road_core *= (d > 0.15); road_worn *= (d > 0.1)

# ------------------------------------------------------------------ object footprints: ao / dirt / fields
ao = np.zeros((S, S), np.float32); trample = np.zeros((S, S), np.float32); tilled = np.zeros((S, S), np.float32)
leaf = np.zeros((S, S), np.float32)
def rect(x0, y0, x1, y1, a, val=1.0):
    ia, ib = max(0, int((y0 - X0) * R)), min(S, int((y1 - X0) * R)); ja, jb = max(0, int((x0 - X0) * R)), min(S, int((x1 - X0) * R))
    a[ia:ib, ja:jb] = val
for o in objs:
    s = o['sprite']; x, y = o['x'], o['y']; fw, fh = FOOT.get(s, (1, 1))
    if s in ('house', 'farmhouse', 'lumberjack', 'chapel', 'warehouse', 'windmill'):
        i = 0.14 if s != 'windmill' else 0.1
        rect(x + i, y + i, x + fw - i, y + fh - i, ao)
        # trampled apron in front of the building (door side = +y / south in game coords) and a little around
        rect(x + 0.05, y + fh - 0.35, x + fw - 0.05, y + fh + 0.45, trample, 0.9)
        rect(x - 0.1, y - 0.1, x + fw + 0.1, y + fh + 0.1, trample, 0.6)
    elif s == 'wheat_field':
        rect(x + 0.07, y + 0.07, x + fw - 0.07, y + fh - 0.07, tilled)
    elif s == 'tree':
        rect(x + 0.2, y + 0.2, x + 0.8, y + 0.8, leaf)
    elif s == 'rock':
        rect(x + 0.25, y + 0.25, x + 0.75, y + 0.75, ao, 0.6)
    elif s == 'pier':
        rect(x - 0.3, y + 0.1, x + 0.35, y + 0.9, trample, 0.5)
ao = ndi.gaussian_filter(ao, 0.12 * R); trample = ndi.gaussian_filter(trample, 0.16 * R)
tilled = ndi.gaussian_filter(tilled, 0.05 * R); leaf = ndi.gaussian_filter(leaf, 0.18 * R)

# ------------------------------------------------------------------ ground colour (land)
GR_D, GR_M, GR_L, GR_Y = col('#2f4a17'), col('#46691f'), col('#6b8a2a'), col('#8d9a3a')
SAND_D, SAND_L = col('#c4a678'), col('#ecd9a8')
DIRT_D, DIRT_L = col('#5b4128'), col('#8a6a45')
WET = col('#6f5a41')

nlow = fbm(5.0, 3, 81); nmid = fbm(1.6, 4, 82); nhi = grain(0.9, 83); nhi2 = grain(2.2, 84)
grass = mix(GR_D, GR_M, sstep(0.25, 0.7, nmid))
grass = mix(grass, GR_L, sstep(0.45, 0.85, nlow) * 0.8)
grass = mix(grass, GR_Y, sstep(0.62, 0.9, fbm(2.4, 3, 85)) * 0.55)
grass = grass * (1 + 0.16 * nhi[..., None] + 0.12 * nhi2[..., None])
# lighter mown meadow stripes in the big clearings (subtle)
clump = grain(5, 86)
grass *= (1 + 0.05 * clump[..., None])
# flowers
fl = (rng.random((S, S)) > 0.99965).astype(np.float32)
fl = ndi.gaussian_filter(fl, 1.1) * 14
fl = np.clip(fl, 0, 1)
fcol = np.where((fbm(0.5, 2, 87) > 0.5)[..., None], col('#f2e9c8'), col('#e6c34a'))
grass = mix(grass, fcol, fl * sstep(0.5, 0.9, g) * 0.85)

sand = mix(SAND_D, SAND_L, sstep(0.25, 0.75, fbm(2.0, 3, 91)))
sand = sand * (1 + 0.05 * nhi[..., None])
# fine wind ripples on dry sand
rip = np.sin((xx * 0.55 + yy * 0.35) / R * 2 * np.pi * 7 + fbm(1.2, 3, 92) * 9)
sand = sand * (1 + 0.020 * rip[..., None])
# dry scrub: dried grass tint + dark tufts
dry = col('#9c8d4c')
tufts = sstep(0.62, 0.8, fbm(0.35, 2, 93)) * scrub
base_land = mix(sand, grass, g)
base_land = mix(base_land, dry * (1 + 0.15 * nhi[..., None]), scrub * 0.65)
base_land = mix(base_land, GR_D * 0.9, tufts * 0.7)
# wet sand at the waterline + darkened
wetm = (1 - sstep(0.0, 0.42, d)) * (d > -0.001) * (1 - 0.3 * fbm(0.5, 2, 94))
wetm = np.clip(wetm, 0, 1)
base_land = mix(base_land, WET * (1 + 0.06 * nhi[..., None]), wetm * 0.9)
# dry crest line above the wet: slightly paler band, as seen after receding waves
crest = np.exp(-((d - 0.55) / 0.12) ** 2) * (g < 0.4)
base_land = base_land * (1 + 0.06 * crest[..., None])
# leaf litter & ao & trample & tilled
base_land = mix(base_land, base_land * np.array([0.62, 0.66, 0.5], np.float32), leaf * 0.7)
dirt = mix(DIRT_D, DIRT_L, sstep(0.3, 0.75, fbm(0.7, 3, 95)))
dirt = dirt * (1 + 0.10 * nhi[..., None] + 0.08 * nhi2[..., None])
# ruts
rutd = np.abs(np.sin((xx + yy * 0.0) / R * 2 * np.pi * 0.0))  # placeholder (ruts follow road orientation below)
# trampled apron: dirt patches, ragged
tr_m = sstep(0.18, 0.7, trample + (fbm(0.5, 3, 96) - 0.5) * 0.55)
base_land = mix(base_land, mix(base_land, dirt, 0.85), tr_m * (d > 0.4))
worn = road_worn * (0.55 + 0.25 * fbm(0.6, 3, 97))
base_land = mix(base_land, mix(base_land, dirt * 1.05, 0.6), np.clip(worn - road_core, 0, 1) * sstep(0.3, 0.9, fbm(0.45, 3, 98)) * 0.9)
road_col = dirt * (1 + 0.07 * grain(0.6, 99)[..., None])
# a darker rut pair is implied by noise stripes; pebbles
peb = (rng.random((S, S)) > 0.9985).astype(np.float32); peb = np.clip(ndi.gaussian_filter(peb, 1.0) * 12, 0, 1)
road_col = mix(road_col, col('#b7a98c'), peb * 0.7)
road_col = road_col * (1 - 0.10 * sstep(0.5, 1.0, fbm(0.4, 3, 100))[..., None])
base_land = mix(base_land, road_col, road_core * 0.95)
# tilled earth under wheat fields
soil = mix(col('#4a3322'), col('#6a4a2e'), sstep(0.3, 0.7, fbm(0.4, 3, 101))) * (1 + 0.1 * nhi[..., None])
base_land = mix(base_land, soil, sstep(0.3, 0.8, tilled))
# grass tufts creeping over the road edge
edge = sstep(0.2, 0.8, road_soft) * (1 - road_core)
base_land = mix(base_land, grass * 0.95, edge * sstep(0.55, 0.75, fbm(0.25, 3, 102)) * 0.7)
# ambient occlusion contact darkening around buildings
base_land = base_land * (1 - 0.42 * np.clip(ao, 0, 1))[..., None]

# ------------------------------------------------------------------ seabed (seen through the water) incl. caustics
dep = depth_sea
sea_sand = mix(col('#d8c493'), col('#b8a272'), sstep(0.0, 1.8, dep))
sea_sand = sea_sand * (1 + 0.06 * nhi[..., None] + 0.05 * fbm(0.8, 3, 111)[..., None] - 0.025)
grass_sea = sstep(0.62, 0.78, fbm(1.0, 3, 112)) * sstep(0.12, 0.45, dep) * (1 - sstep(0.9, 1.6, dep))
sea_sand = mix(sea_sand, col('#2c5a34') * (1 + 0.2 * nhi[..., None]), grass_sea * 0.75)
rockp = sstep(0.7, 0.82, fbm(0.7, 3, 113)) * sstep(0.3, 0.6, dep) * (1 - sstep(1.2, 2.0, dep))
sea_sand = mix(sea_sand, col('#4d5546') * (1 + 0.2 * nhi[..., None]), rockp * 0.8)
sea_sand = sea_sand * (1 - 0.55 * sstep(1.2, 3.0, dep))[..., None]
# caustics: web of bright lines from layered |noise| ridges
def ridge(scale, seed):
    n = fbm(scale, 3, seed); return 1 - np.abs(n - 0.5) * 2
c1 = ridge(0.42, 121) ** 6; c2 = ridge(0.31, 122) ** 6
caus = np.clip(c1 + c2, 0, 1.4) * sstep(0.03, 0.18, dep) * (1 - sstep(0.7, 1.7, dep))
sea_sand = sea_sand * (1 + 0.85 * caus[..., None])

color = np.where((d > 0)[..., None], base_land, sea_sand)
# soft blend across the waterline (wet sand into seabed)
blend = sstep(-0.03, 0.03, d)
color = mix(sea_sand, base_land, blend)

# ------------------------------------------------------------------ foam / wet masks
sh = np.maximum(-d, 0)           # offshore distance (tiles)
sw = fbm(0.55, 3, 131)
# swash: bright thin line right at the waterline, a broken second wave line further out, streaky
swash = np.exp(-((sh - 0.035 - 0.03 * sw) / 0.055) ** 2) * (d <= 0.02)
line2 = np.exp(-((sh - 0.33 - 0.12 * np.sin(fbm(1.5, 2, 132) * 12)) / 0.07) ** 2) * sstep(0.45, 0.75, fbm(0.28, 3, 133))
line3 = np.exp(-((sh - 0.75 - 0.18 * np.sin(fbm(1.9, 2, 134) * 11)) / 0.06) ** 2) * sstep(0.55, 0.8, fbm(0.3, 3, 135)) * 0.6
lace = sstep(0.35, 0.65, fbm(0.18, 3, 136))
foam = np.clip(swash * (0.55 + 0.6 * lace) + line2 * 0.75 * lace + line3 * lace, 0, 1)
foam *= sstep(-0.01, 0.02, -d + 0.04)

def save16(a, name, scale=1.0):
    Image.fromarray((np.clip(a / scale, 0, 1) * 65535).astype(np.uint16)).save(os.path.join(FD, name))
Image.fromarray((np.clip(color, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(FD, 'color.png'))
save16(depth_sea * (d <= 0), 'depth.png', DMAX)
save16(foam, 'foam.png'); save16(wetm, 'wet.png')
# heightfield raw: subsample 16 verts per tile
V = 16
hs = h[::R // V, ::R // V].astype(np.float32)
hs.tofile(os.path.join(FD, 'height.f32'))
json.dump(dict(X0=X0, N=N, R=R, V=V, nv=int(hs.shape[0]), DMAX=DMAX), open(os.path.join(FD, 'info.json'), 'w'))
# debugging preview
prev = Image.fromarray((np.clip(color, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
prev.save(os.path.join(FD, 'preview.png'))
print('fields done', S, 'land frac', land.mean())
