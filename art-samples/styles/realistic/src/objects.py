import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import models_a as A
try: import models_b as Bm
except ImportError: Bm = None

def mk(fn, *a):
    def build(ctr):
        objs = fn(ctr, *a); return objs
    return build

SPP = int(os.environ.get("OSPP", "128"))
JOBS = {}
for v in range(4): JOBS[f'house_{v}'] = (A.house, (v,), 1, 1, dict(K=1.18))
JOBS['farmhouse'] = (A.farmhouse, (), 1, 1, dict(K=1.1))
JOBS['lumberjack'] = (A.lumberjack, (), 1, 1, dict(K=1.25))
JOBS['chapel'] = (A.chapel, (), 2, 2, {})
JOBS['warehouse'] = (A.warehouse, (), 2, 2, {})
JOBS['windmill'] = (A.windmill, (), 1, 1, dict(K=1.15, W=700, H=860))
if Bm: JOBS.update(Bm.JOBS)

if __name__ == '__main__':
    a = args(); names = a[0].split(',') if a else list(JOBS)
    for n in names:
        if '*' in n: ms = [k for k in JOBS if k.startswith(n.rstrip('*'))]
        else: ms = [n]
        for m in ms:
            fn, fa, fw, fh, kw = JOBS[m]
            sprite(m, mk(fn, *fa), fw, fh, samples=kw.get('spp', SPP), flat=kw.get('flat', False), catcher=kw.get('catcher', True),
                   cat_size=kw.get('cat_size'), W=kw.get('W'), H=kw.get('H'), K=kw.get('K', 1.0))
