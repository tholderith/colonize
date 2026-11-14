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
  /** Quay faces +x: water required at (x+w, y..y+h-1), and ships dock there (port). */
  dockEast?: boolean;
  /** Must lie within a depot's radius (port). */
  needsDepot?: boolean;
  house?: boolean;
  worker?: WorkerType;
  jobs?: number;
  /** Cycle length in ticks. */
  cycle?: number;
  inputs?: Stock;
  outputs?: Stock;
  /** Goods consumed per minute from the island stock (coastal battery). */
  upkeep?: Stock;
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
  /** Stock every other island starts with (the first island gets `startStock`). */
  islandStartStock: Stock;
  /** Goods stock a house needs to hold before its upgrade timer runs, and the goods an upgrade consumes. */
  upgradeMinGoods: number;
  upgradeGoods: number;
  tiers: TierDef[];
}

export interface TradeData {
  hauler: { cost: Stock; capacity: number; slots: number; tilesPerSec: number; dockTicks: number };
  tariff: number;
  levy: { periodTicks: number; base: number; step: number; popPerStep: number; max: number; reliefPct: number; penaltyPct: number; penaltyPeriods: number };
  demand: { firstAtTicks: number; intervalTicks: number; deadlineTicks: number; goods: string[]; amount: [number, number]; rewardMult: number; fineMult: number };
  trader: { firstAtTicks: number; intervalTicks: [number, number]; dockTicks: number; better: number; qty: [number, number]; exposurePer: number };
  audit: { firstAtTicks: number; intervalTicks: [number, number]; dockTicks: number; exposureForSure: number; fineBase: number; finePerExposure: number };
}

export type Difficulty = 'relaxed' | 'standard' | 'hard';
export interface IndependenceData {
  sentiment: {
    declareAt: number; levyFloor: number; perLevyPct: number; perTech: number; perRelay: number; missedDemand: number; auditFine: number;
    grievanceDrain: number; calmPerMin: number; calmTicks: number; suppressAt: number; suppressFines: number;
  };
  blockade: {
    cycleTicks: number; cyclesToWin: number; popWinPct: number; popLosePct: number; seizeRadius: number; avoidRadius: number; avoidMargin: number;
    patrolTilesPerSec: number; growTicks: number; spawnGapTicks: number; limpTicks: number; limpSpeed: number; immuneTicks: number;
    traderBetter: number; traderIntervalTicks: [number, number]; upkeepShortfallMult: number; bankruptPeriods: number;
  };
  difficulty: Record<Difficulty, { label: string; levyMult: number; demandMult: number; patrols: [number, number] }>;
}

export type Status = 'idle' | 'working' | 'no input' | 'no workers' | 'unpowered' | 'no depot' | 'storage full';

export interface Building {
  id: number;
  /** Island index (0 = largest). */
  island: number;
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

export interface IslandState {
  id: number;
  name: string;
  stock: Stock;
  /** Net change per minute per good (rolling ~1 minute). */
  rates: Stock;
  power: { supply: number; demand: number };
  /** Rolling per-second deltas feeding `rates`. */
  flow: Stock[];
  acc: Stock;
}

export interface Order {
  good: string;
  mode: 'load' | 'unload';
  amount: number;
}
export interface Stop {
  kind: 'port' | 'exchange';
  /** Port building id. */
  building?: number;
  orders: Order[];
}

/** Tick-based mover: position is a point on a cached water path, `px/py` is the previous tick for interpolation. */
export interface Mover {
  id: number;
  x: number;
  y: number;
  px: number;
  py: number;
  /** Cache key of the current leg ('' = needs a path). */
  leg: string;
  /** Segment index and fraction along it. */
  seg: number;
  t: number;
}
export interface Hauler extends Mover {
  kind: 'hauler';
  home: number;
  route: Stop[];
  /** Index of the stop being sailed to / docked at. */
  stop: number;
  phase: 'sail' | 'dock';
  wait: number;
  cargo: Stock;
  /** Ticks left limping home after a seizure (slow), and ticks of seizure immunity. */
  limp: number;
  immune: number;
}
export interface TraderOffer {
  side: 'buys' | 'sells';
  good: string;
  qty: number;
  /** Price per unit, already 25% better than the exchange and tariff-free. */
  price: number;
  done: boolean;
}
export interface Visitor extends Mover {
  kind: 'trader' | 'patrol';
  /** Target port building id. */
  target: number;
  phase: 'in' | 'dock' | 'out';
  wait: number;
  offer?: TraderOffer;
}

/** Blockade patrol: roams the sea lanes towards (gx, gy), seizes hauler cargo within range. */
export interface Patrol extends Mover {
  kind: 'patrol';
  hasGoal: boolean;
  gx: number;
  gy: number;
}

export interface Demand {
  good: string;
  amount: number;
  delivered: number;
  deadline: number;
  reward: number;
  fine: number;
}
export interface GameEvent {
  id: number;
  tick: number;
  kind: 'levy' | 'demand_issued' | 'demand_met' | 'demand_missed' | 'trader' | 'audit' | 'seized' | 'declared' | 'cycle' | 'info';
  text: string;
  /** Map position (seizures). */
  x?: number;
  y?: number;
}
export interface Concordat {
  periodStart: number;
  /** Credits earned this levy period. */
  earned: number;
  /** Levy % that applies at the end of this period. */
  levyPct: number;
  /** Next period levy reduced by `reliefPct`. */
  relief: boolean;
  /** Periods still carrying the penalty surcharge. */
  penaltyPeriods: number;
  tariff: number;
  exposure: number;
  nextDemandAt: number;
  demand: Demand | null;
  nextTraderAt: number;
  nextPatrolAt: number;
  seq: number;
  log: GameEvent[];
}

export interface Independence {
  /** 0-100. */
  sentiment: number;
  /** Current drivers, points per minute (calm is negative). */
  drivers: { levy: number; tech: number; relay: number; grievance: number; calm: number };
  /** Points from missed demands / audit fines still to be paid out into sentiment. */
  grievance: number;
  calmUntil: number;
  declared: boolean;
  declaredAt: number;
  popAtDeclare: number;
  /** Completed blockade cycles. */
  cycles: number;
  nextPatrolSpawn: number;
  /** Consecutive levy periods ending with credits < 0. */
  negPeriods: number;
  /** Audit fines received while sentiment >= suppression threshold, undeclared. */
  suppressFines: number;
  seized: number;
}
export type EndCause = 'victory' | 'bankruptcy' | 'collapse' | 'suppression';
export interface Outcome {
  win: boolean;
  cause: EndCause;
  tick: number;
}
export interface Stats {
  peakPop: number;
  creditsEarned: number;
  cargoMoved: number;
}

export interface GameState {
  seed: number;
  difficulty: Difficulty;
  tick: number;
  speed: Speed;
  paused: boolean;
  nextId: number;
  buildings: Building[];
  /** Global. */
  credits: number;
  creditRate: number;
  creditAcc: number;
  creditFlow: number[];
  islands: IslandState[];
  pop: { laborers: number; technicians: number; laborerJobs: number; technicianJobs: number };
  haulers: Hauler[];
  visitors: Visitor[];
  concordat: Concordat;
  patrols: Patrol[];
  ind: Independence;
  stats: Stats;
  outcome: Outcome | null;
}

export type Command =
  | { type: 'placeBuilding'; building: string; x: number; y: number }
  | { type: 'demolish'; x: number; y: number }
  | { type: 'setSpeed'; speed: Speed }
  | { type: 'pause'; paused: boolean }
  | { type: 'buildHauler'; port: number }
  | { type: 'scrapHauler'; hauler: number }
  | { type: 'setRoute'; hauler: number; route: Stop[] }
  | { type: 'tradeWithTrader' }
  | { type: 'declare' };
