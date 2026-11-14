"""Painted Isometric - generates every PNG + manifest.json into ..  Run: python3 build.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import terrain, objs, objs2, ui

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sprites = {}
def save(name, im): im.save(os.path.join(OUT, name))
def add(key, files, anchor, flat=False):
    d = {"files": files, "anchor": list(anchor)}
    if flat: d["flat"] = True
    sprites[key] = d

for kind, key, nv in [('deep', 'deep_water', 2), ('shallow', 'shallow_water', 3), ('sand', 'sand', 3), ('grass', 'grass', 5), ('road', 'road', 2)]:
    fs = []
    for v in range(nv):
        fn = f'{key}_{v}.png'; save(fn, terrain.make(kind, v)); fs.append(fn)
    add(key, fs, terrain.ANCH)

def many(key, fn, n, flat=False, **kw):
    fs = []; anc = None
    for v in range(n):
        im, anc = fn(v)
        name = f'{key}_{v}.png' if n > 1 else f'{key}.png'
        save(name, im); fs.append(name)
    add(key, fs, anc, flat)

many('tree', lambda v: objs.tree(v, 5), 4)
many('rock', lambda v: objs.rock(v, 3), 2)
many('house', lambda v: objs.house(v), 3)
many('farmhouse', lambda v: objs.farmhouse(), 1)
many('windmill', lambda v: objs.windmill(), 1)
many('lumberjack', lambda v: objs.lumberjack(), 1)
many('chapel', lambda v: objs.chapel(), 1)
many('warehouse', lambda v: objs.warehouse(), 1)
many('wheat_field', lambda v: objs2.wheat(), 1, flat=True)
many('pier', lambda v: objs2.pier(), 1, flat=True)
many('ship', lambda v: objs2.ship(), 1)
many('cart', lambda v: objs2.cart(), 1)
many('colonist', lambda v: objs2.colonist(v), 4)

save('ui_topbar.png', ui.topbar())
save('ui_panel.png', ui.panel())
manifest = {"name": "Painted Isometric", "background": "#1f5f7a", "filter": "linear", "sprites": sprites,
            "overlays": [{"file": "ui_topbar.png", "pos": [0, 0], "anchor": [0, 0]},
                         {"file": "ui_panel.png", "pos": [24, 1056], "anchor": [0, 300]}]}
json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=2)
print('built')
