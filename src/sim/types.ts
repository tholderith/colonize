export type TileClass = 'deep' | 'shallow' | 'shore' | 'land';
export const TILE_CLASSES: readonly TileClass[] = ['deep', 'shallow', 'shore', 'land'];

export interface GameMap {
  w: number;
  h: number;
  /** Row-major indices into TILE_CLASSES. */
  tiles: Uint8Array;
}

export type Stock = Record<string, number>;
export type WorkerType = 'laborer' | 'technician';

export interface BuildingDef {
  id: string;
  name: string;
  group: string;
  footprint: [number, number];
  terrain: TileClass[];
  color: string;
  /** Placeholder box height in px. */
  height: number;
  cost: Stock;
  /** Coverage radius in tiles (depot, wind turbine). */
  radius?: number;
  /** Power supplied (turbine). */
  supply?: number;
  /** Power drawn (production). */
  draw?: number;
  needsWater?: boolean;
  house?: boolean;
  worker?: WorkerType;
  jobs?: number;
  /** Cycle length in ticks. */
  cycle?: number;
  inputs?: Stock;
  outputs?: Stock;
}

export interface TierDef {
  worker: WorkerType;
  capacity: number;
  needsPerResidentPerMin: Stock;
  taxPerResidentPerMin: number;
}

export interface EconomyData {
  startStock: Stock;
  storageCap: number;
  unpoweredSpeed: number;
  turbineSupply: number;
  growTicks: number;
  decayTicks: number;
  upgradeTicks: number;
  downgradeTicks: number;
  tiers: TierDef[];
}

export type Status = 'idle' | 'working' | 'no input' | 'no workers' | 'unpowered' | 'no depot' | 'storage full';

export interface Building {
  id: number;
  type: string;
  x: number;
  y: number;
  status: Status;
  /** Production: ticks of progress in the current cycle; running = inputs taken. */
  progress: number;
  running: boolean;
  /** Fraction of jobs filled (0..1). */
  staffed: number;
  powered: boolean;
  covered: boolean;
  /** House state. */
  tier: number;
  residents: number;
  grow: number;
  upTimer: number;
  unmet: number;
  /** House needs currently met. */
  needs: Record<string, boolean>;
  /** House tax income, credits per minute. */
  tax: number;
}

export type Speed = 1 | 2 | 3;

export interface GameState {
  seed: number;
  tick: number;
  speed: Speed;
  paused: boolean;
  nextId: number;
  buildings: Building[];
  stock: Stock;
  /** Net change per minute per good (rolling ~1 minute). */
  rates: Stock;
  power: { supply: number; demand: number };
  pop: { laborers: number; technicians: number; laborerJobs: number; technicianJobs: number };
  /** Rolling per-second deltas feeding `rates`. */
  flow: Stock[];
  acc: Stock;
}

export type Command =
  | { type: 'placeBuilding'; building: string; x: number; y: number }
  | { type: 'demolish'; x: number; y: number }
  | { type: 'setSpeed'; speed: Speed }
  | { type: 'pause'; paused: boolean };
