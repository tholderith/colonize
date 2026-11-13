"""The 'Pixel' style palette: 47 hand-picked colours in hue-shifted ramps.

Shadows lean cool/purple, highlights lean warm/yellow. Every opaque pixel in every
sprite comes from this table (the only exception is the single translucent
ground-shadow colour SHADOW_RGBA)."""

def _h(s):
    s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

RAMPS = {
    # name: dark -> light
    'ink':   ['#1c1626', '#2d2436', '#453848'],
    'grass': ['#1e3a34', '#2a5638', '#3d7a3c', '#5c9c40', '#8cc04e', '#c6e07a'],
    'water': ['#10213d', '#173659', '#1d4f78', '#276e93', '#3c94ad', '#67c1c4', '#b7ece0'],
    'sand':  ['#7a5a46', '#a8835a', '#cfac74', '#e8cf96', '#fbefc4'],
    'wood':  ['#3a2424', '#5a3626', '#7e4f30', '#a6703c', '#cc9a58'],
    'stone': ['#3e3d52', '#5f6175', '#8a8d9c', '#b8b8bf', '#e2ddd3'],
    'roof':  ['#4f1f2c', '#7f2f36', '#ad4a3c', '#d4704a', '#eea066'],
    'slate': ['#26304f', '#3a4f78', '#5674a0', '#7ea0c4'],
    'gold':  ['#7a5a1c', '#b88a2c', '#e0b84a', '#f6e08a'],
    'skin':  ['#b06f55', '#e7b088'],
    'white': ['#fffbea'],
}
RAMPS = {k: [_h(c) for c in v] for k, v in RAMPS.items()}

def all_colours():
    out = []
    for v in RAMPS.values():
        for c in v:
            if c not in out: out.append(c)
    return out

def C(name, i):
    r = RAMPS[name]; return r[max(0, min(len(r) - 1, i))]

INK = C('ink', 0)
SHADOW_RGBA = (28, 22, 38, 92)   # translucent ground shadow (ink-0 at ~36%)

# Material ramps used by the object renderer: a list of colours dark->light.
def ramp(*spec):
    """ramp(('stone',1),('stone',2),...) -> list of RGB"""
    return [C(n, i) for n, i in spec]

MAT = {
    'plaster': ramp(('stone', 1), ('stone', 2), ('stone', 3), ('stone', 4), ('white', 0)),
    'ochre':   ramp(('wood', 2), ('sand', 1), ('sand', 2), ('sand', 3), ('sand', 4)),
    'timber':  ramp(('wood', 0), ('wood', 1), ('wood', 2), ('wood', 3), ('wood', 4)),
    'plank':   ramp(('wood', 0), ('wood', 1), ('wood', 2), ('wood', 3), ('wood', 4)),
    'roof':    ramp(('roof', 0), ('roof', 1), ('roof', 2), ('roof', 3), ('roof', 4)),
    'slate':   ramp(('ink', 1), ('slate', 0), ('slate', 1), ('slate', 2), ('slate', 3)),
    'thatch':  ramp(('wood', 1), ('gold', 0), ('gold', 1), ('gold', 2), ('gold', 3)),
    'stone':   ramp(('ink', 1), ('stone', 0), ('stone', 1), ('stone', 2), ('stone', 3)),
    'rock':    ramp(('ink', 1), ('stone', 0), ('stone', 1), ('stone', 2), ('stone', 3), ('stone', 4)),
    'leaf':    ramp(('grass', 0), ('grass', 1), ('grass', 2), ('grass', 3), ('grass', 4), ('grass', 5)),
    'pine':    ramp(('ink', 1), ('grass', 0), ('grass', 1), ('grass', 2), ('grass', 3)),
    'bark':    ramp(('wood', 0), ('wood', 1), ('wood', 2), ('wood', 3)),
    'glass':   ramp(('ink', 0), ('water', 1), ('water', 2), ('water', 3)),
    'sail':    ramp(('stone', 2), ('sand', 2), ('sand', 3), ('sand', 4), ('white', 0)),
    'hull':    ramp(('wood', 0), ('wood', 1), ('wood', 2), ('wood', 3), ('wood', 4)),
    'paint_red':  ramp(('roof', 0), ('roof', 1), ('roof', 2), ('roof', 3)),
    'paint_blue': ramp(('slate', 0), ('slate', 1), ('slate', 2), ('slate', 3)),
    'gold':    ramp(('gold', 0), ('gold', 1), ('gold', 2), ('gold', 3)),
    'wheat':   ramp(('wood', 2), ('gold', 0), ('gold', 1), ('gold', 2), ('gold', 3)),
    'moss':    ramp(('grass', 0), ('grass', 1), ('grass', 2), ('grass', 3)),
    'skin':    ramp(('skin', 0), ('skin', 0), ('skin', 1), ('skin', 1)),
    'ox':      ramp(('wood', 0), ('wood', 1), ('wood', 2), ('wood', 3), ('wood', 4)),
    'dark':    ramp(('ink', 0), ('ink', 1), ('ink', 2)),
}
