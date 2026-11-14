export type TileClass = 'deep' | 'shallow' | 'shore' | 'land';
export const TILE_CLASSES: readonly TileClass[] = ['deep', 'shallow', 'shore', 'land'];

export interface GameMap {
  w: number;
  h: number;
  /** Row-major indices into TILE_CLASSES. */
  tiles: Uint8Array;
}

export interface BuildingDef {
  id: string;
  name: string;
  footprint: [number, number];
  terrain: TileClass[];
  color: string;
  /** Placeholder box height in px. */
  height: number;
}

export interface Building {
  id: number;
  type: string;
  x: number;
  y: number;
}

export type Speed = 1 | 2 | 3;

export interface GameState {
  seed: number;
  tick: number;
  speed: Speed;
  paused: boolean;
  nextId: number;
  buildings: Building[];
}

export type Command =
  | { type: 'placeBuilding'; building: string; x: number; y: number }
  | { type: 'demolish'; x: number; y: number }
  | { type: 'setSpeed'; speed: Speed }
  | { type: 'pause'; paused: boolean };
