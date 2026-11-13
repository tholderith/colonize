// Pure scene logic from SPEC.md: no Pixi, no DOM. Turns (manifest, layout) into an
// ordered list of draw items with screen positions. Engine-agnostic and unit-testable.

export type Vec2 = [number, number];

export interface SpriteDef {
  files: string[];
  anchor: Vec2;
  flat?: boolean;
}

export interface OverlayDef {
  file: string;
  pos: Vec2;
  anchor?: Vec2;
}

export interface Manifest {
  name: string;
  background: string;
  filter?: 'linear' | 'nearest';
  sprites: Record<string, SpriteDef>;
  overlays?: OverlayDef[];
}

export interface LayoutObject {
  sprite: string;
  x: number;
  y: number;
}

export interface Layout {
  width: number;
  height: number;
  terrain_legend: Record<string, string>;
  terrain: string[];
  objects: LayoutObject[];
}

export interface DrawItem {
  kind: 'terrain' | 'object';
  key: string;
  file: string;
  /** layout tile */
  x: number;
  y: number;
  /** footprint in tiles (1x1 for terrain) */
  fw: number;
  fh: number;
  /** top-left screen position of the sprite (P - anchor) */
  left: number;
  top: number;
  /** index in layout.objects (-1 for terrain) */
  index: number;
}

export const SCREEN_W = 1920;
export const SCREEN_H = 1080;

/** Footprints that are not 1x1 (SPEC table). */
export const FOOTPRINT: Record<string, Vec2> = {
  chapel: [2, 2],
  warehouse: [2, 2],
  wheat_field: [2, 2],
  ship: [2, 2],
};

export function footprint(key: string): Vec2 {
  return FOOTPRINT[key] ?? [1, 1];
}

/** Screen position of the top corner of tile (x, y). */
export function tileTop(x: number, y: number): Vec2 {
  return [960 + (x - y) * 64, -72 + (x + y) * 32];
}

/** Screen position of the south (bottom) corner of tile (x, y). */
export function tileSouth(x: number, y: number): Vec2 {
  const [sx, sy] = tileTop(x, y);
  return [sx, sy + 64];
}

export function variantFile(def: SpriteDef, x: number, y: number): string {
  return def.files[(x * 7 + y * 13) % def.files.length];
}

function spriteDef(m: Manifest, key: string): SpriteDef {
  const def = m.sprites[key];
  if (!def) throw new Error(`manifest "${m.name}" has no sprite "${key}"`);
  return def;
}

function item(m: Manifest, kind: DrawItem['kind'], key: string, x: number, y: number, index: number): DrawItem {
  const def = spriteDef(m, key);
  const [fw, fh] = kind === 'terrain' ? [1, 1] : footprint(key);
  const [px, py] = tileSouth(x + fw - 1, y + fh - 1);
  return {
    kind, key, x, y, fw, fh, index,
    file: variantFile(def, x, y),
    left: px - def.anchor[0],
    top: py - def.anchor[1],
  };
}

/** World draw list in SPEC draw order (steps 2–4). Overlays are separate. */
export function buildDrawList(m: Manifest, lay: Layout): DrawItem[] {
  const out: DrawItem[] = [];

  const tiles: Vec2[] = [];
  for (let y = 0; y < lay.height; y++) for (let x = 0; x < lay.width; x++) tiles.push([x, y]);
  tiles.sort((a, b) => a[0] + a[1] - (b[0] + b[1]) || a[0] - b[0]);
  for (const [x, y] of tiles) {
    const key = lay.terrain_legend[lay.terrain[y][x]];
    out.push(item(m, 'terrain', key, x, y, -1));
  }

  const flat: DrawItem[] = [];
  const rest: { it: DrawItem; depth: number; ax: number }[] = [];
  lay.objects.forEach((o, i) => {
    const it = item(m, 'object', o.sprite, o.x, o.y, i);
    if (spriteDef(m, o.sprite).flat) {
      flat.push(it);
    } else {
      const ax = o.x + it.fw - 1;
      const ay = o.y + it.fh - 1;
      rest.push({ it, depth: ax + ay, ax });
    }
  });
  // Array.prototype.sort is stable, so ties keep layout order.
  rest.sort((a, b) => a.depth - b.depth || a.ax - b.ax);
  out.push(...flat, ...rest.map((r) => r.it));
  return out;
}

/** Every file referenced by the manifest (sprites + overlays), deduplicated. */
export function manifestFiles(m: Manifest): string[] {
  const s = new Set<string>();
  for (const def of Object.values(m.sprites)) def.files.forEach((f) => s.add(f));
  for (const ov of m.overlays ?? []) s.add(ov.file);
  return [...s];
}
