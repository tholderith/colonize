"""Write manifest.json from sprites_meta.json (anchors measured by post.py)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
meta = json.load(open(os.path.join(HERE, 'sprites_meta.json')))
def files(prefix):
    ks = sorted([k for k in meta if k.startswith(prefix + '_') and k[len(prefix) + 1:].isdigit()], key=lambda k: int(k.split('_')[-1]))
    return ks
spr = {}
def add(key, names, flat=False):
    if not names: return
    anchors = {tuple(meta[n]['anchor']) for n in names}
    # a single anchor per sprite key is required by the spec -> pad all variants to the same anchor if they differ
    spr[key] = dict(files=[n + '.png' for n in names], anchor=list(meta[names[0]]['anchor']))
    if flat: spr[key]['flat'] = True
    spr[key]['_anchors'] = sorted(list(a) for a in anchors)
for key, pre in (('deep_water', 'deep'), ('shallow_water', 'shallow'), ('sand', 'sand'), ('grass', 'grass'), ('road', 'road'),
                 ('tree', 'tree'), ('rock', 'rock'), ('house', 'house'), ('colonist', 'colonist')):
    add(key, files(pre))
for key in ('farmhouse', 'windmill', 'lumberjack', 'chapel', 'warehouse', 'ship', 'cart'): add(key, [key])
add('wheat_field', ['wheat_field'], True); add('pier', ['pier'], True)
bad = {k: v['_anchors'] for k, v in spr.items() if len(v['_anchors']) > 1}
for v in spr.values(): v.pop('_anchors')
man = dict(name='Realistic (Blender/Cycles PBR)', background='#0a2a33', filter='linear', sprites=spr,
           overlays=[dict(file='ui_vignette.png', pos=[0, 0], anchor=[0, 0]), dict(file='ui_topbar.png', pos=[0, 0], anchor=[0, 0]), dict(file='ui_panel.png', pos=[24, 1056], anchor=[0, 300])])
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
print('manifest written;', 'ANCHOR MISMATCH within keys: %s' % bad if bad else 'anchors consistent per key')
