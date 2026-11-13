// Pixi side: loads a style folder generically from its manifest and builds display objects.
import { Assets, Container, Sprite, Texture } from 'pixi.js';
import { buildDrawList, manifestFiles, type DrawItem, type Layout, type Manifest, type OverlayDef } from './scene';

export interface LoadedStyle {
  base: string; // absolute URL of the style folder, ending in '/'
  manifest: Manifest;
  textures: Map<string, Texture>; // file (as written in manifest) -> texture
  urls: string[];
}

export async function fetchJson<T>(url: string): Promise<T> {
  const r = await fetch(url, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`GET ${url} -> ${r.status}`);
  return (await r.json()) as T;
}

export async function loadStyle(styleBase: string): Promise<LoadedStyle> {
  const base = new URL(styleBase.endsWith('/') ? styleBase : styleBase + '/', location.href).href;
  const manifest = await fetchJson<Manifest>(base + 'manifest.json');
  const files = manifestFiles(manifest);
  const urls = files.map((f) => new URL(f, base).href);
  const loaded = await Assets.load<Texture>(urls);
  const scaleMode = manifest.filter === 'nearest' ? 'nearest' : 'linear';
  const textures = new Map<string, Texture>();
  files.forEach((f, i) => {
    const tex = loaded[urls[i]];
    tex.source.scaleMode = scaleMode;
    textures.set(f, tex);
  });
  return { base, manifest, textures, urls };
}

export async function unloadStyle(s: LoadedStyle): Promise<void> {
  await Assets.unload(s.urls);
}

export interface WorldSprite {
  item: DrawItem;
  sprite: Sprite;
}

/** World layer: terrain + objects, already in SPEC draw order (children order = draw order). */
export function buildWorld(style: LoadedStyle, layout: Layout): { container: Container; sprites: WorldSprite[] } {
  const container = new Container();
  const sprites: WorldSprite[] = [];
  for (const it of buildDrawList(style.manifest, layout)) {
    const sprite = new Sprite(style.textures.get(it.file)!);
    sprite.position.set(it.left, it.top);
    container.addChild(sprite);
    sprites.push({ item: it, sprite });
  }
  return { container, sprites };
}

export interface OverlaySprite {
  def: OverlayDef;
  sprite: Sprite;
}

/** Screen-space overlays in manifest order. Positioned for the 1920x1080 reference frame. */
export function buildOverlays(style: LoadedStyle): { container: Container; sprites: OverlaySprite[] } {
  const container = new Container();
  const sprites: OverlaySprite[] = [];
  for (const def of style.manifest.overlays ?? []) {
    const sprite = new Sprite(style.textures.get(def.file)!);
    const [ax, ay] = def.anchor ?? [0, 0];
    sprite.position.set(def.pos[0] - ax, def.pos[1] - ay);
    container.addChild(sprite);
    sprites.push({ def, sprite });
  }
  return { container, sprites };
}
