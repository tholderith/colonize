# SDL2 / C++17 engine — art-sample renderer

Roll-our-own option: C++17, SDL2 2.30 `SDL_Renderer`, SDL2_image for PNG I/O, vendored
`nlohmann/json` 3.11.3 single header (`third_party/nlohmann/json.hpp`, MIT,
sha256 `9bea4c80…103ea6`, from the GitHub release). No other dependencies.

## Usage

```bash
# headless: build if needed, render 1920x1080, exit (works from any cwd)
engines/sdl/render.sh styles/placeholder renders/sdl/placeholder.png
# same, plus diff against tools/render_ref.py (PASS if mean abs diff < 2)
engines/sdl/check.sh styles/placeholder
# interactive window (needs a desktop, or xvfb-run): arrows/WASD or mouse-drag to pan,
# wheel to zoom (0.25x-3x, honours the style's linear/nearest filter), 0 = reset,
# F5 = hot-reload the style folder, Esc = quit
engines/sdl/build/colonize_sdl --style styles/painted
```

Binary flags: `--style <dir>` (required), `--out <png>`, `--layout <json>` (default:
`<style>/../../scene/layout.json`, else the art-samples path baked in at build time),
`--renderer surface|opengl|opengles2|software` (headless only), `--frames N` (interactive:
quit after N frames — a smoke test for the window path).

### Headless rendering path (which renderer)

- **Default `--renderer surface`**: `SDL_CreateSoftwareRenderer()` drawing directly into a
  1920×1080 ARGB8888 `SDL_Surface`. No window, no X server, no GL — `SDL_Init(0)` only.
  This is what `render.sh` uses. Diff vs reference: **mean 0.133, max 3** (SDL's software
  blitter rounds alpha blending slightly differently from PIL).
- **`--renderer opengl` / `opengles2`**: hidden window + `SDL_TEXTUREACCESS_TARGET` texture,
  draw, `SDL_RenderReadPixels`. Works under `xvfb-run` (x11 driver) *and* with no display at
  all — SDL 2.30 falls back to its EGL `offscreen` video driver (Mesa llvmpipe). Diff vs
  reference: **mean 0.034, max 1** (GPU blending is exact up to rounding).
- Output is saved as RGB24 PNG via `IMG_SavePNG`, matching the reference's `convert("RGB")`.

Blending: every texture uses `SDL_BLENDMODE_BLEND` = straight-alpha over
(`rgb = src·a + dst·(1−a)`), same as PIL `alpha_composite` onto an opaque canvas.
`filter` → `SDL_SetTextureScaleMode(Nearest|Linear)`; at 1:1 integer placement both give
identical pixels, the difference shows when zooming interactively. All images are
normalised to ARGB8888 with `SDL_ConvertSurfaceFormat` before upload so paletted (tRNS),
grey+alpha and RGB PNGs behave like PIL `convert("RGBA")`.

## Setup

```bash
apt-get install -y g++ cmake pkg-config libsdl2-dev libsdl2-image-dev   # (ttf not needed yet)
cmake -S engines/sdl -B engines/sdl/build && cmake --build engines/sdl/build -j
```

## Metrics (4-core cloud container)

| metric | value |
|---|---|
| clean configure + build | **5.0 s** (≈ 4 s of that is compiling `nlohmann/json.hpp`); `render.sh` from clean incl. render: 6.2 s |
| incremental rebuild (one .cpp) | ~3 s (`scene.cpp` includes json), ~1 s (`main.cpp`) |
| binary size | 220 KB (178 KB stripped), dynamically linked to libSDL2 + libSDL2_image |
| headless render, `surface` | whole process ~0.12 s: JSON parse 0.2 ms, PNG load+upload ~7 ms, 452 blits ~9 ms, PNG encode ~75 ms |
| headless render, `opengl` (llvmpipe) | draw + readback ~65–135 ms (mostly GL context + readback on a software rasteriser) |
| interactive loop, xvfb + llvmpipe | ~45 fps at 1920×1080 logical (pure CPU GL); a real GPU would be vsync-bound |
| lines written | ~540 (main.cpp 278, scene.cpp/hpp 196, CMake 20, render.sh + check.sh 46) |
| vs reference (placeholder) | mean abs diff 0.133 (`surface`), 0.034 (`opengl`) — target < 2 |

Also tested against a synthetic style (variants, paletted PNG with tRNS, LA, RGB-only,
`#rgb` background, `nearest`, semi-transparent and partly off-canvas overlays):
mean diff 0.25, max 3.

## Pain points / workarounds

- **No JSON in the C++ stdlib** — had to vendor a 900 KB header; it dominates compile time.
  (A precompiled header or moving JSON behind one TU fixes that if it matters.)
- **Headless output isn't a first-class SDL concept.** You choose between the software
  renderer on a surface (simplest, no display) or render-target + `SDL_RenderReadPixels`
  (needs a GL context). Both work; it's ~30 lines either way, but you have to know the trick.
  SDL 2.30's automatic `offscreen` EGL fallback was a pleasant surprise (no Xvfb needed);
  it prints a harmless `XDG_RUNTIME_DIR` warning while probing Wayland.
- **Software-renderer blending is approximate** (max ±3 per channel vs PIL). Fine for the
  < 2 mean threshold, but pixel-exact golden-image tests would need tolerance or the GL path.
- **Palette/greyscale PNGs**: must convert to ARGB8888 before creating textures, otherwise
  palette alpha handling depends on SDL internals.
- Footprints are hard-coded from the SPEC table (as `render_ref.py` does) — a manifest/data
  field would be cleaner for the real game.
- Interactive window: `SDL_RenderSetLogicalSize(1920,1080)` keeps the 1920-wide UI art
  intact at any window size, but letterboxes; a real game wants a resolution-independent UI
  layout instead of fixed-size overlay bitmaps.
- Nothing was hard to debug: compiler errors are clear, the program is tiny, and the
  diff-against-reference loop is ~0.2 s. That fast loop is the strongest argument for C++/SDL.

## Assessment: would a custom C++/SDL engine suit the FULL game built by an AI agent team?

For *this* sample it was nearly frictionless: ~540 lines, 5 s builds, sub-second headless
renders with no display, deterministic output that diffs within 0.03–0.13 of the reference,
a 200 KB binary. Agents are very fluent in C++/SDL, the toolchain runs fine in a Linux
container, and the "render a frame to PNG and compare" loop is trivially scriptable — which
is exactly what an agent team needs for verification. Raw performance is a non-issue for
an Anno-scale 2D map (thousands of sprites per frame is easy with `SDL_RenderGeometry`
batching or a move to SDL3/SDL_gpu), and packaging is "one binary + SDL .so/.dll" for
Linux/Windows/macOS (Steam-friendly; web via Emscripten is possible but extra work).
Headless testability is arguably *better* than in a big engine: the simulation can be a
plain C++ library unit-tested with no window at all, and rendering is golden-image testable.

The cost is everything that isn't a sprite blit. Before real game work we would have to
build or integrate: a UI toolkit (Dear ImGui is great for debug/tools but looks like a dev
tool; a styled, skinnable game UI — this game is UI-heavy — means RmlUi (HTML/CSS-like, the
best fit) or a custom widget system, plus layout/scaling/localisation), text rendering
(SDL_ttf/HarfBuzz, rich text, fonts per style), input mapping, audio (SDL_mixer or miniaudio),
sprite animation + tweening, camera/zoom/culling/batching, tile-map picking and the
isometric draw-order rules for multi-tile and moving units, A* pathfinding (roads, ships,
tactical battles), a fixed-tick sim with pause/speed controls, save/load (serialization of
the whole economy — nlohmann or cereal), an asset pipeline (atlas packing, hot reload,
manifest validation), crash handling and CI packaging for three OSes. Realistically that is
4–8 weeks of focused engine work for an agent team before gameplay velocity matches what
Godot gives on day one, plus a lasting tax: memory-safety bugs in C++ are the class of
error agents are worst at spotting, and every engine subsystem is ours to maintain. My frank
take: C++/SDL is the best choice if we value full control, a tiny deterministic headless
core, and painless CI — and it pairs well with a "simulation as a pure library" architecture
— but for a UI-heavy strategy game it front-loads a lot of non-game work; it only wins if
we commit to RmlUi (or similar) for UI early and keep the engine layer deliberately small.
- Underlays (SPEC step 2b): manifest `underlays` images are drawn in manifest order after all terrain and before any object, world-space (pan/zoom with the map in the browser viewer).
