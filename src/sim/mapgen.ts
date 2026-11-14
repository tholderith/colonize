import { createRng } from './rng';
import type { GameMap, TileClass } from './types';
import { TILE_CLASSES } from './types';

export const MAP_SIZE = 80;
/** Land is kept this far from the map edge so ships can circle the archipelago. */
const EDGE = 5;
const NOISE_CELL = 5;

/** Island centre and blob scale (area grows with scale squared). */
const CENTERS: [number, number, number][] = [
  [24, 26, 1.38],
  [56, 30, 1.35],
  [40, 56, 1.3],
];

export function tileAt(map: GameMap, x: number, y: number): TileClass | null {
  if (x < 0 || y < 0 || x >= map.w || y >= map.h) return null;
  return TILE_CLASSES[map.tiles[y * map.w + x] as number] ?? null;
}

/** 3 organic islands from overlapping noisy blobs. Deterministic per seed. */
export function generateMap(seed: number): GameMap {
  const w = MAP_SIZE;
  const h = MAP_SIZE;
  const rng = createRng(seed ^ 0x9e3779b9);

  // Coarse value-noise lattice, bilinearly sampled, wobbles blob edges.
  const gw = Math.ceil(w / NOISE_CELL) + 2;
  const lattice = Array.from({ length: gw * gw }, () => rng.next());
  const noise = (x: number, y: number) => {
    const fx = x / NOISE_CELL;
    const fy = y / NOISE_CELL;
    const ix = Math.floor(fx);
    const iy = Math.floor(fy);
    const tx = fx - ix;
    const ty = fy - iy;
    const at = (i: number, j: number) => lattice[j * gw + i] as number;
    const top = at(ix, iy) * (1 - tx) + at(ix + 1, iy) * tx;
    const bot = at(ix, iy + 1) * (1 - tx) + at(ix + 1, iy + 1) * tx;
    return top * (1 - ty) + bot * ty;
  };

  const blobs: { x: number; y: number; r: number }[] = [];
  for (const [cx, cy, sc] of CENTERS) {
    const jx = cx + rng.range(-3, 3);
    const jy = cy + rng.range(-3, 3);
    blobs.push({ x: jx, y: jy, r: rng.range(5, 6.5) * sc });
    const extra = 4 + rng.int(3);
    for (let i = 0; i < extra; i++) {
      const a = rng.range(0, Math.PI * 2);
      const d = rng.range(2, 4.5) * sc;
      blobs.push({ x: jx + Math.cos(a) * d, y: jy + Math.sin(a) * d, r: rng.range(2.5, 4.5) * sc });
    }
  }

  const land = new Uint8Array(w * h);
  for (let y = EDGE; y < h - EDGE; y++) {
    for (let x = EDGE; x < w - EDGE; x++) {
      for (const b of blobs) {
        const d = Math.hypot(x - b.x, y - b.y);
        if (d < b.r * (0.65 + 0.7 * noise(x, y))) {
          land[y * w + x] = 1;
          break;
        }
      }
    }
  }
  // Drop stray specks: keep only the 3 largest land components.
  {
    const seen = new Uint8Array(w * h);
    const comps: number[][] = [];
    for (let i = 0; i < w * h; i++) {
      if (!land[i] || seen[i]) continue;
      const comp: number[] = [];
      const stack = [i];
      while (stack.length) {
        const j = stack.pop() as number;
        if (seen[j] || !land[j]) continue;
        seen[j] = 1;
        comp.push(j);
        const x = j % w, y = (j - x) / w;
        if (x > 0) stack.push(j - 1);
        if (x < w - 1) stack.push(j + 1);
        if (y > 0) stack.push(j - w);
        if (y < h - 1) stack.push(j + w);
      }
      comps.push(comp);
    }
    comps.sort((a, b) => b.length - a.length);
    for (const c of comps.slice(3)) for (const j of c) land[j] = 0;
  }
  const isLand = (x: number, y: number) => x >= 0 && y >= 0 && x < w && y < h && land[y * w + x] === 1;

  // land -> shore if any 8-neighbour is water; water -> shallow within 2 tiles of land.
  const tiles = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      let cls: TileClass = 'deep';
      let nearWater = false;
      let nearLand = false;
      for (let dy = -2; dy <= 2; dy++) {
        for (let dx = -2; dx <= 2; dx++) {
          const l = isLand(x + dx, y + dy);
          if (l) nearLand = true;
          else if (Math.abs(dx) <= 1 && Math.abs(dy) <= 1) nearWater = true;
        }
      }
      if (isLand(x, y)) cls = nearWater ? 'shore' : 'land';
      else if (nearLand) cls = 'shallow';
      tiles[y * w + x] = TILE_CLASSES.indexOf(cls);
    }
  }
  return { w, h, tiles };
}

/** Connected solid (shore/land) regions, 4-neighbour, as lists of tile indices. Largest first. */
export function islands(map: GameMap): number[][] {
  const { w, h, tiles } = map;
  const seen = new Uint8Array(w * h);
  const out: number[][] = [];
  for (let i = 0; i < w * h; i++) {
    if ((tiles[i] as number) < 2 || seen[i]) continue;
    const comp: number[] = [];
    const stack = [i];
    while (stack.length) {
      const j = stack.pop() as number;
      if (seen[j] || (tiles[j] as number) < 2) continue;
      seen[j] = 1;
      comp.push(j);
      const x = j % w;
      const y = (j - x) / w;
      if (x > 0) stack.push(j - 1);
      if (x < w - 1) stack.push(j + 1);
      if (y > 0) stack.push(j - w);
      if (y < h - 1) stack.push(j + w);
    }
    out.push(comp);
  }
  return out.sort((a, b) => b.length - a.length);
}

const NAME_A = ['Slag', 'Cinder', 'Rivet', 'Brine', 'Ember', 'Flux', 'Gantry', 'Kiln', 'Ratchet', 'Soot'];
const NAME_B = ['Reach', 'Holm', 'Shoal', 'Landing', 'Spit', 'Haven', 'Point', 'Ness'];

/** Fictional island names, one per island (largest first), deterministic per seed. */
export function islandNames(seed: number, n = 3): string[] {
  const rng = createRng(seed ^ 0x51ed270b);
  const a = [...NAME_A];
  const out: string[] = [];
  for (let i = 0; i < n; i++) out.push(`${a.splice(rng.int(a.length), 1)[0]} ${NAME_B[rng.int(NAME_B.length)]}`);
  return out;
}

export function isWater(map: GameMap, x: number, y: number): boolean {
  const c = tileAt(map, x, y);
  return c === 'deep' || c === 'shallow';
}

interface IslandIndex {
  idx: Int8Array;
  centres: { x: number; y: number }[];
}
const indexCache = new WeakMap<GameMap, IslandIndex>();
function islandIndex(map: GameMap): IslandIndex {
  let c = indexCache.get(map);
  if (!c) {
    const idx = new Int8Array(map.w * map.h).fill(-1);
    const centres = islands(map).map((comp, n) => {
      let sx = 0, sy = 0;
      for (const i of comp) {
        idx[i] = n;
        sx += i % map.w;
        sy += Math.floor(i / map.w);
      }
      return { x: sx / comp.length, y: sy / comp.length };
    });
    c = { idx, centres };
    indexCache.set(map, c);
  }
  return c;
}

/** Island (0 = largest) that owns tile (x, y); water and off-map tiles resolve to the nearest island centre. */
export function islandAt(map: GameMap, x: number, y: number): number {
  const { idx, centres } = islandIndex(map);
  const cx = Math.min(map.w - 1, Math.max(0, Math.floor(x)));
  const cy = Math.min(map.h - 1, Math.max(0, Math.floor(y)));
  const own = idx[cy * map.w + cx] as number;
  if (own >= 0) return own;
  let best = 0, bd = Infinity;
  centres.forEach((c, i) => {
    const d = Math.hypot(c.x - x, c.y - y);
    if (d < bd) { bd = d; best = i; }
  });
  return best;
}

/** The Concordat exchange: a fixed water tile on the north edge. */
export function exchangeTile(map: GameMap): { x: number; y: number } {
  return { x: Math.floor(map.w / 2), y: 2 };
}

/** Nearest water tile to (x, y), scanning outwards; deterministic. */
export function nearestWater(map: GameMap, x: number, y: number): { x: number; y: number } {
  for (let r = 0; r < map.w; r++)
    for (let dy = -r; dy <= r; dy++)
      for (let dx = -r; dx <= r; dx++)
        if (Math.max(Math.abs(dx), Math.abs(dy)) === r && isWater(map, x + dx, y + dy)) return { x: x + dx, y: y + dy };
  return { x, y };
}
