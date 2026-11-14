"""Write public/assets/manifest.json: {tiles:{key:{file,anchor}}, buildings:{key:{file,glow,anchor}}}; paths relative to public/assets/."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "public", "assets")
tiles = {}
for k in ('deep_water', 'shallow_water', 'land', 'road'): tiles[k] = dict(file='tiles/%s.png' % k, anchor=[66, 66])
for k in ('land_0', 'land_1', 'land_2'): tiles[k] = dict(file='tiles/%s.png' % k, anchor=[66, 66])
for m in range(16): tiles['road_%d' % m] = dict(file='tiles/road_%d.png' % m, anchor=[66, 66])
for m in range(16): tiles['shore_%d' % m] = dict(file='tiles/shore_%d.png' % m, anchor=[66, 66])
meta = json.load(open(os.path.join(HERE, 'out', 'buildings_meta.json')))
KEYS = ['pod_house', 'hydroponics', 'scrap_yard', 'smelter', 'wind_turbine', 'depot',
        'ration_plant', 'algae_skimmer', 'refinery', 'fabricator', 'pod_house_t2']
b = {k: dict(file=meta[k]['file'], glow=meta[k]['glow'], anchor=meta[k]['anchor']) for k in KEYS}
json.dump(dict(tiles=tiles, buildings=b), open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
print('manifest written:', len(tiles), 'tiles,', len(b), 'buildings')
