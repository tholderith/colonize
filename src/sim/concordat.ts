import { add, addCredits } from './economy';
import { exchangeTile } from './mapgen';
import { ECON, GOODS, TRADE, price } from './placement';
import { newVisitor, traderSpawn, visitorsTick, type Ctx } from './trade';
import type { Building, Concordat, GameEvent, GameState, TraderOffer, Visitor } from './types';

const T = TRADE;

export function newConcordat(): Concordat {
  return {
    periodStart: 0, earned: 0, levyPct: T.levy.base, relief: false, penaltyPeriods: 0, tariff: T.tariff, exposure: 0,
    nextDemandAt: T.demand.firstAtTicks, demand: null, nextTraderAt: T.trader.firstAtTicks, nextPatrolAt: T.audit.firstAtTicks, seq: 0, log: [],
  };
}

/** Levy percentage: base plus a step per population threshold, plus the penalty surcharge, minus relief. */
export function levyRate(pop: number, penalty: boolean, relief: boolean): number {
  const steps = Math.floor(pop / T.levy.popPerStep);
  const pct = Math.min(T.levy.max, T.levy.base + T.levy.step * steps) + (penalty ? T.levy.penaltyPct : 0) - (relief ? T.levy.reliefPct : 0);
  return Math.max(0, pct);
}

const totalPop = (s: GameState) => s.pop.laborers + s.pop.technicians;

function log(s: GameState, kind: GameEvent['kind'], text: string): void {
  const c = s.concordat;
  c.log.push({ id: ++c.seq, tick: s.tick, kind, text });
  if (c.log.length > 30) c.log.shift();
}

const roll = (ctx: Ctx, [a, b]: [number, number]) => Math.floor(a + ctx.rng.next() * (b - a));

/** Leave the credits non-negative. */
function charge(s: GameState, amt: number): number {
  const n = Math.min(Math.max(0, s.credits), amt);
  addCredits(s, -n);
  return n;
}

export function concordatTick(ctx: Ctx): void {
  const { s } = ctx;
  const c = s.concordat;
  const t = s.tick;

  // Levy: a share of the credits earned this period.
  if (t - c.periodStart >= T.levy.periodTicks) {
    const pct = levyRate(totalPop(s), c.penaltyPeriods > 0, c.relief);
    const took = charge(s, Math.floor((c.earned * pct) / 100));
    log(s, 'levy', `Levy ${pct}% of ${Math.floor(c.earned)} cr earned: ${Math.floor(took)} cr taken`);
    c.earned = 0;
    c.periodStart = t;
    c.relief = false;
    if (c.penaltyPeriods > 0) c.penaltyPeriods--;
  }
  c.levyPct = levyRate(totalPop(s), c.penaltyPeriods > 0, c.relief);

  // Demands.
  if (!c.demand && t >= c.nextDemandAt) {
    const good = T.demand.goods[ctx.rng.int(T.demand.goods.length)] as string;
    const amount = Math.round(roll(ctx, T.demand.amount) / 5) * 5;
    c.demand = {
      good, amount, delivered: 0, deadline: t + T.demand.deadlineTicks,
      reward: Math.round(amount * price(good) * T.demand.rewardMult), fine: Math.round(amount * price(good) * T.demand.fineMult),
    };
    c.nextDemandAt = t + T.demand.intervalTicks + roll(ctx, [-600, 600]);
    log(s, 'demand_issued', `Demand: ${amount} ${good} to the exchange within ${Math.round(T.demand.deadlineTicks / 600)} min (reward ${c.demand.reward} cr)`);
  }
  const d = c.demand;
  if (d) {
    if (d.delivered >= d.amount) {
      addCredits(s, d.reward);
      c.relief = true;
      c.demand = null;
      log(s, 'demand_met', `Demand met: +${d.reward} cr, levy -${T.levy.reliefPct}% next period`);
    } else if (t >= d.deadline) {
      const paid = charge(s, d.fine);
      c.penaltyPeriods = T.levy.penaltyPeriods;
      c.demand = null;
      log(s, 'demand_missed', `Demand missed: fined ${Math.floor(paid)} cr, levy +${T.levy.penaltyPct}% for ${T.levy.penaltyPeriods} periods`);
    }
  }

  // Visitors.
  const ports = s.buildings.filter((b) => b.type === 'port');
  const spawn = (kind: 'trader' | 'patrol') => {
    const port = ports[ctx.rng.int(ports.length)] as Building;
    const from = kind === 'trader' ? traderSpawn(ctx.map) : exchangeTile(ctx.map);
    s.visitors.push(newVisitor(s.nextId++, kind, from, port.id));
  };
  if (t >= c.nextTraderAt) {
    if (ports.length && !s.visitors.some((v) => v.kind === 'trader')) {
      spawn('trader');
      c.nextTraderAt = t + roll(ctx, T.trader.intervalTicks);
    } else c.nextTraderAt = t + 600;
  }
  if (t >= c.nextPatrolAt) {
    if (ports.length && !s.visitors.some((v) => v.kind === 'patrol')) {
      spawn('patrol');
      c.nextPatrolAt = t + roll(ctx, T.audit.intervalTicks);
    } else c.nextPatrolAt = t + 600;
  }
  visitorsTick(ctx, (v, port) => arrive(ctx, v, port));
}

function arrive(ctx: Ctx, v: Visitor, port: Building): void {
  const { s } = ctx;
  const c = s.concordat;
  const name = s.islands[port.island]?.name ?? '';
  if (v.kind === 'patrol') {
    const chance = Math.min(1, c.exposure / T.audit.exposureForSure);
    if (ctx.rng.next() < chance) {
      const paid = charge(s, T.audit.fineBase + T.audit.finePerExposure * c.exposure);
      log(s, 'audit', `Audit at ${name}: contraband found, fined ${Math.floor(paid)} cr`);
    } else log(s, 'audit', `Audit at ${name}: clean`);
    c.exposure = 0;
    return;
  }
  const isl = s.islands[port.island];
  if (!isl) return;
  const good = GOODS.filter((g) => g.price)[ctx.rng.int(GOODS.filter((g) => g.price).length)]?.id as string;
  let side: TraderOffer['side'] = ctx.rng.next() < 0.5 ? 'buys' : 'sells';
  let qty = roll(ctx, T.trader.qty);
  if (side === 'buys') {
    qty = Math.min(qty, Math.floor(isl.stock[good] ?? 0));
    if (qty < 5) side = 'sells';
  }
  if (side === 'sells') qty = roll(ctx, T.trader.qty);
  const mult = side === 'buys' ? 1 + T.trader.better : 1 - T.trader.better;
  v.offer = { side, good, qty, price: Math.round(price(good) * mult * 100) / 100, done: false };
  log(s, 'trader', `Free trader at ${name}: ${side === 'buys' ? 'buying' : 'selling'} ${qty} ${good} at ${v.offer.price} cr each`);
}

/** Accept the docked free trader's offer. Untaxed, but raises contraband exposure. */
export function tradeWithTrader(ctx: Ctx): void {
  const { s } = ctx;
  const v = s.visitors.find((o) => o.kind === 'trader' && o.phase === 'dock' && o.offer && !o.offer.done);
  const port = v && s.buildings.find((b) => b.id === v.target);
  const isl = port && s.islands[port.island];
  const o = v?.offer;
  if (!v || !o || !port || !isl) return;
  const depots = s.buildings.filter((b) => b.type === 'depot' && b.island === port.island).length;
  let n = o.qty;
  if (o.side === 'buys') {
    n = Math.min(n, Math.floor(isl.stock[o.good] ?? 0));
    add(isl, o.good, -n);
    addCredits(s, n * o.price); // not counted as earned: the Concordat never sees it
  } else {
    n = Math.min(n, Math.floor(s.credits / o.price), Math.max(0, ECON.storageCap * depots - (isl.stock[o.good] ?? 0)));
    addCredits(s, -n * o.price);
    add(isl, o.good, n);
  }
  o.done = true;
  if (n <= 0) return;
  s.concordat.exposure += n / T.trader.exposurePer;
  log(s, 'trader', `Traded ${n} ${o.good} with the free trader (exposure +${(n / T.trader.exposurePer).toFixed(1)})`);
}
