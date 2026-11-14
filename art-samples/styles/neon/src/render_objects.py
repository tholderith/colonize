import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
import models as MD
if __name__ == '__main__':
    a = args(); names = a[0].split(',') if a else list(MD.JOBS)
    spp = int(os.environ.get("NSPP", "0"))
    for n in names:
        ms = [k for k in MD.JOBS if k.startswith(n.rstrip('*'))]
        for m in ms:
            fn, fa, fw, fh, kw = MD.JOBS[m]
            kw = dict(kw); 
            if spp: kw['samples'] = spp
            kw.setdefault('samples', 64)
            try: lib.sprite(m, lambda fn=fn, fa=fa: fn(*fa), fw, fh, seed=sum(map(ord, m)) % 1000, **kw)
            except Exception as e:
                import traceback; traceback.print_exc(); print('FAILED', m, flush=True)
