# Bevy engine entry

- Bevy 0.20.1 (pinned; declares rust-version 1.97.1, builds on installed 1.97.0 with `--ignore-rust-version`).
- Run: `engines/bevy/render.sh <style-dir> <out.png>` (any cwd). Or the binary directly: `--style <dir> --out <png> [--layout <json>]`.
- Headless: no window/winit at all (`primary_window: None`). Renders to an offscreen `Image` target (Rgba8UnormSrgb, 1920x1080) on Mesa lavapipe (Vulkan, software), read back with the Screenshot API. No Xvfb needed. `WGPU_BACKEND=gl` also selectable.
- Style loaded at runtime from CLI path; PNGs decoded directly into `Image` with the manifest `filter` sampler (linear/nearest). Tonemapping/dither/MSAA off, sRGB texture + sRGB target => pass-through.

## Results (mean abs per-channel diff vs tools/render_ref.py)
placeholder 0.94, lowpoly 0.42, pixel 0.14 (painted/parchment not present when tested). All < 2.
Placeholder residual (max 68) is edge-pixel resampling at sprite borders (premultiplied vs straight alpha filtering).

## Metrics
- Cold build (full Bevy, minimal features, opt-level 3 deps, 4 cores): 9m29s (user 27m30s).
- Incremental (touch main.rs, relink): ~3s.
- target/ dir: 3.9 GB (debug profile with debuginfo; could drop with `debug = false`). Binary: 844 MB debug (mostly debuginfo).
- Render time: ~0.6 s wall for process (452 sprites, 4 warm-up + capture frames), ~0.75 s via render.sh.
- LOC: ~300 (src/main.rs).

## Pain points
- API churn: Bevy 0.20 differs from most tutorials/LLM memory: `RenderTarget` is now a component, `Anchor` is a separate component, observers (`On<ScreenshotCaptured>`), feature names changed (`bevy_sprite_render`, `bevy_shader`). Must read docs.rs / source; the agent guessed little but verified by compiling.
- Gotcha: screenshotting on the first frames yields a black image; textures/pipelines need a few warm-up `app.update()` frames (plus `synchronous_pipeline_compilation`) before requesting the readback.
- Colour space: fine once sRGB formats are used consistently; clear colour must be built with `Color::srgb_u8`.
- Headless: works well, but only because one can disable windows; the lavapipe adapter prints a software-render warning.
- Draw order: Transparent2d sorts by z; used strictly increasing z per sprite (452 sprites => fine).

## Assessment for the full game
Bevy gives an excellent fit for the simulation half: ECS suits Anno-style production chains, thousands of agents and deterministic fixed-step ticks, and headless `App` tests (run schedules without a GPU) are first class, which is ideal for an AI agent team's CI. Rendering 2D iso sprites is simple and fast, wasm (WebGPU/WebGL2) and desktop export are real, and serde/RON saves are easy. The costs are: a 9.5 minute cold build and multi-GB target dir on 4 cores (incremental is OK, ~3s link here, but real game code with bevy_ui adds more; dynamic linking helps locally), and rapid breaking API changes every ~3 months which hurt LLM agents trained on older versions: expect compile-fix loops and the need to pin the version and keep docs/source greppable.

UI is the weakest part: bevy_ui is workable (flexbox, text, images) but verbose with no mature widget set; a UI-heavy game (tooltips, panels, lists, drag/drop) means either lots of bespoke code or bevy_egui (fast to build, immediate-mode, hard to skin to an art style). Overall: strong for sim, tests and perf; mediocre for UI-heavy iteration speed and compile time. Viable with a disciplined team that pins versions, but the UI and build-time overheads are real.
- Underlays (SPEC step 2b): manifest `underlays` images are drawn in manifest order after all terrain and before any object, world-space (pan/zoom with the map in the browser viewer). Bevy caveat: its sprite blending happens in linear light, so semi-transparent underlay pixels come out brighter than the sRGB-space reference (test style with a 43%-alpha ellipse: 2.55 mean diff; same pre-existing effect as overlays).
