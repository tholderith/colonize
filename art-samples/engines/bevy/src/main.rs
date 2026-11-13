//! Headless Bevy renderer for the art-samples bake-off.
//!
//! Usage: colonize_bevy_render --style <style_dir> --out <out.png> [--layout <layout.json>]
//!
//! Implements art-samples/SPEC.md: loads any style folder at runtime, builds the
//! isometric harbour scene from scene/layout.json, renders it with a 2D orthographic
//! camera (1 world unit = 1 px) into an offscreen 1920x1080 image target, reads the
//! frame back with Bevy's Screenshot API and writes a PNG. No window / winit is used.

use std::{
    collections::HashMap,
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
};

use bevy::{
    asset::RenderAssetUsages,
    camera::{ClearColorConfig, RenderTarget},
    image::{CompressedImageFormats, ImageSampler, ImageType},
    log::LogPlugin,
    prelude::*,
    render::{
        render_resource::{PollType, TextureFormat},
        renderer::RenderDevice,
        view::{
            screenshot::{Screenshot, ScreenshotCaptured},
            DebandDither, Msaa, Tonemapping,
        },
        RenderPlugin,
    },
    sprite::Anchor,
    window::ExitCondition,
};
use serde_json::Value;

const W: u32 = 1920;
const H: u32 = 1080;

/// One sprite to draw: image file (relative to style dir) and screen-space top-left (y down).
struct Draw {
    file: String,
    x: i32,
    y: i32,
}

fn footprint(key: &str) -> (i32, i32) {
    match key {
        "warehouse" | "wheat_field" | "ship" | "chapel" => (2, 2),
        _ => (1, 1),
    }
}

/// South corner of tile (x, y) in screen pixels (SPEC: top corner + (0, 64)).
fn south(x: i32, y: i32) -> (i32, i32) {
    (960 + (x - y) * 64, -72 + (x + y) * 32 + 64)
}

fn pair(v: &Value) -> (i32, i32) {
    (v[0].as_i64().unwrap_or(0) as i32, v[1].as_i64().unwrap_or(0) as i32)
}

fn read_json(p: &Path) -> Value {
    let s = std::fs::read_to_string(p).unwrap_or_else(|e| panic!("reading {}: {e}", p.display()));
    serde_json::from_str(&s).unwrap_or_else(|e| panic!("parsing {}: {e}", p.display()))
}

/// Resolve the whole scene to an ordered list of blits, following SPEC.md draw order.
fn build_draw_list(manifest: &Value, layout: &Value) -> Vec<Draw> {
    let sprites = &manifest["sprites"];
    let mut out = Vec::new();
    let mut place = |key: &str, x: i32, y: i32, p: (i32, i32)| {
        let s = &sprites[key];
        let files = s["files"].as_array().unwrap_or_else(|| panic!("sprite '{key}' missing"));
        let idx = ((x * 7 + y * 13) as usize) % files.len();
        let (ax, ay) = pair(&s["anchor"]);
        out.push(Draw { file: files[idx].as_str().unwrap().to_string(), x: p.0 - ax, y: p.1 - ay });
    };

    // 1. Terrain, ordered by (x + y), then x.
    let (w, h) = (layout["width"].as_i64().unwrap() as i32, layout["height"].as_i64().unwrap() as i32);
    let rows: Vec<Vec<char>> = layout["terrain"]
        .as_array()
        .unwrap()
        .iter()
        .map(|r| r.as_str().unwrap().chars().collect())
        .collect();
    let mut tiles: Vec<(i32, i32)> = (0..h).flat_map(|y| (0..w).map(move |x| (x, y))).collect();
    tiles.sort_by_key(|&(x, y)| (x + y, x));
    for (x, y) in tiles {
        let ch = rows[y as usize][x as usize].to_string();
        let key = layout["terrain_legend"][&ch].as_str().unwrap();
        place(key, x, y, south(x, y));
    }

    // 2. Objects: flat ones in layout order, then the rest depth-sorted (stable).
    struct Obj<'a> {
        idx: usize,
        key: &'a str,
        x: i32,
        y: i32,
        ax: i32,
        ay: i32,
    }
    let objs: Vec<Obj> = layout["objects"]
        .as_array()
        .unwrap()
        .iter()
        .enumerate()
        .map(|(idx, o)| {
            let key = o["sprite"].as_str().unwrap();
            let (x, y) = (o["x"].as_i64().unwrap() as i32, o["y"].as_i64().unwrap() as i32);
            let (fw, fh) = footprint(key);
            Obj { idx, key, x, y, ax: x + fw - 1, ay: y + fh - 1 }
        })
        .collect();
    let is_flat = |k: &str| sprites[k]["flat"].as_bool().unwrap_or(false);
    let (flat, mut rest): (Vec<&Obj>, Vec<&Obj>) = objs.iter().partition(|o| is_flat(o.key));
    for o in flat {
        place(o.key, o.x, o.y, south(o.ax, o.ay));
    }
    rest.sort_by_key(|o| (o.ax + o.ay, o.ax, o.idx));
    for o in rest {
        place(o.key, o.x, o.y, south(o.ax, o.ay));
    }

    // 3. Screen-space overlays in manifest order.
    if let Some(ovs) = manifest["overlays"].as_array() {
        for ov in ovs {
            let (px, py) = pair(&ov["pos"]);
            let (ax, ay) = if ov["anchor"].is_null() { (0, 0) } else { pair(&ov["anchor"]) };
            out.push(Draw { file: ov["file"].as_str().unwrap().to_string(), x: px - ax, y: py - ay });
        }
    }
    out
}

fn parse_hex(s: &str) -> Color {
    let s = s.trim_start_matches('#');
    let c = |i: usize| u8::from_str_radix(&s[i..i + 2], 16).unwrap_or(0);
    Color::srgb_u8(c(0), c(2), c(4))
}

struct Args {
    style: PathBuf,
    out: PathBuf,
    layout: PathBuf,
}

fn parse_args() -> Args {
    let mut style = None;
    let mut out = None;
    let mut layout = None;
    let mut it = std::env::args().skip(1);
    while let Some(a) = it.next() {
        match a.as_str() {
            "--style" => style = it.next().map(PathBuf::from),
            "--out" => out = it.next().map(PathBuf::from),
            "--layout" => layout = it.next().map(PathBuf::from),
            _ => {
                eprintln!("usage: colonize_bevy_render --style <dir> --out <png> [--layout <json>]");
                std::process::exit(2);
            }
        }
    }
    let (Some(style), Some(out)) = (style, out) else {
        eprintln!("usage: colonize_bevy_render --style <dir> --out <png> [--layout <json>]");
        std::process::exit(2);
    };
    // Default: <style>/../../scene/layout.json (styles/<name>/ sits next to scene/).
    let layout = layout.unwrap_or_else(|| style.join("../../scene/layout.json"));
    Args { style, out, layout }
}

fn main() {
    let t0 = std::time::Instant::now();
    let args = parse_args();
    let manifest = read_json(&args.style.join("manifest.json"));
    let layout = read_json(&args.layout);
    let draws = build_draw_list(&manifest, &layout);
    let sampler = match manifest["filter"].as_str().unwrap_or("linear") {
        "nearest" => ImageSampler::nearest(),
        _ => ImageSampler::linear(),
    };
    let background = parse_hex(manifest["background"].as_str().unwrap_or("#000000"));

    let mut app = App::new();
    app.add_plugins(
        DefaultPlugins
            .set(WindowPlugin {
                // No window at all: we render into an Image target.
                primary_window: None,
                exit_condition: ExitCondition::DontExit,
                ..default()
            })
            .set(RenderPlugin {
                // Compile every pipeline before the first frame so frame 1 is complete.
                synchronous_pipeline_compilation: true,
                ..default()
            })
            .set(LogPlugin { level: bevy::log::Level::WARN, ..default() }),
    );
    app.finish();
    app.cleanup();

    let world = app.world_mut();

    // Decode every referenced PNG synchronously (no AssetServer round-trip, so no
    // load-state polling): sRGB textures, sampler from the manifest's `filter`.
    let mut handles: HashMap<String, Handle<Image>> = HashMap::new();
    {
        let mut images = world.resource_mut::<Assets<Image>>();
        for d in &draws {
            if handles.contains_key(&d.file) {
                continue;
            }
            let path = args.style.join(&d.file);
            let bytes = std::fs::read(&path).unwrap_or_else(|e| panic!("reading {}: {e}", path.display()));
            let img = Image::from_buffer(
                &bytes,
                ImageType::Extension("png"),
                CompressedImageFormats::NONE,
                true,
                sampler.clone(),
                RenderAssetUsages::RENDER_WORLD,
            )
            .unwrap_or_else(|e| panic!("decoding {}: {e:?}", path.display()));
            handles.insert(d.file.clone(), images.add(img));
        }
    }

    // Offscreen 1920x1080 sRGB render target.
    let target_img = Image::new_target_texture(W, H, TextureFormat::Rgba8UnormSrgb, None);
    let target = world.resource_mut::<Assets<Image>>().add(target_img);

    // Orthographic 2D camera; default 2D projection is 1 world unit = 1 pixel of the
    // target, centred on the origin. Tonemapping/MSAA/dither off so pixels pass through.
    world.spawn((
        Camera2d,
        Camera { clear_color: ClearColorConfig::Custom(background), ..default() },
        RenderTarget::Image(target.clone().into()),
        Tonemapping::None,
        DebandDither::Disabled,
        Msaa::Off,
    ));

    // Screen (y down, origin top-left) -> world (y up, origin centre). Top-left anchor,
    // integer positions => texel centres land exactly on pixel centres.
    // Draw order = strictly increasing z (Transparent2d phase sorts back-to-front by z).
    for (i, d) in draws.iter().enumerate() {
        world.spawn((
            Sprite::from_image(handles[&d.file].clone()),
            Anchor::TOP_LEFT,
            Transform::from_xyz(d.x as f32 - (W / 2) as f32, (H / 2) as f32 - d.y as f32, i as f32 * 0.01),
        ));
    }

    let captured: Arc<Mutex<Option<Image>>> = Arc::default();
    let sink = captured.clone();
    app.world_mut()
        .spawn(Screenshot::image(target))
        .observe(move |ev: On<ScreenshotCaptured>| {
            *sink.lock().unwrap() = Some(ev.image.clone());
        });

    // Pump frames until the GPU readback lands.
    let mut frames = 0;
    while captured.lock().unwrap().is_none() {
        frames += 1;
        if frames > 60 {
            panic!("screenshot was not captured after 60 frames");
        }
        app.update();
        app.world()
            .resource::<RenderDevice>()
            .wgpu_device()
            .poll(PollType::Wait { submission_index: None, timeout: None })
            .ok();
    }

    let img = captured.lock().unwrap().take().unwrap();
    let rgb = img.try_into_dynamic().expect("convert screenshot").to_rgb8();
    if let Some(dir) = args.out.parent().filter(|p| !p.as_os_str().is_empty()) {
        std::fs::create_dir_all(dir).ok();
    }
    rgb.save(&args.out).unwrap_or_else(|e| panic!("writing {}: {e}", args.out.display()));
    eprintln!(
        "wrote {} ({} sprites, {} frames, {:.2}s)",
        args.out.display(),
        draws.len(),
        frames,
        t0.elapsed().as_secs_f64()
    );
}
