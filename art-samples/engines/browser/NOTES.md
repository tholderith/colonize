# Browser engine: TypeScript + PixiJS 8.23 + Vite 8

## Setup / run
- `./render.sh <style-dir> <out.png>`: runs `build.sh` (npm ci if needed, vite build if stale), serves dist + the style dir + layout on a local port, screenshots 1920x1080 with Playwright. Works from any cwd.
- `./bundle.sh`: builds and creates `site/` (viewer, layout.json, every style with a manifest, `styles/index.json`; relative paths). Preview: `node scripts/static-server.cjs site 8080`, open `?style=<name>`.
- Dev: `npm run dev`. Viewer: drag pan, wheel zoom at cursor, style dropdown, click building = highlight + tooltip (sprite key, tile, footprint), R reset, U toggle UI.
- URL param `?style=<name>`; render mode is used by the screenshot script (exact 1:1 camera, no viewer chrome).

## Results
- Diff vs `tools/render_ref.py` (placeholder): mean abs per-channel diff 0.034 (limit 2).
- lowpoly / pixel had no manifest.json at test time, so were not verified; the loader is generic (manifest + `filter`: nearest/linear).
- Cold: npm ci + build ~6 s (npm cache warm); vite build alone ~0.35 s. Warm render.sh: ~1.5 s total (screenshot ~1.4 s incl. chromium launch).
- LOC written: ~650 (src 492 TS, scripts 79, index.html 26, plus shell scripts).
- node_modules 161 MB (mostly typescript 7 / vite / rolldown native binaries); dist/site bundle: ~625 KB JS+HTML (pixi ~260 KB min, 77 KB gzip) + styles (placeholder 736 KB total site).

## Pain points
- Pixi v8 async init and texture loading need an explicit "ready" flag for screenshots; sub-pixel placement must be rounded to match the reference exactly.
- Premultiplied-alpha / linear filtering differences are tiny (diff 0.03) but need care.
- 161 MB of node_modules for a trivial scene; supply-chain surface.
- Draw order is manual (sort + zIndex off); fine for this spec, needs a real layering design in the full game.

## Assessment for the full game
Strong fit for an AI agent team. TypeScript gives fast, typed, compile-checked iteration; edit-build-screenshot loop is ~2 s, and Playwright makes headless visual regression and UI testing trivial in a Linux container (DOM/HTML overlays can be asserted on directly, not just pixels). UI-heavy screens (trade tables, production chain panels, diplomacy, tooltips, tech trees) are where this stack is best by a wide margin: the HTML/CSS/React/Svelte layer is the most productive UI toolkit that exists and agents know it very well; use Pixi only for the map and battles canvas. Simulation can be pure TS in a Web Worker, deterministic and testable under plain Node with no renderer; saves are JSON/IndexedDB or exported files. Pixi v8 handles thousands of sprites easily (batched WebGL/WebGPU, ParticleContainer for 10k+); the real perf risks are GC churn in the sim and large-map culling, which are manageable.

Weaknesses: JS is slower than native for heavy simulation (mitigate with workers, typed arrays, or WASM later); there is no editor, so scene/asset tooling must be built by the team (a Godot-style editor is absent); audio and gamepad support are browser-grade. Desktop packaging is well trodden: Tauri (small, Rust, needs a toolchain and webview differences across OSes) or Electron (heavier, consistent Chromium); Steam via Steamworks bindings (steamworks.js / greenworks) works with Electron and is the lower-risk route, Tauri plugins for Steam are less mature. Overall: lowest friction for an agent team, highest UI productivity, adequate performance for an Anno-like scale.
- Underlays (SPEC step 2b): manifest `underlays` images are drawn in manifest order after all terrain and before any object, world-space (pan/zoom with the map in the browser viewer).
