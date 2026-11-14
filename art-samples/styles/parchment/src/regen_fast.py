# regenerate only overlays + ui (fast iteration)
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import ui, overlays
ui.topbar(f"{OUT}/ui_topbar.png"); ui.panel(f"{OUT}/ui_panel.png")
overlays.chart_ink(os.path.join(OUT, "../../scene/layout.json"), f"{OUT}/chart_ink.png"); overlays.paper(f"{OUT}/paper.png")
