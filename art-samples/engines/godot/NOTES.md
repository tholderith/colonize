# Godot 4 — art sample notes

**Version:** Godot 4.7.2-stable (official linux x86_64), GDScript, Compatibility (OpenGL 3) renderer on Mesa llvmpipe under Xvfb.
**Download:** zip 78 MB, binary 146 MB, kept at `/home/user/tools/godot/` (render.sh downloads it if missing).

## Run
`engines/godot/render.sh styles/<style> renders/godot/<style>.png` (any cwd; uses `$GODOT` / `$GODOT_DIR`; wraps in `xvfb-run` unless `$DISPLAY` is set).
Direct: `godot --path engines/godot --rendering-driver opengl3 -- --style <abs dir> --out <png>`.

## Result
placeholder vs `render_ref.py`: mean abs per-channel diff **0.007** (max 1/255) — pass (< 2).

## Metrics
- First run (no `.godot/` cache, no import step needed since textures load at runtime): ~1.3 s total. Warm: ~1.3 s. Render itself is a few frames.
- LOC: main.gd 137, render.sh ~40, project.godot 21, main.tscn 6 (~200 total).
- No editor import: `Image.load_from_file` + `ImageTexture.create_from_image`; filter set per manifest via `texture_filter` on the root Node2D (children inherit) and on overlay TextureRects.
- Draw order = scene-tree order (add_child order); no z_index needed.

## Pain points
- Xvfb/GL: works with `--rendering-driver opengl3`. Vulkan (Forward+) is not needed. Harmless warning about vsync (`set_use_vsync`) under Xvfb. `--headless` cannot capture frames (dummy renderer), as expected.
- Import system: avoided entirely; a project with `res://` assets needs `godot --headless --import` once in CI, otherwise textures fail to load.
- .tscn/.project.godot as text: simple and diffable; the trivial scene here is 6 lines. I built the scene in code, which is the more robust path for agents; hand-written .tscn for complex UIs is fiddly (ext_resource ids, load_steps, subresource ordering) but tolerable.
- Pixel snapping (`snap_2d_transforms_to_pixel`) and `stretch/mode=disabled` are needed for 1:1 match.

## Assessment for the full game with an AI agent team
Godot is a strong fit for text-and-CLI development. Projects are plain text (`project.godot`, `.tscn`, `.tres`, `.gd`), the binary is a single 146 MB file with no install, and `--headless` runs scripts, imports, and tests; GUT or gdUnit4 can run in CI via CLI. GDScript is compact and agents write it well, though the typed-but-Python-like syntax has fewer training examples than JS/Python and errors only surface at load/run time, so agents need a lint/`--check-only` + run loop. Control-node UI (containers, themes, anchors) is a good match for a UI-heavy game and can be built wholly in code or `.tscn`; Theme resources in text are readable. Saves are easy (JSON, `ConfigFile`, or `var_to_bytes`/Resource serialisation). Export templates (~1 GB extra download) and presets are CLI-driven (`--export-release`). Weak spots: the simulation of thousands of entities should be data-oriented (arrays/PackedArrays, a MultiMesh/`RenderingServer` canvas-item draw or TileMap layers rather than thousands of Node2D); GDScript is ~10-50x slower than C#/C++ so heavy sim may need GDExtension or C#, which complicates the Linux-container workflow. Screenshots/visual verification work as shown, but only via Xvfb + software GL (slow for animation, fine for stills).

A human in the editor would gain: visual UI/Theme layout, 2D scene/TileMap editing, live inspector and remote scene tree debugging, profiler, animation/particle tooling, and one-click export/preview — things an agent can only approximate through text. Net: low friction for agents, the engine's best trait being that everything is text and the CLI is complete; the main risk is runtime-only errors and GDScript perf ceilings.
- Underlays (SPEC step 2b): manifest `underlays` images are drawn in manifest order after all terrain and before any object, world-space (pan/zoom with the map in the browser viewer).
