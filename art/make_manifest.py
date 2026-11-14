"""Write public/assets/manifest.json: {tiles:{key:{file,anchor}}, buildings:{key:{file,glow,anchor}}}; paths relative to public/assets/."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "public", "assets")
tiles = {}
for k in ('deep_water', 'shallow_water', 'land', 'road'): tiles[k] = dict(file='tiles/%s.png' % k, anchor=[66, 66])
for k in ['%s_water_%d' % (w, i) for w in ('deep', 'shallow') for i in range(3)] + ['land_0', 'land_1', 'land_2']: tiles[k] = dict(file='tiles/%s.png' % k, anchor=[66, 66])
for m in range(16): tiles['road_%d' % m] = dict(file='tiles/road_%d.png' % m, anchor=[66, 66])
for m in range(16): tiles['shore_%d' % m] = dict(file='tiles/shore_%d.png' % m, anchor=[66, 66])
meta = json.load(open(os.path.join(HERE, 'out', 'buildings_meta.json')))
KEYS = ['pod_house', 'hydroponics', 'scrap_yard', 'smelter', 'wind_turbine', 'depot',
        'ration_plant', 'algae_skimmer', 'refinery', 'fabricator', 'pod_house_t2', 'port']
b = {k: dict(file=meta[k]['file'], glow=meta[k]['glow'], anchor=meta[k]['anchor']) for k in KEYS}
UK = ['%s_%s' % (s, d) for s in ('hauler', 'trader', 'patrol') for d in ('ne', 'se', 'sw', 'nw')]
u = {k: dict(file=meta[k]['file'], glow=meta[k]['glow'], anchor=meta[k]['anchor']) for k in UK if k in meta}
ICONS = ['credits', 'biomass', 'rations', 'scrap', 'alloy', 'algae', 'polymer', 'goods', 'laborers', 'technicians', 'power']
icons = {k: dict(file='ui/icons/%s.png' % k, file2x='ui/icons/%s@2x.png' % k) for k in ICONS}
fr = ['wind_turbine_f%d' % i for i in range(8)]   # same crop box + anchor as the static wind_turbine -> frames swap in place
anims = dict(wind_turbine=dict(frames=[meta[k]['file'] for k in fr], glowFrames=[meta[k]['glow'] for k in fr], anchor=meta['wind_turbine']['anchor'], fps=8))
json.dump(dict(tiles=tiles, buildings=b, units=u, icons=icons, anims=anims), open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
print('manifest written:', len(tiles), 'tiles,', len(b), 'buildings,', len(u), 'units')
