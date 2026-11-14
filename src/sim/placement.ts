import raw from '../data/buildings.json';
import { tileAt } from './mapgen';
import type { Building, BuildingDef, GameMap } from './types';

export const BUILDINGS = raw as BuildingDef[];

export function buildingDef(id: string): BuildingDef | undefined {
  return BUILDINGS.find((b) => b.id === id);
}

/** Id of the building covering tile (x, y), if any. */
export function buildingAt(buildings: readonly Building[], x: number, y: number): Building | undefined {
  return buildings.find((b) => {
    const def = buildingDef(b.type);
    return def && x >= b.x && y >= b.y && x < b.x + def.footprint[0] && y < b.y + def.footprint[1];
  });
}

/** Returns null when `def` can be placed with its origin at (x, y), else a reason. */
export function placementError(
  map: GameMap,
  buildings: readonly Building[],
  def: BuildingDef,
  x: number,
  y: number,
): string | null {
  for (let dy = 0; dy < def.footprint[1]; dy++) {
    for (let dx = 0; dx < def.footprint[0]; dx++) {
      const cls = tileAt(map, x + dx, y + dy);
      if (cls === null) return 'out of bounds';
      if (!def.terrain.includes(cls)) return `cannot build on ${cls}`;
      if (buildingAt(buildings, x + dx, y + dy)) return 'tile occupied';
    }
  }
  return null;
}
