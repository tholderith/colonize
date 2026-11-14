export const TILE_W = 128;
export const TILE_H = 64;

/** World position of grid point (a, b); for integers this is a tile's top corner. */
export function gridToWorld(a: number, b: number): { x: number; y: number } {
  return { x: (a - b) * (TILE_W / 2), y: (a + b) * (TILE_H / 2) };
}

/** Tile containing world point (wx, wy). */
export function worldToTile(wx: number, wy: number): { x: number; y: number } {
  const a = (wx / (TILE_W / 2) + wy / (TILE_H / 2)) / 2;
  const b = (wy / (TILE_H / 2) - wx / (TILE_W / 2)) / 2;
  return { x: Math.floor(a), y: Math.floor(b) };
}
