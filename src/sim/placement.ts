import raw from '../data/buildings.json';
import goodsRaw from '../data/goods.json';
import econRaw from '../data/economy.json';
import { tileAt } from './mapgen';
import type { Building, BuildingDef, EconomyData, GameMap, Stock } from './types';

export const BUILDINGS = raw as unknown as BuildingDef[];
export const GOODS = goodsRaw as { id: string; name: string; short: string }[];
export const ECON = econRaw as unknown as EconomyData;

export function buildingDef(id: string): BuildingDef | undefined {
  return BUILDINGS.find((b) => b.id === id);
}

export function newBuilding(id: number, def: BuildingDef, x: number, y: number): Building {
  return {
    id, type: def.id, x, y, status: 'idle', progress: 0, running: false, staffed: 1, powered: false, covered: false,
    tier: 1, residents: 0, grow: 0, upTimer: 0, unmet: 0, needs: {}, tax: 0,
  };
}

/** Id of the building covering tile (x, y), if any. */
export function buildingAt(buildings: readonly Building[], x: number, y: number): Building | undefined {
  return buildings.find((b) => {
    const def = buildingDef(b.type);
    return def && x >= b.x && y >= b.y && x < b.x + def.footprint[0] && y < b.y + def.footprint[1];
  });
}

export function affordError(stock: Stock, def: BuildingDef): string | null {
  for (const [g, n] of Object.entries(def.cost)) {
    if ((stock[g] ?? 0) < n) return `need ${n} ${g} (have ${Math.floor(stock[g] ?? 0)})`;
  }
  return null;
}

/** Returns null when `def` can be placed with its origin at (x, y), else a reason. Pass `stock` to check cost too. */
export function placementError(
  map: GameMap,
  buildings: readonly Building[],
  def: BuildingDef,
  x: number,
  y: number,
  stock?: Stock,
): string | null {
  let wet = false;
  const isWater = (tx: number, ty: number) => {
    const c = tileAt(map, tx, ty);
    return c === 'deep' || c === 'shallow';
  };
  for (let dy = 0; dy < def.footprint[1]; dy++) {
    for (let dx = 0; dx < def.footprint[0]; dx++) {
      const cls = tileAt(map, x + dx, y + dy);
      if (cls === null) return 'out of bounds';
      if (!def.terrain.includes(cls)) return `cannot build on ${cls}`;
      if (buildingAt(buildings, x + dx, y + dy)) return 'tile occupied';
    }
  }
  if (def.needsWater) {
    for (let dy = -1; dy <= def.footprint[1]; dy++)
      for (let dx = -1; dx <= def.footprint[0]; dx++) {
        const inside = dx >= 0 && dy >= 0 && dx < def.footprint[0] && dy < def.footprint[1];
        const corner = (dx === -1 || dx === def.footprint[0]) && (dy === -1 || dy === def.footprint[1]);
        if (!inside && !corner && isWater(x + dx, y + dy)) wet = true;
      }
    if (!wet) return 'must be next to water';
  }
  return stock ? affordError(stock, def) : null;
}
