import { islands } from '../src/sim/mapgen';
import { buildingDef, placementError } from '../src/sim/placement';
import type { Sim } from '../src/sim/sim';

/** Depot + port on an island, placed by command; returns the port id. */
export function setupPort(sim: Sim, island: number): number {
  const tiles = islands(sim.map)[island]!;
  const { w } = sim.map;
  const cx = tiles.reduce((t, i) => t + (i % w), 0) / tiles.length;
  const cy = tiles.reduce((t, i) => t + Math.floor(i / w), 0) / tiles.length;
  const near = (def: string, ax: number, ay: number, maxD: number) => {
    const d = buildingDef(def)!;
    return tiles
      .map((i) => [i % w, Math.floor(i / w)] as [number, number])
      .filter(([x, y]) => Math.hypot(x - ax, y - ay) <= maxD && placementError(sim.map, sim.state.buildings, d, x, y) === null)
      .sort((a, b) => Math.hypot(a[0] - ax, a[1] - ay) - Math.hypot(b[0] - ax, b[1] - ay) || a[0] - b[0] || a[1] - b[1])[0];
  };
  const place = (id: string, p: [number, number] | undefined) => {
    if (!p) throw new Error(`no spot for ${id}`);
    sim.enqueue({ type: 'placeBuilding', building: id, x: p[0], y: p[1] });
    sim.flush();
    return sim.state.buildings[sim.state.buildings.length - 1]!;
  };
  const depot = place('depot', near('depot', cx, cy, 99));
  // Port must be within depot range and on a coast: sweep radius outwards until one fits.
  let p: [number, number] | undefined;
  for (let r = 3; r <= 9 && !p; r++) p = near('port', depot.x + 1, depot.y + 1, r);
  return place('port', p).id;
}

