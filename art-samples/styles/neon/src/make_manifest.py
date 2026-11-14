"""Write manifest.json from sprites_meta.json (anchors) + terrain files."""
import json, os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
meta = json.load(open(os.path.join(HERE, 'sprites_meta.json')))
def files(prefix):
    names = [os.path.basename(f)[:-4] for f in glob.glob(os.path.join(OUT, prefix + '_*.png'))]
    names = [n for n in names if n[len(prefix) + 1:].isdigit()]
    return sorted(names, key=lambda n: int(n.split('_')[-1]))
spr = {}
def add(key, names, flat=False, anchor=None):
    if not names: return
    spr[key] = dict(files=[n + '.png' for n in names], anchor=anchor or list(meta[names[0]]['anchor']) if names[0] in meta else anchor)
    if flat: spr[key]['flat'] = True
T_ANCHOR = [66, 66]
for key, pre in (('deep_water', 'deep'), ('shallow_water', 'shallow'), ('sand', 'sand'), ('grass', 'grass'), ('road', 'road')):
    add(key, files(pre), anchor=T_ANCHOR)
for key, pre in (('tree', 'tree'), ('rock', 'rock'), ('house', 'house'), ('colonist', 'colonist')): add(key, files(pre))
for key in ('farmhouse', 'windmill', 'lumberjack', 'chapel', 'warehouse', 'ship', 'cart'): add(key, [key])
add('wheat_field', ['wheat_field'], True); add('pier', ['pier'], True)
# anchors must be identical across variants of one key (post.py groups them); verify
for key, s in spr.items():
    if key in ('deep_water', 'shallow_water', 'sand', 'grass', 'road'): continue
    an = {tuple(meta[f[:-4]]['anchor']) for f in s['files']}
    assert len(an) == 1, (key, an)
overlays = []
if os.path.exists(os.path.join(OUT, 'ui_overlay.png')): overlays.append(dict(file='ui_overlay.png', pos=[0, 0], anchor=[0, 0]))
if os.path.exists(os.path.join(OUT, 'ui_topbar.png')):
    overlays += [dict(file='ui_topbar.png', pos=[0, 0], anchor=[0, 0]), dict(file='ui_panel.png', pos=[24, 1056], anchor=[0, 300])]
man = dict(name='Neon Foundry', background='#04060b', filter='linear', sprites=spr, overlays=overlays)
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
print('manifest written:', {k: len(v['files']) for k, v in spr.items()})
