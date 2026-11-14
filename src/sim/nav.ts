import { isWater } from './mapgen';
import type { GameMap, Mover } from './types';

export type Pt = readonly [number, number];

const DIRS: Pt[] = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];

/** A* over water tiles (8-neighbour, no corner cutting). Returns tile coordinates from start to goal, or null. */
export function findWaterPath(map: GameMap, sx: number, sy: number, gx: number, gy: number, blocked?: (x: number, y: number) => boolean): Pt[] | null {
  const { w, h } = map;
  if (!isWater(map, sx, sy) || !isWater(map, gx, gy) || blocked?.(gx, gy)) return null;
  const heur = (x: number, y: number) => {
    const dx = Math.abs(x - gx), dy = Math.abs(y - gy);
    return Math.max(dx, dy) + (Math.SQRT2 - 1) * Math.min(dx, dy);
  };
  const g = new Float64Array(w * h).fill(Infinity);
  const from = new Int32Array(w * h).fill(-1);
  const closed = new Uint8Array(w * h);
  // Binary heap of [f, index]; ties break on index so results are deterministic.
  const heap: [number, number][] = [];
  const less = (a: [number, number], b: [number, number]) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
  const push = (e: [number, number]) => {
    heap.push(e);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (!less(heap[i] as [number, number], heap[p] as [number, number])) break;
      [heap[i], heap[p]] = [heap[p] as [number, number], heap[i] as [number, number]];
      i = p;
    }
  };
  const pop = (): [number, number] => {
    const top = heap[0] as [number, number];
    const last = heap.pop() as [number, number];
    if (heap.length) {
      heap[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < heap.length && less(heap[l] as [number, number], heap[m] as [number, number])) m = l;
        if (r < heap.length && less(heap[r] as [number, number], heap[m] as [number, number])) m = r;
        if (m === i) break;
        [heap[i], heap[m]] = [heap[m] as [number, number], heap[i] as [number, number]];
        i = m;
      }
    }
    return top;
  };
  const start = sy * w + sx, goal = gy * w + gx;
  g[start] = 0;
  push([heur(sx, sy), start]);
  while (heap.length) {
    const [, cur] = pop();
    if (closed[cur]) continue;
    closed[cur] = 1;
    if (cur === goal) break;
    const cx = cur % w, cy = (cur - cx) / w;
    for (const [dx, dy] of DIRS) {
      const nx = cx + dx, ny = cy + dy;
      if (nx < 0 || ny < 0 || nx >= w || ny >= h || !isWater(map, nx, ny) || blocked?.(nx, ny)) continue;
      if (dx !== 0 && dy !== 0 && (!isWater(map, cx + dx, cy) || !isWater(map, cx, cy + dy))) continue;
      const ni = ny * w + nx;
      const ng = (g[cur] as number) + (dx !== 0 && dy !== 0 ? Math.SQRT2 : 1);
      if (ng < (g[ni] as number)) {
        g[ni] = ng;
        from[ni] = cur;
        push([ng + heur(nx, ny), ni]);
      }
    }
  }
  if (!closed[goal]) return null;
  const out: Pt[] = [];
  for (let i = goal; i !== -1; i = from[i] as number) out.push([i % w, Math.floor(i / w)]);
  return out.reverse();
}

/** Battery exclusion zones from a signature "x,y;x,y" of battery centres: tiles within `radius` are blocked. */
function zoneBlocked(sig: string, radius: number): ((x: number, y: number) => boolean) | undefined {
  if (!sig) return undefined;
  const cs = sig.split(';').map((p) => p.split(',').map(Number) as [number, number]);
  return (x, y) => cs.some(([cx, cy]) => Math.hypot(x + 0.5 - cx, y + 0.5 - cy) < radius);
}

/**
 * Per-leg path cache (lives beside the state, not in it). A key fully describes its path
 * ("sx,sy>gx,gy" plus "|sig" for battery avoidance), so paths can be rebuilt after a load.
 */
export class Navigator {
  private cache = new Map<string, Pt[] | null>();
  constructor(
    readonly map: GameMap,
    private avoidRadius = 6.8,
  ) {}

  path(sx: number, sy: number, gx: number, gy: number, sig = ''): { key: string; path: Pt[] | null } {
    const key = `${sx},${sy}>${gx},${gy}${sig ? '|' + sig : ''}`;
    return { key, path: this.byKey(key) };
  }
  byKey(key: string): Pt[] | null {
    if (!this.cache.has(key)) {
      const [leg = '', sig = ''] = key.split('|');
      const [a = '', b = ''] = leg.split('>');
      const [sx = 0, sy = 0] = a.split(',').map(Number);
      const [gx = 0, gy = 0] = b.split(',').map(Number);
      this.cache.set(key, findWaterPath(this.map, sx, sy, gx, gy, zoneBlocked(sig, this.avoidRadius)));
    }
    return this.cache.get(key) ?? null;
  }
}

/** Place a mover at the start of a leg. */
export function startLeg(m: Mover, key: string, path: Pt[]): void {
  m.leg = key;
  m.seg = 0;
  m.t = 0;
  m.px = m.x = (path[0] as Pt)[0] + 0.5;
  m.py = m.y = (path[0] as Pt)[1] + 0.5;
}

/** Move along the leg by `dist` tiles. Returns true on arrival. */
export function advance(m: Mover, path: Pt[], dist: number): boolean {
  m.px = m.x;
  m.py = m.y;
  let rem = dist;
  while (rem > 0 && m.seg < path.length - 1) {
    const a = path[m.seg] as Pt, b = path[m.seg + 1] as Pt;
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const left = len * (1 - m.t);
    if (rem >= left) {
      rem -= left;
      m.seg++;
      m.t = 0;
    } else {
      m.t += rem / len;
      rem = 0;
    }
  }
  const a = path[Math.min(m.seg, path.length - 1)] as Pt;
  const b = path[Math.min(m.seg + 1, path.length - 1)] as Pt;
  m.x = a[0] + (b[0] - a[0]) * m.t + 0.5;
  m.y = a[1] + (b[1] - a[1]) * m.t + 0.5;
  return m.seg >= path.length - 1;
}
