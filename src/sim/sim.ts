import { concordatTick, newConcordat, tradeWithTrader } from './concordat';
import { economyTick, newIsland } from './economy';
import { generateMap, islandAt, islandNames, islands } from './mapgen';
import { Navigator } from './nav';
import { ECON, TRADE, buildingAt, buildingDef, newBuilding, placementError, stockAtTile } from './placement';
import { createRng } from './rng';
import { dockTile, haulersTick, newHauler, type Ctx } from './trade';
import type { Command, GameMap, GameState } from './types';

export const TICK_HZ = 10;

export class Sim {
  readonly map: GameMap;
  state: GameState;
  private queue: Command[] = [];
  private ctx: Ctx;

  constructor(seed: number) {
    this.map = generateMap(seed);
    const { credits, ...homeStock } = ECON.startStock;
    this.state = {
      seed, tick: 0, speed: 1, paused: false, nextId: 1, buildings: [], credits: credits ?? 0, creditRate: 0, creditAcc: 0, creditFlow: [],
      islands: islandNames(seed).map((name, i) => newIsland(i, name, i === 0 ? homeStock : ECON.islandStartStock)),
      pop: { laborers: 0, technicians: 0, laborerJobs: 0, technicianJobs: 0 }, haulers: [], visitors: [], concordat: newConcordat(),
    };
    this.ctx = { s: this.state, map: this.map, nav: new Navigator(this.map), rng: createRng(seed ^ 0xc04dac7) };
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
    if (best) this.state.buildings.push(newBuilding(this.state.nextId++, def, best[0], best[1], 0));
  }

  /** Spend a cost: credits globally, everything else from the island's stock. */
  private pay(cost: Record<string, number>, island: number): void {
    const s = this.state;
    for (const [g, n] of Object.entries(cost)) {
      if (g === 'credits') s.credits -= n;
      else {
        const stock = s.islands[island]?.stock;
        if (stock) stock[g] = (stock[g] ?? 0) - n;
      }
    }
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
          if (def && placementError(this.map, s.buildings, def, cmd.x, cmd.y, stockAtTile(this.map, s, cmd.x, cmd.y)) === null) {
            const isl = islandAt(this.map, cmd.x, cmd.y);
            this.pay(def.cost, isl);
            s.buildings.push(newBuilding(s.nextId++, def, cmd.x, cmd.y, isl));
          }
          break;
        }
        case 'buildHauler': {
          const port = s.buildings.find((b) => b.id === cmd.port && b.type === 'port');
          const dock = port && dockTile(this.map, port);
          if (!port || !dock) break;
          const stock: Record<string, number> = { ...s.islands[port.island]?.stock, credits: s.credits };
          if (Object.entries(TRADE.hauler.cost).some(([g, n]) => (stock[g] ?? 0) < n)) break;
          this.pay(TRADE.hauler.cost, port.island);
          const h = newHauler(s.nextId++, dock, port.island);
          h.route = [{ kind: 'port', building: port.id, orders: [] }];
          s.haulers.push(h);
          break;
        }
        case 'scrapHauler':
          s.haulers = s.haulers.filter((h) => h.id !== cmd.hauler);
          break;
        case 'setRoute': {
          const h = s.haulers.find((o) => o.id === cmd.hauler);
          if (!h) break;
          const before = h.route[h.stop];
          h.route = cmd.route.slice(0, 8).map((st) => ({
            kind: st.kind === 'exchange' ? 'exchange' : 'port',
            building: st.kind === 'port' ? st.building : undefined,
            orders: st.orders.slice(0, 8).map((o) => ({ good: o.good, mode: o.mode === 'load' ? 'load' : 'unload', amount: Math.max(1, Math.floor(o.amount) || 1) })),
          }));
          // Keep the current stop (and any docking/sailing progress) when the edit leaves it in place.
          const cur = h.route[h.stop];
          if (!cur || !before || cur.kind !== before.kind || cur.building !== before.building) {
            if (h.stop >= h.route.length) h.stop = 0;
            h.phase = 'sail';
            h.leg = '';
          }
          break;
        }
        case 'tradeWithTrader':
          tradeWithTrader(this.ctx);
          break;
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
      haulersTick(this.ctx);
      concordatTick(this.ctx);
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
