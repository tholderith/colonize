"""blender -b --python render.py -- [sprite names]   (renders raw object + shadow passes into $R98WORK/raw)"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import *
SPP = int(os.environ.get("R98SPP", "40"))
LAND = '#2a5a2c'; WATER = '#12306a'
JOBS = {}
def job(name, fn, **kw): JOBS[name] = (fn, kw)
for k in range(4): job(f'house_{k}', build_house(k), W=320, H=380, K=1.18, shadow_col=LAND)
for k in range(4): job(f'tree_{k}', build_tree(k), W=320, H=380, shadow_col=LAND)
for k in range(2): job(f'rock_{k}', build_rock(k), W=320, H=300, shadow_col=LAND)
for k in range(4): job(f'colonist_{k}', build_colonist(k), W=240, H=240, K=1.3, shadow_col=LAND)
job('farmhouse', build_farmhouse, W=340, H=340, shadow_col=LAND)
job('windmill', build_windmill, W=340, H=420, shadow_col=LAND)
job('lumberjack', build_lumber, W=340, H=320, shadow_col=LAND)
job('cart', build_cart, W=360, H=260, K=1.3, shadow_col=LAND)
job('chapel', build_chapel, fw=2, fh=2, W=560, H=640, off=230, shadow_col=LAND)
job('warehouse', build_warehouse, fw=2, fh=2, W=560, H=600, off=220, shadow_col=LAND)
job('wheat_field', build_wheat, fw=2, fh=2, W=560, H=400, off=100, shadow=False, flat=True)
job('pier', build_pier, W=320, H=240, shadow_col=WATER, flat=True)
job('ship', build_ship, fw=2, fh=2, W=620, H=680, off=250, shadow_col=WATER)
if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for n, (fn, kw) in JOBS.items():
        if a and not any(n.startswith(p) for p in a): continue
        kw = dict(kw); kw.setdefault('samples', SPP)
        render_sprite(n, fn, **kw)
