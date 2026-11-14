import { addCredits, add } from './economy';
import { exchangeTile, isWater, nearestWater } from './mapgen';
import { advance, startLeg, type Navigator } from './nav';
import { ECON, IND, TRADE, buildingDef, price } from './placement';
import type { Rng } from './rng';
import type { Building, GameMap, GameState, Hauler, Mover, Stock, Stop, Visitor } from './types';

export interface Ctx {
  s: GameState;
  map: GameMap;
  nav: Navigator;
  rng: Rng;
}

const SPEED = TRADE.hauler.tilesPerSec / 10; // tiles per tick

/** Water tile next to a port's footprint (4-neighbour ring, fixed scan order). */
export function dockTile(map: GameMap, b: Building): { x: number; y: number } | null {
  const def = buildingDef(b.type);
  if (!def) return null;
  const [fw, fh] = def.footprint;
  if (def.dockEast) {
    for (let dy = 0; dy < fh; dy++) if (isWater(map, b.x + fw, b.y + dy)) return { x: b.x + fw, y: b.y + dy };
    return null;
  }
  for (let dx = 0; dx < fw; dx++) {
    if (isWater(map, b.x + dx, b.y - 1)) return { x: b.x + dx, y: b.y - 1 };
    if (isWater(map, b.x + dx, b.y + fh)) return { x: b.x + dx, y: b.y + fh };
  }
  for (let dy = 0; dy < fh; dy++) {
    if (isWater(map, b.x - 1, b.y + dy)) return { x: b.x - 1, y: b.y + dy };
    if (isWater(map, b.x + fw, b.y + dy)) return { x: b.x + fw, y: b.y + dy };
  }
  return null;
}

export function stopTile(ctx: Ctx, stop: Stop): { x: number; y: number } | null {
  if (stop.kind === 'exchange') return ctx.s.ind.declared ? null : exchangeTile(ctx.map); // closed by the blockade
  const b = ctx.s.buildings.find((o) => o.id === stop.building && o.type === 'port');
  return b ? dockTile(ctx.map, b) : null;
}

/** Where the free trader enters and leaves. */
export const traderSpawn = (map: GameMap) => nearestWater(map, map.w - 3, Math.floor(map.h / 2));

const mover = (id: number, tile: { x: number; y: number }): Mover => ({
  id, x: tile.x + 0.5, y: tile.y + 0.5, px: tile.x + 0.5, py: tile.y + 0.5, leg: '', seg: 0, t: 0,
});

export function newHauler(id: number, tile: { x: number; y: number }, home: number): Hauler {
  return { ...mover(id, tile), kind: 'hauler', home, route: [], stop: 0, phase: 'sail', wait: 0, cargo: {}, limp: 0, immune: 0 };
}
export function newVisitor(id: number, kind: Visitor['kind'], tile: { x: number; y: number }, target: number): Visitor {
  return { ...mover(id, tile), kind, target, phase: 'in', wait: 0 };
}

/** Sail one tick towards a water tile. `sig` makes the path avoid battery zones; `speed` is a multiplier. */
export function sail(ctx: Ctx, m: Mover, goal: { x: number; y: number }, speed = 1, sig = ''): 'moving' | 'arrived' | 'blocked' {
  if (!m.leg) {
    const { key, path } = ctx.nav.path(Math.floor(m.x), Math.floor(m.y), goal.x, goal.y, sig);
    if (!path) return 'blocked';
    startLeg(m, key, path);
  }
  const path = ctx.nav.byKey(m.leg);
  if (!path) {
    m.leg = '';
    return 'blocked';
  }
  if (advance(m, path, SPEED * speed)) {
    m.leg = '';
    return 'arrived';
  }
  return 'moving';
}

const total = (c: Stock) => Object.values(c).reduce((t, n) => t + n, 0);

/** Run a stop's load/unload orders. Port: island stock. Exchange: sell (after tariff) or buy for credits. */
function transfer(ctx: Ctx, h: Hauler, stop: Stop): void {
  const { s } = ctx;
  const port = stop.kind === 'port' ? s.buildings.find((b) => b.id === stop.building) : undefined;
  const isl = port ? s.islands[port.island] : undefined;
  if (stop.kind === 'port' && !isl) return;
  const cap = port ? ECON.storageCap * s.buildings.filter((b) => b.type === 'depot' && b.island === port.island).length : 0;
  for (const o of stop.orders) {
    const have = h.cargo[o.good] ?? 0;
    if (o.mode === 'load') {
      const slotOk = have > 0 || Object.values(h.cargo).filter((n) => n > 0).length < TRADE.hauler.slots;
      const room = TRADE.hauler.capacity - total(h.cargo);
      let n = Math.min(o.amount, room);
      if (isl) n = Math.min(n, Math.floor(isl.stock[o.good] ?? 0));
      else n = Math.min(n, Math.floor(s.credits / Math.max(price(o.good), 0.01)));
      if (!slotOk || n <= 0) continue;
      if (isl) add(isl, o.good, -n);
      else addCredits(s, -n * price(o.good));
      h.cargo[o.good] = have + n;
    } else {
      let n = Math.min(o.amount, have);
      if (isl) n = Math.min(n, Math.max(0, cap - (isl.stock[o.good] ?? 0)));
      if (n <= 0) continue;
      h.cargo[o.good] = have - n;
      ctx.s.stats.cargoMoved += n;
      if (isl) add(isl, o.good, n);
      else sellAtExchange(s, o.good, n);
    }
    if ((h.cargo[o.good] ?? 0) <= 0) delete h.cargo[o.good];
  }
}

/** Units of a demanded good count towards the demand first; the rest is sold at base price minus tariff. */
function sellAtExchange(s: GameState, good: string, n: number): void {
  const d = s.concordat.demand;
  if (d && d.good === good && d.delivered < d.amount) {
    const used = Math.min(n, d.amount - d.delivered);
    d.delivered += used;
    n -= used;
  }
  if (n > 0) addCredits(s, n * price(good) * (1 - s.concordat.tariff), true);
}

export function haulersTick(ctx: Ctx): void {
  for (const h of ctx.s.haulers) {
    if (h.limp > 0) h.limp--;
    if (h.immune > 0) h.immune--;
    if (!h.route.length) continue;
    if (h.stop >= h.route.length) h.stop = 0;
    if (h.phase === 'dock') {
      if (--h.wait <= 0) {
        h.stop = (h.stop + 1) % h.route.length;
        h.phase = 'sail';
        h.leg = '';
      }
      continue;
    }
    const stop = h.route[h.stop] as Stop;
    const goal = stopTile(ctx, stop);
    const r = goal ? sail(ctx, h, goal, h.limp > 0 ? IND.blockade.limpSpeed : 1) : 'blocked';
    if (r === 'blocked') {
      h.stop = (h.stop + 1) % h.route.length; // port gone or unreachable: skip it
      h.leg = '';
    } else if (r === 'arrived') {
      transfer(ctx, h, stop);
      h.phase = 'dock';
      h.wait = TRADE.hauler.dockTicks;
    }
  }
}

/** Free trader and patrol: sail in, dock, sail out, vanish. `onArrive` fires when they dock. */
export function visitorsTick(ctx: Ctx, onArrive: (v: Visitor, port: Building) => void): void {
  const { s, map } = ctx;
  s.visitors = s.visitors.filter((v) => {
    const home = v.kind === 'trader' ? traderSpawn(map) : exchangeTile(map);
    const port = s.buildings.find((b) => b.id === v.target && b.type === 'port');
    if (v.phase === 'in') {
      const goal = port ? dockTile(map, port) : null;
      if (!goal || !port) {
        v.phase = 'out';
        v.leg = '';
        return true;
      }
      const r = sail(ctx, v, goal);
      if (r === 'arrived') {
        v.phase = 'dock';
        v.wait = v.kind === 'trader' ? TRADE.trader.dockTicks : TRADE.audit.dockTicks;
        onArrive(v, port);
      } else if (r === 'blocked') return false;
    } else if (v.phase === 'dock') {
      if (--v.wait <= 0 || !port) {
        v.phase = 'out';
        v.leg = '';
      }
    } else {
      const r = sail(ctx, v, home);
      if (r !== 'moving') return false;
    }
    return true;
  });
}
