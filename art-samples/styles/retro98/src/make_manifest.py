import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
meta = json.load(open(f"{HERE}/sprites_meta.json"))
T = {'deep_water': ('deep', 4), 'shallow_water': ('shallow', 4), 'sand': ('sand', 3), 'grass': ('grass', 4), 'road': ('road', 2)}
spr = {k: dict(files=[f'{p}_{i}.png' for i in range(n)], anchor=[64, 64]) for k, (p, n) in T.items()}
for k in ('tree', 'rock', 'house', 'farmhouse', 'windmill', 'lumberjack', 'chapel', 'warehouse', 'wheat_field', 'pier', 'ship', 'cart', 'colonist'):
    m = meta[k]; spr[k] = dict(files=m['files'], anchor=m['anchor'])
    if m.get('flat'): spr[k]['flat'] = True
man = dict(name='Pre-rendered 98 (Blender/Cycles -> 256 colours)', background='#103a8a', filter='nearest', sprites=spr,
           overlays=[dict(file='ui_topbar.png', pos=[0, 0], anchor=[0, 0]), dict(file='ui_panel.png', pos=[24, 1056], anchor=[0, 300])])
json.dump(man, open(f"{OUT}/manifest.json", 'w'), indent=1); print('manifest written')
