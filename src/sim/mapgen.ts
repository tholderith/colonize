import { createRng } from './rng';
import type { GameMap, TileClass } from './types';
import { TILE_CLASSES } from './types';

export const MAP_SIZE = 64;
const NOISE_CELL = 5;

const CENTERS: [number, number][] = [
  [18, 19],
  [46, 22],
  [32, 47],
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
  for (const [cx, cy] of CENTERS) {
    const jx = cx + rng.range(-3, 3);
    const jy = cy + rng.range(-3, 3);
    blobs.push({ x: jx, y: jy, r: rng.range(5, 6.5) });
    const extra = 4 + rng.int(3);
    for (let i = 0; i < extra; i++) {
      const a = rng.range(0, Math.PI * 2);
      const d = rng.range(2, 4.5);
      blobs.push({ x: jx + Math.cos(a) * d, y: jy + Math.sin(a) * d, r: rng.range(2.5, 4.5) });
    }
  }

  const land = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      for (const b of blobs) {
        const d = Math.hypot(x - b.x, y - b.y);
        if (d < b.r * (0.65 + 0.7 * noise(x, y))) {
          land[y * w + x] = 1;
          break;
        }
      }
    }
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
