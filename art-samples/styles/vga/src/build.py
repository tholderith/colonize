import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
out = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import terrain, objs
terrain.build(out)
A = objs.build(out)
try:
    import ui; ui.build(out, A)
except ImportError: ui = None
def sp(key, n, anchor, **kw):
    d = {"files": [f"{key}_{i}.png" for i in range(n)], "anchor": anchor}; d.update(kw); return d
S = {}
for k, n in [('deep_water',3),('shallow_water',3),('sand',3),('grass',4),('road',2)]: S[k] = sp(k, n, [64, 64])
for k, n in [('tree',3),('rock',1),('house',3),('farmhouse',1),('windmill',1),('lumberjack',1),('chapel',1),('warehouse',1),('ship',1),('cart',1),('colonist',4),('wheat_field',1),('pier',1)]:
    S[k] = sp(k, n, A[f'{k}_0'])
    if k in ('wheat_field','pier'): S[k]['flat'] = True
ov = []
if ui:
    ov = [{"file": "ui_topbar.png", "pos": [0, 0], "anchor": [0, 0]}, {"file": "ui_panel.png", "pos": [24, 1056], "anchor": [0, 300]}]
json.dump({"name": "VGA Classic", "background": "#081a40", "filter": "nearest", "sprites": S, "overlays": ov}, open(out + '/manifest.json', 'w'), indent=1)
