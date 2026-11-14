import { economyTick, emptyStock } from './economy';
import { generateMap, islands } from './mapgen';
import { ECON, buildingAt, buildingDef, newBuilding, placementError } from './placement';
import type { Command, GameMap, GameState } from './types';

export const TICK_HZ = 10;

export class Sim {
  readonly map: GameMap;
  state: GameState;
  private queue: Command[] = [];

  constructor(seed: number) {
    this.map = generateMap(seed);
    this.state = {
      seed, tick: 0, speed: 1, paused: false, nextId: 1, buildings: [],
      stock: { ...emptyStock(), ...ECON.startStock }, rates: emptyStock(), flow: [], acc: {},
      power: { supply: 0, demand: 0 }, pop: { laborers: 0, technicians: 0, laborerJobs: 0, technicianJobs: 0 },
    };
    this.placeStartDepot();
  }

  /** Free depot on the largest island, as close to its centre as fits. */
  private placeStartDepot(): void {
    const def = buildingDef('depot');
    const island = islands(this.map)[0];
    if (!def || !island) return;
    const { w } = this.map;
    const cx = island.reduce((t, i) => t + (i % w), 0) / island.length;
    const cy = island.reduce((t, i) => t + Math.floor(i / w), 0) / island.length;
    let best: [number, number] | null = null;
    let bestD = Infinity;
    for (const i of island) {
      const x = i % w, y = Math.floor(i / w);
      const d = Math.hypot(x + 1 - cx, y + 1 - cy);
      if (d < bestD && placementError(this.map, [], def, x, y) === null) {
        best = [x, y];
        bestD = d;
      }
    }
    if (best) this.state.buildings.push(newBuilding(this.state.nextId++, def, best[0], best[1]));
  }

  enqueue(cmd: Command): void {
    this.queue.push(cmd);
  }

  /** Apply queued commands without advancing time (so pause/speed work while paused). */
  flush(): void {
    const s = this.state;
    for (const cmd of this.queue.splice(0)) {
      switch (cmd.type) {
        case 'pause':
          s.paused = cmd.paused;
          break;
        case 'setSpeed':
          s.speed = cmd.speed;
          break;
        case 'placeBuilding': {
          const def = buildingDef(cmd.building);
          if (def && placementError(this.map, s.buildings, def, cmd.x, cmd.y, s.stock) === null) {
            for (const [g, n] of Object.entries(def.cost)) s.stock[g] = (s.stock[g] ?? 0) - n;
            s.buildings.push(newBuilding(s.nextId++, def, cmd.x, cmd.y));
          }
          break;
        }
        case 'demolish': {
          const b = buildingAt(s.buildings, cmd.x, cmd.y);
          if (b) s.buildings = s.buildings.filter((o) => o !== b);
          break;
        }
      }
    }
  }

  /** One 10 Hz tick: apply commands, then advance unless paused. */
  step(): void {
    this.flush();
    if (!this.state.paused) {
      economyTick(this.state);
      this.state.tick++;
    }
  }
}

export interface TimedCommand {
  /** Tick at which the command is enqueued (before that tick's step). */
  tick: number;
  cmd: Command;
}

export function runHeadless(seed: number, commands: TimedCommand[], ticks: number): GameState {
  const sim = new Sim(seed);
  for (let t = 0; t < ticks; t++) {
    for (const c of commands) if (c.tick === t) sim.enqueue(c.cmd);
    sim.step();
  }
  return sim.state;
}

/** FNV-1a over the JSON snapshot. */
export function hashState(state: GameState): number {
  const str = JSON.stringify(state);
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) h = Math.imul(h ^ str.charCodeAt(i), 0x01000193);
  return h >>> 0;
}
