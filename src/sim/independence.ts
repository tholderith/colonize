import { add, addCredits } from './economy';
import { log } from './concordat';
import { exchangeTile, isWater, nearestWater } from './mapgen';
import { IND, TRADE, buildingDef, price } from './placement';
import { sail, type Ctx } from './trade';
import type { Building, GameState, Independence, Patrol } from './types';

const S = IND.sentiment;
const B = IND.blockade;
const TICKS_PER_MIN = 600;

export function newIndependence(): Independence {
  return {
    sentiment: 0, drivers: { levy: 0, tech: 0, relay: 0, grievance: 0, calm: 0 }, grievance: 0, calmUntil: 0, declared: false, declaredAt: 0,
    popAtDeclare: 0, cycles: 0, nextPatrolSpawn: 0, negPeriods: 0, suppressFines: 0, seized: 0,
  };
}

const totalPop = (s: GameState) => s.pop.laborers + s.pop.technicians;

/** Net sentiment change per minute, from the current drivers. */
export const sentimentRate = (ind: Independence) => Object.values(ind.drivers).reduce((t, n) => t + n, 0);

/** Sentiment drivers and one tick of accumulation. Frozen once independence is declared. */
export function sentimentTick(s: GameState): void {
  const ind = s.ind;
  if (ind.declared) {
    ind.drivers = { levy: 0, tech: 0, relay: 0, grievance: 0, calm: 0 };
    return;
  }
  const relays = s.buildings.filter((b) => b.type === 'signal_relay').length;
  const paying = ind.grievance > 0;
  ind.drivers = {
    levy: Math.max(0, s.concordat.levyPct - S.levyFloor) * S.perLevyPct,
    tech: s.pop.technicians * S.perTech,
    relay: relays * S.perRelay,
    grievance: paying ? S.grievanceDrain : 0,
    calm: s.tick < ind.calmUntil ? -S.calmPerMin : 0,
  };
  const drain = Math.min(ind.grievance, S.grievanceDrain / TICKS_PER_MIN);
  ind.grievance -= drain;
  ind.sentiment = Math.min(100, Math.max(0, ind.sentiment + (sentimentRate(ind) - ind.drivers.grievance) / TICKS_PER_MIN + drain));
}

export function canDeclare(s: GameState): boolean {
  return !s.ind.declared && !s.outcome && s.ind.sentiment >= S.declareAt;
}

/** Levy and demands stop, the exchange closes, patrols arrive. */
export function declare(ctx: Ctx): void {
  const { s } = ctx;
  if (!canDeclare(s)) return;
  const ind = s.ind;
  ind.declared = true;
  ind.declaredAt = s.tick;
  ind.popAtDeclare = totalPop(s);
  ind.cycles = 0;
  ind.nextPatrolSpawn = s.tick;
  s.concordat.demand = null;
  s.concordat.nextTraderAt = Math.min(s.concordat.nextTraderAt, s.tick + 300);
  s.visitors = s.visitors.filter((v) => v.kind !== 'patrol'); // no more audits
  log(s, 'declared', 'INDEPENDENCE DECLARED. The Concordat closes the exchange and sends the blockade.');
}

/** Alloy upkeep per battery, drawn from its island; a shortfall is billed in credits at a premium (can push credits below zero). */
export function upkeepTick(s: GameState): void {
  for (const b of s.buildings) {
    const up = buildingDef(b.type)?.upkeep;
    const isl = s.islands[b.island];
    if (!up || !isl) continue;
    for (const [g, perMin] of Object.entries(up)) {
      const need = perMin / TICKS_PER_MIN;
      if ((isl.stock[g] ?? 0) >= need) add(isl, g, -need);
      else addCredits(s, -need * price(g) * B.upkeepShortfallMult);
    }
  }
}

/** Battery exclusion centres, as a path signature. */
const batteries = (s: GameState): { x: number; y: number }[] =>
  s.buildings.flatMap((b: Building) => {
    const d = buildingDef(b.type);
    return d?.id === 'coastal_battery' ? [{ x: b.x + d.footprint[0] / 2, y: b.y + d.footprint[1] / 2 }] : [];
  });
const inZone = (bs: { x: number; y: number }[], x: number, y: number, r: number) => bs.some((b) => Math.hypot(x - b.x, y - b.y) < r);

export const patrolCount = (s: GameState): number => {
  const [lo, hi] = IND.difficulty[s.difficulty].patrols;
  return Math.min(hi, lo + Math.floor((s.tick - s.ind.declaredAt) / B.growTicks));
};

function pickGoal(ctx: Ctx, p: Patrol, bs: { x: number; y: number }[]): void {
  const { s, map, rng } = ctx;
  p.hasGoal = false;
  for (let i = 0; i < 4 && !p.hasGoal; i++) {
    let g: { x: number; y: number };
    if (s.haulers.length && rng.next() < 0.6) {
      const h = s.haulers[rng.int(s.haulers.length)]!;
      g = { x: Math.floor(h.x), y: Math.floor(h.y) };
    } else g = nearestWater(map, 6 + rng.int(map.w - 12), 6 + rng.int(map.h - 12));
    if (isWater(map, g.x, g.y) && !inZone(bs, g.x + 0.5, g.y + 0.5, B.avoidRadius + B.avoidMargin)) {
      p.gx = g.x;
      p.gy = g.y;
      p.hasGoal = true;
    }
  }
  p.leg = '';
}

function seize(ctx: Ctx, p: Patrol): void {
  const { s } = ctx;
  for (const h of s.haulers) {
    const goods = Object.entries(h.cargo).filter(([, n]) => n > 0);
    if (!goods.length || h.immune > 0 || Math.hypot(h.x - p.x, h.y - p.y) > B.seizeRadius) continue;
    const text = goods.map(([g, n]) => `${n} ${g}`).join(', ');
    h.cargo = {};
    h.limp = B.limpTicks;
    h.immune = B.immuneTicks;
    // Limp home: head for the first port stop on the hauler's home island.
    const home = h.route.findIndex((st) => st.kind === 'port' && s.buildings.find((b) => b.id === st.building)?.island === h.home);
    if (home >= 0) {
      h.stop = home;
      h.phase = 'sail';
      h.leg = '';
    }
    s.ind.seized++;
    log(s, 'seized', `Blockade patrol seized ${text} from hauler #${h.id}`, h.x, h.y);
  }
}

export function blockadeTick(ctx: Ctx): void {
  const { s, map } = ctx;
  const ind = s.ind;
  if (!ind.declared) return;
  const cycles = Math.floor((s.tick - ind.declaredAt) / B.cycleTicks);
  if (cycles > ind.cycles) {
    ind.cycles = cycles;
    log(s, 'cycle', `Blockade cycle ${cycles} survived`);
  }
  if (s.patrols.length < patrolCount(s) && s.tick >= ind.nextPatrolSpawn) {
    const t = exchangeTile(map);
    s.patrols.push({ id: s.nextId++, kind: 'patrol', x: t.x + 0.5, y: t.y + 0.5, px: t.x + 0.5, py: t.y + 0.5, leg: '', seg: 0, t: 0, hasGoal: false, gx: 0, gy: 0 });
    ind.nextPatrolSpawn = s.tick + B.spawnGapTicks;
  }
  const bs = batteries(s);
  const sig = bs.map((b) => `${b.x},${b.y}`).join(';');
  for (const p of s.patrols) {
    // Inside a zone (a battery went up around us) the way out is unrestricted; otherwise the path keeps clear.
    const want = inZone(bs, p.x, p.y, B.avoidRadius) ? '' : sig;
    if (p.leg && (p.leg.split('|')[1] ?? '') !== want) p.leg = '';
    if (!p.hasGoal) pickGoal(ctx, p, bs);
    if (p.hasGoal) {
      const r = sail(ctx, p, { x: p.gx, y: p.gy }, B.patrolTilesPerSec / TRADE.hauler.tilesPerSec, want);
      if (r !== 'moving') pickGoal(ctx, p, bs);
    }
    seize(ctx, p);
  }
}

/** Win / lose checks. Pauses the game and records the outcome. */
export function outcomeTick(s: GameState): void {
  if (s.outcome) return;
  const ind = s.ind;
  const pop = totalPop(s);
  s.stats.peakPop = Math.max(s.stats.peakPop, pop);
  const end = (win: boolean, cause: NonNullable<GameState['outcome']>['cause']) => {
    s.outcome = { win, cause, tick: s.tick };
    s.paused = true;
  };
  if (ind.negPeriods >= B.bankruptPeriods) return end(false, 'bankruptcy');
  if (!ind.declared) {
    if (ind.suppressFines >= S.suppressFines) end(false, 'suppression');
    return;
  }
  if (pop < B.popLosePct * ind.popAtDeclare) return end(false, 'collapse');
  if (ind.cycles >= B.cyclesToWin && s.credits >= 0 && pop >= B.popWinPct * ind.popAtDeclare) end(true, 'victory');
}
