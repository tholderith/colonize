"""Generate every PNG + manifest.json for the Pixel style:  python3 build.py"""
import os, json, sys
sys.path.insert(0, os.path.dirname(__file__))
import terrain as T, objs as O, ui
from palette import all_colours

OUT = os.path.join(os.path.dirname(__file__), '..')
sprites = {}
def save(name, im): im.save(os.path.join(OUT, name))
def add(key, files_ims, anchor, flat=False):
    files = []
    for i, im in enumerate(files_ims):
        fn = f'{key}_{i}.png'; save(fn, im); files.append(fn)
    sprites[key] = {'files': files, 'anchor': anchor}
    if flat: sprites[key]['flat'] = True
def A(im, dx=0, dy=0): return [im.width // 2 + dx, im.height + dy]

add('deep_water', [T.water('deep', i) for i in range(3)], [64, 64])
add('shallow_water', [T.water('shallow', i) for i in range(3)], [64, 64])
add('sand', [T.sand(i) for i in range(3)], [64, 64])
add('grass', [T.grass(i) for i in range(4)], [64, 64])
add('road', [T.road(i) for i in range(2)], [64, 64])
for key, ims in [('tree', [O.tree(i) for i in range(3)]), ('rock', [O.rock()]), ('house', [O.house(i) for i in range(4)]),
                 ('farmhouse', [O.farmhouse()]), ('windmill', [O.windmill()]), ('lumberjack', [O.lumberjack()]),
                 ('chapel', [O.chapel()]), ('warehouse', [O.warehouse()]), ('ship', [O.ship()]), ('cart', [O.cart()]),
                 ('colonist', [O.colonist(i) for i in range(4)])]:
    add(key, ims, A(ims[0]))
add('wheat_field', [O.wheat()], A(O.wheat()), flat=True)
add('pier', [O.pier()], A(O.pier()), flat=True)
save('ui_topbar.png', ui.topbar()); save('ui_panel.png', ui.panel())
man = {'name': 'Pixel Art', 'background': '#173659', 'filter': 'nearest', 'sprites': sprites,
       'overlays': [{'file': 'ui_topbar.png', 'pos': [0, 0], 'anchor': [0, 0]},
                    {'file': 'ui_panel.png', 'pos': [24, 1056], 'anchor': [0, 300]}]}
json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
print('ok', len(sprites))
