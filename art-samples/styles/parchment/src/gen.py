import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import terrain, sprites, ui, overlays
terrain.build(OUT); sprites.build(OUT)
ui.topbar(f"{OUT}/ui_topbar.png"); ui.panel(f"{OUT}/ui_panel.png")
overlays.chart_ink(os.path.join(OUT, "../../scene/layout.json"), f"{OUT}/chart_ink.png")
overlays.paper(f"{OUT}/paper.png")
def v(k, n): return [f"{k}_{i}.png" for i in range(n)]
sp = {
 "deep_water": (v("deep", 2), [64, 64]), "shallow_water": (v("shallow", 2), [64, 64]), "sand": (v("sand", 2), [64, 64]),
 "grass": (v("grass", 4), [64, 64]), "road": (v("road", 2), [64, 64]),
 "tree": (v("tree", 3), [40, 100]), "rock": (["rock.png"], [32, 52]), "house": (v("house", 3), [64, 100]),
 "farmhouse": (["farmhouse.png"], [64, 108]), "windmill": (["windmill.png"], [80, 150]), "lumberjack": (["lumberjack.png"], [64, 90]),
 "chapel": (["chapel.png"], [128, 215]), "warehouse": (["warehouse.png"], [128, 178]), "wheat_field": (["wheat.png"], [128, 128]),
 "pier": (["pier.png"], [64, 64]), "ship": (["ship.png"], [128, 200]), "cart": (["cart.png"], [48, 64]), "colonist": (["colonist.png"], [16, 40]),
}
flat = {"wheat_field", "pier"}
man = {"name": "Parchment Chart", "background": "#8fb0a0", "filter": "linear",
 "sprites": {k: dict(files=f, anchor=a, **({"flat": True} if k in flat else {})) for k, (f, a) in sp.items()},
 "overlays": [
  {"file": "chart_ink.png", "pos": [0, 0], "anchor": [0, 0]},
  {"file": "paper.png", "pos": [0, 0], "anchor": [0, 0]},
  {"file": "ui_topbar.png", "pos": [0, 0], "anchor": [0, 0]},
  {"file": "ui_panel.png", "pos": [24, 1056], "anchor": [0, 300]}]}
json.dump(man, open(f"{OUT}/manifest.json", "w"), indent=1)
